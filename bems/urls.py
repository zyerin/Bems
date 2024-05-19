from django.urls import path
# 관련 뷰 임포트
from .views import main_view, send_sms_view, phonebook_view, manager_view, engineer_view, request_approval,  approve_request, engineer_approved_view, control, control_device
from . import views


urlpatterns = [
    path('main/', main_view, name='main'),  # 기본 경로, 즉 "/bems/main"로 접근할 때 메인 페이지
    path('sms/', send_sms_view, name='sms'),  # "/bems/sms/"로 접근할 때 문자 발송 뷰
    path('phonebook/', phonebook_view, name='phonebook'),  # /phonebook 경로 추가
    path('engineer/<int:entry_id>/', engineer_view, name='engineer'),
    path('request_approval/', request_approval, name='request_approval'),
    path('manager/<int:entry_id>/<int:requested_time>/', manager_view, name='manager'),
    path('approve_request_handler/', approve_request, name='approve_request'),
    path('engineer/approved/<int:entry_id>/', engineer_approved_view, name='engineer_approved'),
    path('control/', control, name='control'),
    path('control/control/', control_device, name='control_device'),

]
