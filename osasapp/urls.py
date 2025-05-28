"""
URL configuration for osas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from .import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.login,name='login'),
    path('login/',views.login,name='login'),
    path('register/',views.register,name='register'),
    path('profilefac/', views.profilefac, name='profilefac'), #faculty start page
    path('factimetable/', views.factimetable, name='factimetable'),
    path('class_timetable/', views.class_timetable, name='class_timetable'),
    path('facattendance/', views.facattendance, name='facattendance'),
    path('apply_duty_leave/', views.apply_duty_leave, name='apply_duty_leave'),
    path('faculty/takeattendance/<int:period_number>/<int:class_id>/<int:subject_id>/', views.takeattendance, name='takeattendance'),
    path("goSubstitute/", views.goSubstitute, name="goSubstitute"),
    path("takeattendance2/", views.takeattendance2, name="takeattendance2"),
    path('submitAttendance/', views.submitAttendance, name='submitAttendance'),
    path('profilestu/', views.profilestu, name='profilestu'), # student start page
    path('stutimetable/', views.stutimetable, name='stutimetable'),
    path('stuattendance/', views.stuattendance, name='stuattendance'),
     path("get_class_attendance/<int:subject_id>/", views.get_class_attendance, name="get_class_attendance"),
    path('faculty/',views.faculty,name='faculty'), # admin start page
    path('upload_faculty/', views.upload_faculty, name='upload_faculty'),
    path('logout/',views.logout,name='logout'),
    path('student/',views.student,name='student'),
    path('upload_students/', views.upload_students, name='upload_students'),
    path('subject/',views.subject,name='subject'),
    path('upload_subjects/', views.upload_subjects, name='upload_subjects'),
    path('timetable/',views.timetable,name='timetable'),
    path("save_timetable/", views.save_timetable, name="save_timetable"),
    
]
