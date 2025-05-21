from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
from uuid import uuid4
import os
from ..models import Manager, SupportRequest


def send_sms_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method."}, status=405)

    entry_id = request.POST.get('entry_id')

    if not entry_id:
        return JsonResponse({"error": "Entry ID not provided."}, status=400)

    try:
        # Manager에서 엔트리 찾기
        phonebook_entry = Manager.objects.get(id=entry_id)
        manager_phone_number = phonebook_entry.phone_number

        # 엔지니어에게 보낼 메시지
        # 절대 URL 생성: ID가 포함된 URL을 생성
        relative_url = reverse('engineer', args=[entry_id])  # 상대 URL 생성
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
        engineer_phone_number = os.getenv('ENGINEER_PHONE_NUMBER') # 고정

        # 문자발송 전화번호 지정
        sender_phone_number = os.getenv('SENDER_PHONE_NUMBER')

        # 문자 메시지 생성
        engineer_sms_text = (
            f"BEMS 문제 발생\n"
            f"{engineer_url}\n"
            f"비밀번호: {temp_password}"
        )
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
        return JsonResponse({"error": "Manager entry not found."}, status=404)

    except CoolsmsException as e:
        return JsonResponse({"error": f"Error Code: {e.code}, Error Message: {e.msg}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 1회용 비밀번호 발급 함수
def generate_temp_password():
    return str(uuid4())[:8]  # 8자리 랜덤 비밀번호