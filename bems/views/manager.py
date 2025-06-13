from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ..models import Manager, SupportRequest, Engineer
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
import os
from django.utils import timezone
from datetime import timedelta


# 관리자가 승인할 수 있는 페이지 렌더링
def manager_view(request, entry_id):
    context = {
        'entry_id': entry_id,
    }
    return render(request, 'bems/manager.html', context)


@csrf_exempt
def manager_login(request):
    """
    관리자 비밀번호 로그인 처리
    """
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        password = request.POST.get('password')

        try:
            # 가장 최근에 생성된 요청을 기준으로 인증
            phonebook_entry = Manager.objects.get(id=entry_id)
            support = SupportRequest.objects.filter(entry=phonebook_entry).order_by('-created_at').first()

            if support is None:
                return JsonResponse({'status': 'no matching request'}, status=404)

            if support.temp_password == password:
                support.is_authenticated = True
                support.save()
                log_access(entry_id, "manager", "login", True)
                return JsonResponse({'status': 'success'})
            else:
                log_access(entry_id, "engineer", "login", False)
                return JsonResponse({'status': 'invalid password'}, status=401)

        except Exception as e:
            return JsonResponse({'status': f'error: {str(e)}'}, status=500)


@csrf_exempt
def manager_response(request):
    """
    관리자가 승인 또는 거부 처리 후 엔지니어에게 문자 발송
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    action = request.POST.get("action")  # 승인 또는 거부
    entry_id = request.POST.get("entry_id")

    try:
        # Manager 인스턴스 조회
        phonebook_entry = Manager.objects.get(id=entry_id)

        # 최신 SupportRequest 조회
        support_request = SupportRequest.objects.filter(entry=phonebook_entry).order_by('-created_at').first()

        if not support_request:
            return JsonResponse({"error": "지원 요청이 존재하지 않습니다."}, status=404)

        if action == "approve":
            # 상태 업데이트
            support_request.status = "approved"
            support_request.is_authenticated = True
            support_request.save()
            log_access(entry_id, "manager", "approve", True)

            # 승인 메시지 전송
            relative_url = reverse('engineer_approved', args=[entry_id])
            yerin_url = "http://www.shimyerin.site"
            engineer_url = f"{yerin_url}{relative_url}"
            engineer_message = f"요청이 승인되었습니다: {engineer_url}"

            api_key = os.getenv('COOL_SMS_API_KEY')
            api_secret = os.getenv('COOL_SMS_API_SECRET')
            cool = Message(api_key, api_secret)

            # 엔지니어 전화번호: 첫 번째 등록된 엔지니어 사용
            engineer = Engineer.objects.first()
            if not engineer:
                return JsonResponse({"error": "등록된 엔지니어가 없습니다."}, status=404)
            engineer_phone_number = engineer.phone_number
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
                log_access(entry_id, "manager", "approve", False)
                return JsonResponse({"error": "문자 전송 실패"}, status=500)

        elif action == "deny":
            support_request.status = "denied"
            support_request.is_authenticated = False
            support_request.save()
            log_access(entry_id, "manager", "deny", True)

            # 승인 메시지 전송
            engineer_message = "해당 요청이 관리자에 의해 거부되었습니다."
            api_key = os.getenv('COOL_SMS_API_KEY')
            api_secret = os.getenv('COOL_SMS_API_SECRET')
            cool = Message(api_key, api_secret)

            # 엔지니어 전화번호: 첫 번째 등록된 엔지니어 사용
            engineer = Engineer.objects.first()
            if not engineer:
                return JsonResponse({"error": "등록된 엔지니어가 없습니다."}, status=404)
            engineer_phone_number = engineer.phone_number
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
                log_access(entry_id, "manager", "deny", False)
                return JsonResponse({"error": "문자 전송 실패"}, status=500)

        else:
            return JsonResponse({"error": "Unknown action."}, status=400)

    except Manager.DoesNotExist:
        return JsonResponse({"error": "존재하지 않는 관리자 ID입니다."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"처리 중 오류 발생: {str(e)}"}, status=500)


def log_access(entry_id, user_type, message, success):
    try:
        print(f"manager id: {entry_id}")
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "log.txt")

        with open(log_file, 'a') as f:
            now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{now}] 학교{entry_id} {user_type.upper()} {message.upper()} {'SUCCESS' if success else 'FAIL'}\n")
    except Exception as e:
        print(f"로그 기록 중 오류 발생: {e}")
