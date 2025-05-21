from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import DeviceStatus, Manager
import socket
import threading
import json
import os
from uuid import uuid4
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
from django.urls import reverse

# TCP 서버 설정
TCP_IP = '0.0.0.0' # 모든 인터페이스에서 접속 허용
TCP_PORT = 38600
BUFFER_SIZE = 1024
connections = []

# 제어 화면 렌더링
def control(request):
    return render(request, 'bems/control.html')


# 명령을 TCP 클라이언트에게 전송
@csrf_exempt
def control_device(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command = data.get('command')

            # JSON 객체를 문자열로 변환하여 TCP 서버로 전송
            # 명령을 문자열로 인코딩하여 TCP 연결에 전송
            command_str = json.dumps(command)

            for conn in connections:
                try:
                    conn.send(command_str.encode('utf-8'))
                except Exception as e:
                    print(f"[TCP 전송 오류] {e}")

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=400)

    return JsonResponse({'status': 'fail'}, status=400)


# Python socket 모듈을 이용해 TCP 서버를 만드는 함수
# TCP 서버 시작 함수 (백그라운드 스레드에서 실행)
def tcp_server():
    # TCP/IP 기반의 서버 소켓
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4 (AF_INET)와 TCP (SOCK_STREAM)를 사용하는 소켓 생성
    s.bind((TCP_IP, TCP_PORT)) # 서버 소켓을 특정 IP와 포트에 바인딩
    s.listen(5) # 클라이언트 접속을 최대 5개까지 대기열(queue) 에 쌓을 수 있음
    print(f"TCP Server started, waiting for connections...{TCP_IP}:{TCP_PORT}")
    while True:
        conn, addr = s.accept() # 컨트롤러가 서버에 접속 (접속 요청이 오면 accept로 하나씩 처리)
        print(f"Connection from: {addr}")
        connections.append(conn) # 접속된 클라이언트 소켓을 전역 리스트 connections에 저장

        # 새 클라이언트 접속마다 별도 스레드에서 처리
        threading.Thread(target=handle_client, args=(conn,)).start()


# 클라이언트 연결 처리 함수
def handle_client(conn):
    while True:
        try:
            data = conn.recv(BUFFER_SIZE) # 컨트롤러가 JSON 상태 데이터 전송하면 수신 받음
            if not data:
                break
            print(f"Received data: {data.decode('utf-8')}") # 수신한 바이트 데이터를 문자열로 변환하여 로그 출력
            process_data(data) # 수신한 데이터를 process_data() 함수에 넘겨서 처리
        except Exception as e:
            print(f"Error handling client: {e}")
            break
    conn.close()
    connections.remove(conn)


# 장비 상태 데이터 처리 함수
def process_data(data):
    try:
        # 1. TCP로 받은 바이트 데이터를 JSON으로 파싱
        data_dict = json.loads(data.decode('utf-8'))

        # 2. 각 필드를 추출
        controller_id = data_dict.get('controller_id')
        groupselector = data_dict.get('groupselector', 'unknown')
        speakerselector = data_dict.get('speakerselector', 'unknown')
        exchanger = data_dict.get('exchanger', 'unknown')
        remoteamp = data_dict.get('remoteamp', 'unknown')

        # 3. controller_id 기준으로 DeviceStatus 테이블에 저장
        DeviceStatus.objects.update_or_create(
            controller_id=controller_id,
            defaults={
                'groupselector': groupselector,
                'speakerselector': speakerselector,
                'exchanger': exchanger,
                'remoteamp': remoteamp,
            }
        )

        # 4. 이상 상태가 있을 경우 문자 발송
        if 'x' in (groupselector, speakerselector, exchanger, remoteamp):
            try:
                # 해당 컨트롤러 ID에 매핑된 학교 관리자 전화번호를 Manager 테이블에서 찾음
                phonebook_entry = Manager.objects.get(id=controller_id)
                manager_phone_number = phonebook_entry.phone_number

                # 엔지니어에게 보낼 메시지
                # 절대 URL 생성: ID가 포함된 URL을 생성
                relative_url = reverse('engineer', args=[controller_id])  # 상대 URL 생성
                nptechon_url = "http://www.nptechon.com"
                yerin_url = "http://www.shimyerin.site"
                engineer_url = f"{yerin_url}{relative_url}"  # 절대 URL 생성

                # 랜덤 비밀번호 생성
                temp_password = str(uuid4())[:8]

                # SupportRequest에 저장
                phonebook_entry = Manager.objects.get(id=entry_id)
                SupportRequest.objects.update_or_create(
                    entry=phonebook_entry,
                    defaults={
                        'temp_password': temp_password,
                        'is_authenticated': False
                    }
                )

                # 엔지니어 전화번호 지정
                engineer_phone_number = os.getenv('ENGINEER_PHONE_NUMBER')  # 고정
                # 엔지니어에게 보낼 메시지
                engineer_text = (
                    f"BEMS 문제 발생\n"
                    f"{engineer_url}\n"
                    f"비밀번호: {temp_password}"
                )
                # 엔지니어에게 문자 발송!!
                if send_sms(engineer_phone_number, engineer_text):
                    print("SMS sent successfully to the engineer.")
                else:
                    print("Failed to send SMS to the engineer.")

                # 관리자에게 문자 발송!!
                message_text = "학교에 문제가 발생했습니다."
                if send_sms(manager_phone_number, message_text):
                    print("SMS sent successfully.")
                else:
                    print("Failed to send SMS.")

            except Manager.DoesNotExist:
                print(f"Manager entry not found for controller_id: {controller_id}")
            except Exception as e:
                print(f"Error processing data: {str(e)}")


    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data: {str(e)}")


# 문자 메시지 전송 함수
def send_sms(phone_number, message_text):
    try:
        api_key = os.getenv('COOL_SMS_API_KEY')
        api_secret = os.getenv('COOL_SMS_API_SECRET')
        sender = os.getenv('SENDER_PHONE_NUMBER')

        cool = Message(api_key, api_secret)
        response = cool.send({
            'type': 'sms',
            'to': phone_number,
            'from': sender,
            'text': message_text,
        })

        if response.get('success_count', 0) > 0:
            return True
        else:
            return False
    except CoolsmsException as e:
        print(f"[CoolSMS Error] {e.code}: {e.msg}")
        return False
    except Exception as e:
        print(f"[Exception] {e}")
        return False


# 서버 시작 (메인 앱에서 import 후 실행해야 함 -> apps.py의 ready 함수에서 호출)
def start_tcp_server():
    # Django의 자동 리로더 재시작을 구분
    if os.environ.get('RUN_MAIN') == 'true':  # Django 개발 서버는 코드 변경 시 내부적으로 재시작 -> 이때 tcp_server()도 다시 실행되어 포트 중복이 발생 -> 이를 방지
        # tcp_server()가 새로운 데몬 스레드에서 실행
        threading.Thread(target=tcp_server, daemon=True).start()
