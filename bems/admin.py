from django.contrib import admin
from .models import Manager, Engineer, SupportRequest, DeviceStatus

# Register your models here.

admin.site.register(Manager)
admin.site.register(Engineer)
admin.site.register(SupportRequest)
admin.site.register(DeviceStatus)