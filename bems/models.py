from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.conf import settings

class Manager(models.Model):
    phone_number = models.CharField('휴대폰 번호', max_length=30, unique=True)
    school_number = models.CharField('학교 번호', max_length=100, blank=True, null=True)  # 자동 생성
    school_name = models.CharField('학교 이름', max_length=100)  # 사용자가 입력

    class Meta:
        db_table = 'manager' # DB 테이블명
        verbose_name_plural = "학교 관리자" # Admin 페이지에서 나타나는 설명

    # 모델을 저장할 때 자동으로 호출되는 메서드
    def save(self, *args, **kwargs):
        # school_number가 비어 있으면 자동 생성
        if not self.school_number:
            try:
                # 최근 생성된 ID를 찾음
                last_id = Manager.objects.latest('id').id
                self.school_number = f'학교 {last_id + 1}'  # 순차적인 이름 생성
            except ObjectDoesNotExist:
                # 데이터베이스에 항목이 없으면 첫 번째 번호로 설정
                self.school_number = '학교 1'

        super().save(*args, **kwargs)  # 부모 클래스의 save 호출

    # 객체를 출력할 때 (print(manager_obj) 또는 Admin에서 리스트 보여줄 때) -> school_number이 보여지도록
    def __str__(self):
        return self.school_number

class Engineer(models.Model):
    name = models.CharField('이름', max_length=100)
    phone_number = models.CharField('전화번호', max_length=30, unique=True)
    company = models.CharField('소속 회사', max_length=100, blank=True, null=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        db_table = 'engineers'
        verbose_name = '엔지니어'
        verbose_name_plural = '엔지니어 목록'

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class SupportRequest(models.Model):
    entry = models.ForeignKey(Manager, on_delete=models.CASCADE)
    requested_time = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=10, default="pending")     # 관리자의 승인/거부
    temp_password = models.CharField(max_length=100, default='temp')
    is_authenticated = models.BooleanField(default=False)   # 관리자/엔지니어의 로그인 여부
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.entry.school_name}: ({self.status})"


class DeviceStatus(models.Model):
    controller_id = models.IntegerField()
    groupselector = models.CharField(max_length=1)
    speakerselector = models.CharField(max_length=1)
    exchanger = models.CharField(max_length=1)
    remoteamp = models.CharField(max_length=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DeviceStatus for Controller {self.controller_id}"