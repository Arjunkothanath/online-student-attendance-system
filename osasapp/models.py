from django.db import models
from django.core.exceptions import ValidationError

class AdminDb(models.Model): #Admin Database
    username = models.CharField(max_length=100, unique=True, primary_key=True)
    fullname = models.CharField(max_length=200, default="Administrator")
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.name

class Semester(models.Model):
    number = models.IntegerField(unique=True)  # Example: 1, 2, 3, etc.

    def __str__(self):
        return f"Semester {self.number}"


class Division(models.Model):
    name = models.CharField(max_length=10, unique=True)  # Example: A, B, C

    def __str__(self):
        return f"Division {self.name}"


class Class(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)  # Changed to ForeignKey
    division = models.ForeignKey(Division, on_delete=models.CASCADE)  # Changed to ForeignKey

    def __str__(self):
        return f"{self.department.name} - {self.semester} - {self.division}"


class FacultyDb(models.Model):
    facid = models.CharField(max_length=100, unique=True, primary_key=True)
    fullname = models.CharField(max_length=200)
    password = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fullname} - {self.facid}"

class StudentDb(models.Model):
    studentid = models.CharField(max_length=100, unique=True, primary_key=True)
    fullname = models.CharField(max_length=200)
    password = models.CharField(max_length=255)
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE)  # Now linked to Class

    def __str__(self):
        return f"{self.fullname} - {self.studentid}"

class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=6)
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.class_info}"

class FacultySubject(models.Model):
    faculty = models.ForeignKey(FacultyDb, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="faculties")
    

    def __str__(self):
        return f"{self.faculty.fullname} - {self.subject.name}"

class TimeTable(models.Model):
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE)  # Now linked to Class
    day = models.CharField(
        max_length=10, choices=[
            ("Monday", "Monday"),
            ("Tuesday", "Tuesday"),
            ("Wednesday", "Wednesday"),
            ("Thursday", "Thursday"),
            ("Friday", "Friday"),
        ]
    )
    period = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey(FacultyDb, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("class_info", "day", "period")

    def __str__(self):
        return f"{self.class_info} - {self.day} - Period {self.period}"
    
from django.utils import timezone

class AttendanceSheet(models.Model):
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    day = models.CharField(max_length=10, choices=[
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ])
    period_number = models.IntegerField()
    student = models.ForeignKey(StudentDb, on_delete=models.CASCADE)
    is_present = models.BooleanField()

    def __str__(self):
        return f"{self.student.fullname} - {self.subject.code} - {self.date}"

class Attendance(models.Model):
    student = models.ForeignKey(StudentDb, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    total_hours = models.IntegerField(default=0)
    total_present = models.IntegerField(default=0)
    total_absent = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.fullname} - {self.subject.code}"

class LeavePeriods(models.Model):
    faculty = models.ForeignKey(FacultyDb, on_delete=models.CASCADE)
    date = models.DateField()
    period = models.IntegerField()
    class_info = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.faculty.fullname} - Period {self.period} on {self.date}"