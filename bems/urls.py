from django.urls import path
from django.urls import path
from bems.views import (
    main_view, phonebook_view, send_sms_view,
    engineer_view, engineer_login, engineer_request_approval, engineer_approved_view,
    manager_view, manager_login, manager_response,
    control, control_device
)

urlpatterns = [
    path('main/', main_view, name='main'),  # 기본 경로, 즉 "/bems/main"로 접근할 때 메인 페이지
    path('sms/', send_sms_view, name='sms'),  # "/bems/sms/"로 접근할 때 문자 발송 뷰
    path('phonebook/', phonebook_view, name='phonebook'),  # /phonebook 경로 추가
    path('engineer/<int:entry_id>/', engineer_view, name='engineer'),
    path('engineer_request_approval/', engineer_request_approval, name='engineer_request_approval'),
    path('manager/<int:entry_id>/', manager_view, name='manager'),
    path('manager_response_handler/', manager_response, name='manager_response'),
    path('engineer/approved/<int:entry_id>/', engineer_approved_view, name='engineer_approved'),
    path('control/', control, name='control'),
    path('control/control/', control_device, name='control_device'),
    path('login/engineer/', engineer_login, name='engineer_login'),
    path('login/manager/', manager_login, name='manager_login'),
]
