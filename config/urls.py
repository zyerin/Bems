from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),  # 관리자 패널 경로
    path("bems/", include("bems.urls")),  # 앱 경로 연결
]
