from django.urls import path
from . import views

urlpatterns = [
    path("", views.supabase_login, name="login"),
    path("signup/", views.supabase_signup, name="signup"),
    path("home_page/", views.home_page, name="home_page"),
    path("logout/", views.supabase_logout, name="logout")
    #path("upload/", views.upload_file, name="upload"),
]