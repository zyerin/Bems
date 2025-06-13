from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ..models import Manager, SupportRequest, DeviceStatus
from django.core.exceptions import ObjectDoesNotExist
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
from uuid import uuid4
import json
from django.utils import timezone
from datetime import timedelta
import os

# 엔지니어 페이지 렌더링
def engineer_view(request, entry_id):
    context = {
        'entry_id': entry_id,
    }

    return render(request, 'bems/engineer.html', context)



# 엔지니어가 접속 → 서버에 비밀번호 제출 → 인증 서버에서 확인 → 통과 시 제어 허용
@csrf_exempt
def engineer_login(request):
    """
    엔지니어 비밀번호 인증 처리
    """
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        password = request.POST.get('password')

        try:
            # 가장 최근에 생성된 요청을 기준으로 인증
            manager_entry = Manager.objects.get(id=entry_id)
            support = SupportRequest.objects.filter(entry=manager_entry).order_by('-created_at').first()

            if support is None:
                return JsonResponse({'status': 'no matching request'}, status=404)

            print(f"temp password: {support.temp_password}")
            if support.temp_password == password:
                support.is_authenticated = True
                support.save()
                log_access(entry_id, "engineer", "login", True)
                return JsonResponse({'status': 'success'})
            else:
                log_access(entry_id, "engineer", "login", False)
                return JsonResponse({'status': 'invalid password'}, status=401)

        except Exception as e:
            return JsonResponse({'status': f'error: {str(e)}'}, status=500)


@csrf_exempt
def engineer_request_approval(request):
    """
    로그인 성공 후 엔지니어가 관리자에게 승인 요청
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    # POST 요청에서 엔트리 ID 추출
    entry_id = request.POST.get('entry_id')

    if not entry_id:
        return JsonResponse({"error": "Missing required parameters(entry_id)."}, status=400)

    try:
        # Phonebook에서 엔트리 찾기
        manager_entry = Manager.objects.get(id=entry_id)
        manager_phone_number = manager_entry.phone_number

        # 문자발송 전화번호 지정
        sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')

        # 관리자에게 전송할 URL 생성
        relative_url = reverse('manager', args=entry_id)
        nptechon_url = "http://www.nptechon.com"
        yerin_url = "http://www.shimyerin.site"
        approval_url = f"{yerin_url}{relative_url}"
        print(approval_url)

        # 랜덤 비밀번호 생성
        temp_password = str(uuid4())[:8]
        # SupportRequest에 저장
        manager_entry = Manager.objects.get(id=entry_id)

        support_request, created = SupportRequest.objects.update_or_create(
            entry=manager_entry,
            defaults={
                'temp_password': temp_password,
                'status': 'pending',
                'is_authenticated': False
            }
        )
        # created_at도 강제로 갱신
        support_request.created_at = timezone.now()
        support_request.save()
        log_access(entry_id, "engineer", "request", True)

        # 관리자에게 보낼 메시지
        manager_sms_text = (
            f"엔지니어 요청 승인: {approval_url}\n"
            f"비밀번호: {temp_password}"
        )

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
            log_access(entry_id, "engineer", "request", False)
            return JsonResponse({"error": "Failed to send approval request."}, status=500)

    except ObjectDoesNotExist:
        return JsonResponse({"error": "Engineer not found."}, status=404)
    except CoolsmsException as e:
        return JsonResponse({"error": f"Error Code: {e.code}, Error Message: {e.msg}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def engineer_approved_view(request, entry_id):
    """
    엔지니어 승인 여부 확인 후 제어 페이지 렌더링
    """
    # 1. 승인된 요청인지 확인
    try:
        support_request = SupportRequest.objects.get(entry_id=entry_id, status='approved', is_authenticated=True)
    except SupportRequest.DoesNotExist:
        return render(request, 'bems/not_authorized.html', status=403)

    # 1시간 초과 시 상태 되돌리기
    if support_request.status == "approved" and support_request.created_at + timedelta(hours=1) < timezone.now():
        support_request.status = "pending"
        support_request.is_authenticated = False
        support_request.save()

    # 2. 장비 상태 데이터 조회
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


def log_access(entry_id, user_type, message, success):
    try:
        print(f"engineer id: {entry_id}")
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "log.txt")

        with open(log_file, 'a') as f:
            now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{now}] {entry_id}번 {user_type.upper()} {message.upper()} {'SUCCESS' if success else 'FAIL'}\n")
    except Exception as e:
        print(f"로그 기록 중 오류 발생: {e}")
