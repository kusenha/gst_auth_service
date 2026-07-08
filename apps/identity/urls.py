from django.urls import path

from apps.identity.views import LoginView, RefreshView, RegisterView, change_password, me

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", me, name="me"),
    path("change-password/", change_password, name="change-password"),
]
