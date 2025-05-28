from django.contrib import admin
from .models import FacultyDb,AdminDb,StudentDb,Subject,FacultySubject,Department,Class,TimeTable, Semester, Division, Attendance,AttendanceSheet,LeavePeriods
# Register your models here.
admin.site.register(FacultyDb)
admin.site.register(AdminDb)
admin.site.register(StudentDb)
admin.site.register(Subject)
admin.site.register(FacultySubject)
admin.site.register(Department)
admin.site.register(Class)
admin.site.register(TimeTable)
admin.site.register(Semester)
admin.site.register(Division)
admin.site.register(AttendanceSheet)
admin.site.register(Attendance)
admin.site.register(LeavePeriods)