
from django.urls import path
from accounts import views

urlpatterns = [
    path('home/' , views.home, name='home'),
    path('login/' , views.login, name='login'),
    path('register/' , views.register, name='register')
]