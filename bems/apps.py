from django.apps import AppConfig


class BemsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bems"

    def ready(self):
        from .views.tcp_control import start_tcp_server
        start_tcp_server()  # tcp 서버 시작! (서버가 실행되면서 자동으로 TCP 서버도 백그라운드로 실행)
