from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from ..models import Manager, SupportRequest
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
import os
import datetime


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
                log_access(entry_id, "engineer", True)
                return JsonResponse({'status': 'success'})
            else:
                log_access(entry_id, "engineer", False)
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

        # 엔지니어 전화번호 지정
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


def log_access(entry_id, user_type, success):
    """
    관리자 로그인 성공/실패 로그 저장
    """
    import os
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'Logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{entry_id}_log.txt")

    with open(log_file, 'a') as f:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{now}] {user_type.upper()} LOGIN {'SUCCESS' if success else 'FAIL'}\n")
