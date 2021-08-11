from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('random/<str:username>', views.random, name='random'),
    path('random/<str:username>/<str:screenshot_id>', views.display_screenshot, name='random'),
    path('view/<str:screenshot_id>', views.view, name='view'),
    path('display/<str:screenshot_id>', views.display_screenshot, name='view'),
    path('review/<str:username>', views.review, name='review'),
    path('review/<str:username>/<str:screenshot_id>', views.display_screenshot, name='review'),
    path('classify', views.classify, name='task'),
    path('classify/<str:screenshot_id>', views.display_screenshot, name='screenshot'),
    path('accounts/', include('django.contrib.auth.urls')),
]
