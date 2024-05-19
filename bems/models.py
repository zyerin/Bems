from django.core.exceptions import ObjectDoesNotExist
from django.db import models

# Create your models here.
class Phonebook(models.Model):
    phone_number = models.CharField('휴대폰 번호', max_length=30, unique=True)
    # auth_number = models.CharField('인증번호', max_length=30)
    name = models.CharField(max_length=100, blank=True, null=True)  # 순차적인 번호가 할당될 필드

    class Meta:
        db_table = 'authentications' # DB 테이블명
        verbose_name_plural = "휴대폰인증 관리 페이지" # Admin 페이지에서 나타나는 설명

    def save(self, *args, **kwargs):
        # `name` 필드가 비어있으면 순차적인 이름을 생성
        if not self.name:
            try:
                # 최근 생성된 ID를 찾음
                last_id = Phonebook.objects.latest('id').id
                self.name = f'학교 {last_id + 1}'  # 순차적인 이름 생성
            except ObjectDoesNotExist:
                # 데이터베이스에 항목이 없으면 첫 번째 번호로 설정
                self.name = '학교 1'

        super().save(*args, **kwargs)  # 부모 클래스의 save 호출

    def __str__(self):
        return self.name

class SupportRequest(models.Model):
    requested_time = models.CharField(max_length=10)  # 엔지니어가 선택한 시간
    status = models.CharField(max_length=10, default="pending")  # 요청 상태: pending, approved, denied

    def __str__(self):
        return f"{self.engineer_name}: {self.requested_time} ({self.status})"

class DeviceStatus(models.Model):
    controller_id = models.IntegerField()
    groupselector = models.CharField(max_length=1)
    speakerselector = models.CharField(max_length=1)
    exchanger = models.CharField(max_length=1)
    remoteamp = models.CharField(max_length=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DeviceStatus for Controller {self.controller_id}"