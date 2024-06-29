from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
import os
from .models import Phonebook, SupportRequest
from .models import DeviceStatus
import json
import socket
import threading
from django.http import HttpRequest
from django.views.decorators.csrf import ensure_csrf_cookie

def main_view(request):
    return render(request, 'bems/index.html')


def send_sms_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    entry_id = request.POST.get('entry_id')

    if not entry_id:
        return JsonResponse({"error": "Entry ID not provided."}, status=400)

    try:
        # Phonebook에서 엔트리 찾기
        phonebook_entry = Phonebook.objects.get(id=entry_id)
        manager_phone_number = phonebook_entry.phone_number

        # 엔지니어에게 보낼 메시지
        # 절대 URL 생성: ID가 포함된 URL을 생성
        relative_url = reverse('engineer', args=[entry_id])  # 상대 URL 생성
        nptechon_url = "http://www.nptechon.com"
        yerin_url = "http://www.shimyerin.site"
        engineer_url = f"{yerin_url}{relative_url}"  # 절대 URL 생성

        # 관리자 전화번호 지정
        engineer_phone_number = os.getenv('ENGINEER_PHONE_NUMBER') # 고정

        # 문자발송 전화번호 지정
        sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')

        # 문자 메시지 생성
        engineer_sms_text = f"이 경로로 접속해주세요: {engineer_url}"
        manager_sms_text = "학교에 문제가 발생했습니다."

        api_key = os.getenv('COOL_SMS_API_KEY')
        api_secret = os.getenv('COOL_SMS_API_SECRET')

        cool = Message(api_key, api_secret)

        # 엔지니어에게 문자 보내기
        engineer_params = {
            'type': 'sms',
            'to': engineer_phone_number,  # 엔지니어에게 보내는 전화번호
            'from': sender_phone_number,  # 발신자 번호
            'text': engineer_sms_text,  # 엔지니어에게 보내는 메시지
        }

        # 관리자에게 문자 보내기
        manager_params = {
            'type': 'sms',
            'to': manager_phone_number,  # 관리자에게 보내는 전화번호
            'from': sender_phone_number,  # 발신자 번호
            'text': manager_sms_text,  # 관리자에게 보내는 메시지
        }

        # 엔지니어와 관리자에게 문자 전송
        engineer_response = cool.send(engineer_params)  # 엔지니어에게 문자 전송
        manager_response = cool.send(manager_params)  # 관리자에게 문자 전송

        if engineer_response.get('success_count', 0) > 0 and manager_response.get('success_count', 0) > 0:
            return JsonResponse({"message": "SMS sent successfully."})
        else:
            return JsonResponse({"error": "SMS send failed."}, status=500)

    except ObjectDoesNotExist:
        return JsonResponse({"error": "Phonebook entry not found."}, status=404)

    except CoolsmsException as e:
        return JsonResponse({"error": f"Error Code: {e.code}, Error Message: {e.msg}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def request_approval(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    # POST 요청에서 엔트리 ID와 요청 시간을 추출
    entry_id = request.POST.get('entry_id')
    requested_time = request.POST.get('requested_time')

    if not entry_id or not requested_time:
        return JsonResponse({"error": "Missing required parameters."}, status=400)

    try:
        # Phonebook에서 엔트리 찾기
        phonebook_entry = Phonebook.objects.get(id=entry_id)
        manager_phone_number = phonebook_entry.phone_number

        # 문자발송 전화번호 지정
        sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')

        # 관리자에게 전송할 URL 생성
        relative_url = reverse('manager', args=[entry_id, requested_time])
        nptechon_url = "http://www.nptechon.com"
        yerin_url = "http://www.shimyerin.site"
        approval_url = f"{yerin_url}{relative_url}"
        print(approval_url)

        # 관리자에게 보낼 메시지
        manager_sms_text = f"엔지니어 요청 승인: {approval_url}"

        api_key = os.getenv('COOL_SMS_API_KEY')
        api_secret = os.getenv('COOL_SMS_API_SECRET')

        cool = Message(api_key, api_secret)

        # 관리자에게 문자 전송
        params = {
            'type': 'sms',
            'to': manager_phone_number,
            'from': sender_phone_number,
            'text': manager_sms_text,
        }

        response = cool.send(params)

        if response.get('success_count', 0) > 0:
            return JsonResponse({"message": "Approval request sent successfully."})
        else:
            return JsonResponse({"error": "Failed to send approval request."}, status=500)

    except ObjectDoesNotExist:
        return JsonResponse({"error": "Engineer not found."}, status=404)
    except CoolsmsException as e:
        return JsonResponse({"error": f"Error Code: {e.code}, Error Message: {e.msg}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def approve_request(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    action = request.POST.get("action")  # 승인 또는 거부
    entry_id = request.POST.get("entry_id")
    requested_time = request.POST.get("requested_time")

    if action == "approve":
        # 승인 처리 로직
        # 승인이 되었다는 메시지와 함께 엔지니어 페이지 URL을 생성하여 전송
        relative_url = reverse('engineer_approved', args=[entry_id])
        nptechon_url = "http://www.nptechon.com"
        yerin_url = "http://www.shimyerin.site"
        engineer_url = f"{yerin_url}{relative_url}"
        engineer_message = f"요청이 승인되었습니다: {engineer_url}"

        api_key = os.getenv('COOL_SMS_API_KEY')
        api_secret = os.getenv('COOL_SMS_API_SECRET')

        cool = Message(api_key, api_secret)

        # 관리자 전화번호 지정
        engineer_phone_number = os.getenv('ENGINEER_PHONE_NUMBER')  # 고정
        # 문자발송 전화번호 지정
        sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')
        params = {
            'type': 'sms',
            'to': engineer_phone_number,
            'from': sender_phone_number,
            'text': engineer_message,
        }

        response = cool.send(params)

        if response.get('success_count', 0) > 0:
            return JsonResponse({"message": "Request approved."})
        else:
            return JsonResponse({"error": "Failed to send approval notification to engineer."}, status=500)

    elif action == "deny":
        # 거부 처리 로직
        return JsonResponse({"message": "Request denied."})

    else:
        return JsonResponse({"error": "Unknown action."}, status=400)


def phonebook_view(request):
    # 데이터베이스에서 모든 Phonebook 항목을 가져옴
    phonebook_entries = Phonebook.objects.all()  # 전체 목록 가져오기

    # 템플릿에 전달할 데이터
    context = {
        'phonebook_entries': phonebook_entries,
    }

    return render(request, 'bems/phonebook.html', context)  # 템플릿 렌더링


def engineer_view(request, entry_id):
    context = {
        'entry_id': entry_id,  # 추가 데이터가 필요한 경우
    }

    return render(request, 'bems/engineer.html', context)


def manager_view(request, entry_id, requested_time):
    context = {
        'entry_id': entry_id,
        'requested_time': requested_time,
    }

    return render(request, 'bems/manager.html', context)

def engineer_approved_view(request, entry_id):
    # DeviceStatus에서 controller_id가 entry_id인 데이터를 가져옴
    device_status = get_object_or_404(DeviceStatus, controller_id=entry_id)

    context = {
        'entry_id': entry_id,
        'device_status': json.dumps({
            'groupselector': device_status.groupselector,
            'speakerselector': device_status.speakerselector,
            'exchanger': device_status.exchanger,
            'remoteamp': device_status.remoteamp,
        }),
    }
    print("engineer_approved: ", context)

    return render(request, 'bems/engineer_approved.html', context)



TCP_IP = '0.0.0.0'  # 모든 인터페이스에서 접속 허용
TCP_PORT = 38600
BUFFER_SIZE = 1024

connections = []

def control(request):
    return render(request, 'bems/control.html')

@csrf_exempt
def control_device(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        command = data.get('command')

        # JSON 객체를 문자열로 변환하여 TCP 서버로 전송
        command_str = json.dumps(command)

        for conn in connections:
            try:
                conn.send(command_str.encode('utf-8'))
            except Exception as e:
                print(f"Error sending command: {e}")

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'}, status=400)


def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(5)
    print("TCP Server started, waiting for connections...")
    while True:
        conn, addr = s.accept()
        print(f"Connection from: {addr}")
        connections.append(conn)
        threading.Thread(target=handle_client, args=(conn,)).start()

def handle_client(conn):
    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            print(f"Received data: {data.decode('utf-8')}")
            process_data(data)
        except Exception as e:
            print(f"Error handling client: {e}")
            break
    conn.close()
    connections.remove(conn)



# 문자 메시지를 보내는 함수
def send_sms(phone_number, message_text):
    api_key = os.getenv('COOL_SMS_API_KEY')
    api_secret = os.getenv('COOL_SMS_API_SECRET')  # 환경 변수로 API Secret 설정 필요

    cool = Message(api_key, api_secret)
    # 문자발송 전화번호 지정
    sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')
    params = {
        'type': 'sms',
        'to': phone_number,
        'from': sender_phone_number,  # 발신자 번호
        'text': message_text,
    }

    try:
        response = cool.send(params)
        if response.get('success_count', 0) > 0:
            return True
        else:
            return False
    except CoolsmsException as e:
        print(f"Error Code: {e.code}, Error Message: {e.msg}")
        return False
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


# 데이터를 처리하는 함수
def process_data(data):
    try:
        data_dict = json.loads(data.decode('utf-8'))
        # print(data_dict)
        controller_id = data_dict.get('controller_id')
        groupselector = data_dict.get('groupselector', 'unknown')
        speakerselector = data_dict.get('speakerselector', 'unknown')
        exchanger = data_dict.get('exchanger', 'unknown')
        remoteamp = data_dict.get('remoteamp', 'unknown')

        # 장치 상태 데이터 저장 또는 업데이트
        device_status, created = DeviceStatus.objects.update_or_create(
            controller_id=controller_id,
            defaults={
                'groupselector': groupselector,
                'speakerselector': speakerselector,
                'exchanger': exchanger,
                'remoteamp': remoteamp,
            }
        )

        if 'x' in (groupselector, speakerselector, exchanger, remoteamp):
            try:
                phonebook_entry = Phonebook.objects.get(id=controller_id)
                manager_phone_number = phonebook_entry.phone_number

                # 엔지니어에게 보낼 메시지
                # 절대 URL 생성: ID가 포함된 URL을 생성
                relative_url = reverse('engineer', args=[controller_id])  # 상대 URL 생성
                nptechon_url = "http://www.nptechon.com"
                yerin_url = "http://www.shimyerin.site"
                engineer_url = f"{yerin_url}{relative_url}"  # 절대 URL 생성

                # 관리자 전화번호 지정
                engineer_phone_number = os.getenv('ENGINEER_PHONE_NUMBER')  # 고정

                # 엔지니어에게 보낼 메시지
                engineer_text = f"이 경로로 접속해주세요: {engineer_url}"

                if send_sms(engineer_phone_number, engineer_text):
                    print("SMS sent successfully to the engineer.")
                else:
                    print("Failed to send SMS to the engineer.")

                # 관리자에게 보낼 메시지
                message_text = "학교에 문제가 발생했습니다."

                if send_sms(manager_phone_number, message_text):
                    print("SMS sent successfully.")
                else:
                    print("Failed to send SMS.")

            except Phonebook.DoesNotExist:
                print(f"Phonebook entry not found for controller_id: {controller_id}")
            except Exception as e:
                print(f"Error processing data: {str(e)}")


    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data: {str(e)}")




# 서버 시작
threading.Thread(target=tcp_server, daemon=True).start()

