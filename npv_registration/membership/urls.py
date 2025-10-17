# membership/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_member, name='register'),
    path('verify/<str:membership_number>/', views.verify_member, name='verify'),
    path('certificate/<str:membership_number>/', views.download_certificate, name='download_certificate'),
    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/<str:membership_number>/', views.MemberDetailView.as_view(), name='member_detail'),
]
