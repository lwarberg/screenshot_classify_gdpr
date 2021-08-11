from django.contrib import admin
from .models import Screenshot
from .models import Response
from .models import Profile
from .models import Task


# Register your models here.
@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    pass


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass