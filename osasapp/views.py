from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse,HttpResponseForbidden, JsonResponse
from django.contrib.auth.hashers import make_password,check_password
from .models import AdminDb,FacultyDb,StudentDb,Subject,FacultySubject,Department,Semester,Class,Division
import csv,io
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from .models import AdminDb, FacultyDb, StudentDb, TimeTable, Class,LeavePeriods  # Ensure you have models for faculty and students
import pandas as pd
######################################## LOGIN AND REGISTRATION START ######################################################
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        fullname = request.POST.get("fullname")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        
        if AdminDb.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")
        
        user = AdminDb(username=username, fullname=fullname, password=password)
        user.save()
        
        messages.success(request, "User registered successfully!")
        return redirect("login")  
    
    return render(request, 'register.html')
def login(request):
    if request.method == 'POST':
        user_id = request.POST.get("id").strip()  # Strip spaces to avoid errors
        password = request.POST.get("password").strip()
        user_type = request.POST.get("user_type")

        try:
            # 🔹 Use the correct fields for each user type
            if user_type == 'admin':
                user = AdminDb.objects.get(username=user_id)  # Use 'username' for Admin
            elif user_type == 'faculty':
                user = FacultyDb.objects.get(facid=user_id)  # Use 'facid' for Faculty
            elif user_type == 'student':
                user = StudentDb.objects.get(studentid=user_id)  # Use 'studentid' for Student
            else:
                messages.error(request, "Invalid user type selected.")
                return redirect('login')

            # 🔹 Check password
            if password == user.password:  
                messages.success(request, "Login successful!")
                request.session['user_type'] = user_type
                request.session['id'] = user_id  
                request.session['full_name'] = user.fullname

                # 🔹 Redirect based on user type
                if user_type == 'admin':
                    return redirect('faculty')  
                elif user_type == 'faculty':
                    return redirect('profilefac')  
                elif user_type == 'student':
                    return redirect('profilestu')  
            else:
                messages.error(request, "Invalid username or password.")
        except (AdminDb.DoesNotExist, FacultyDb.DoesNotExist, StudentDb.DoesNotExist):
            messages.error(request, "User does not exist.")

    return render(request, 'login.html')

def logout(request):
    # Clear the session
    request.session.flush()  # This will clear all session data
    messages.success(request, "You have been logged out.")
    return redirect('login')  # Redirect to the login page
######################################## LOGIN AND REGISTRATION COMPLETE ######################################################

######################################## ADMINDB VIEWS START ######################################################
def faculty(request):
    if request.session.get('user_type') == 'admin':
        departments = Department.objects.all()
        return render(request, "Admin/faculty.html", {"departments": departments})
    else:
        messages.error(request, "You are not authorized to access this page.")
        return redirect('login')

def upload_faculty(request):
    if request.method == 'POST' and request.FILES.get('faculty_file'):
        faculty_file = request.FILES['faculty_file']
        department_code = request.POST.get('department')

        if not department_code:
            messages.error(request, "Department is missing.")
            return redirect('faculty')

        try:
            department = Department.objects.get(code=department_code)
        except Department.DoesNotExist:
            messages.error(request, "Invalid department selected.")
            return redirect('faculty')

        # Save file
        fs = FileSystemStorage()
        filename = fs.save(f'uploads/{department.code}/{faculty_file.name}', faculty_file)
        uploaded_file_url = fs.url(filename)

        # Read the uploaded file
        try:
            if faculty_file.name.endswith('.csv'):
                df = pd.read_csv(faculty_file)
            elif faculty_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(faculty_file)
            else:
                messages.error(request, "Invalid file format. Upload CSV or Excel.")
                return redirect('faculty')
        except Exception as e:
            messages.error(request, f"File error: {str(e)}")
            return redirect('faculty')

        # Validate Required Columns
        required_columns = {'facid', 'fullname', 'password'}
        if not required_columns.issubset(df.columns):
            messages.error(request, "Invalid file structure. Must contain: facid, fullname, password.")
            return redirect('faculty')

        # Save to FacultyDb
        for _, row in df.iterrows():
            FacultyDb.objects.create(
                facid=row['facid'],
                fullname=row['fullname'],
                password=row['password'],  # Hash this in production
                department=department
            )

        messages.success(request, f"Faculty uploaded successfully for {department.name.upper()}.")
        return render(request, 'Admin/faculty.html', {
            'uploaded_file': {'url': uploaded_file_url, 'name': faculty_file.name},
            "departments": Department.objects.all()
        })

    return redirect('faculty')

def faculty_registration(request):
    departments = Department.objects.all()
    return render(request, 'Admin/faculty.html', {"departments": departments})
#---------------------------------------------------------------------------------------#
def student(request):
    return render(request,"Admin/student.html")
def upload_students(request):
    uploaded_file_url = None
    if request.method == "POST" and request.FILES.get("student_file"):
        student_file = request.FILES["student_file"]

        # Save the file temporarily
        fs = FileSystemStorage()
        filename = fs.save(f"uploads/{student_file.name}", student_file)
        file_path = fs.path(filename)
        uploaded_file_url = fs.url(filename)

        try:
            # Read the uploaded file (CSV or Excel)
            if student_file.name.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif student_file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                messages.error(request, "Invalid file format. Please upload a CSV or Excel file.")
                return redirect("upload_students")

            # Check required columns
            required_columns = {"Student ID", "Full Name", "Department", "Semester", "Division", "Password"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "File must have columns: Student ID, Full Name, Department, Semester, Division, Password")
                return redirect("upload_students")

            # 🔹 Department Mapping (Short codes → Full names)
            DEPARTMENT_MAPPING = {
                "CSE": "Computer Science Engineering",
                "ECE": "Electronics & Communication Engineering",
                "EEE": "Electrical & Electronic Engineering",
                "ME": "Mechanical Engineering",
                "CE": "Civil Engineering",
                "ERE": "Electronics & Computer Engineering"
            }

            # Process the data
            for _, row in df.iterrows():
                student_id = row["Student ID"].strip()
                full_name = row["Full Name"].strip()
                department_code = row["Department"].strip()
                semester_number = str(row["Semester"]).strip()
                division_name = str(row["Division"]).strip()
                raw_password = row["Password"].strip()

                # 🔹 Convert Department Code to Full Name
                department_name = DEPARTMENT_MAPPING.get(department_code, department_code)  # If no mapping, keep original

                # 🔹 Check if Department exists using full name
                department = Department.objects.filter(name__iexact=department_name).first()
                if not department:
                    messages.error(request, f"Department '{department_name}' not found. Skipping student '{full_name}'.")
                    continue

                # 🔹 Ensure Semester is an Integer
                try:
                    semester_number = int(semester_number)
                except ValueError:
                    messages.error(request, f"Invalid semester '{semester_number}' for student '{full_name}'. Skipping.")
                    continue

                semester = Semester.objects.filter(number=semester_number).first()
                if not semester:
                    messages.error(request, f"Semester '{semester_number}' not found. Skipping student '{full_name}'.")
                    continue

                # 🔹 Case-insensitive Division Matching
                division = Division.objects.filter(name__iexact=division_name).first()
                if not division:
                    messages.error(request, f"Division '{division_name}' not found. Skipping student '{full_name}'.")
                    continue

                # 🔹 Ensure Class Record Exists (Auto-create if missing)
                class_info, created = Class.objects.get_or_create(
                    department=department, semester=semester, division=division
                )

                if created:
                    print(f"Created new class for {department.name}, Semester {semester.number}, Division {division.name}.")

                # ✅ Use 'studentid' Instead of 'id'
                student, created = StudentDb.objects.get_or_create(
                    studentid=student_id,  
                    defaults={
                        "fullname": full_name,
                        "password": raw_password,
                        "class_info": class_info,
                    },
                )

                if not created:
                    # Update existing student data
                    student.fullname = full_name
                    student.password = raw_password
                    student.class_info = class_info
                    student.save()

            messages.success(request, "Students uploaded successfully.")
            return redirect("upload_students")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("upload_students")

    return render(request, "Admin/student.html", {"uploaded_file_url": uploaded_file_url})


#---------------------------------------------------------------------------------------#
def subject(request):
    return render(request,"Admin/subject.html")

def upload_subjects(request):
    if request.method == "POST" and request.FILES.get("subject_file"):
        subject_file = request.FILES["subject_file"]

        # Save the file temporarily
        fs = FileSystemStorage()
        filename = fs.save(f"uploads/{subject_file.name}", subject_file)
        file_path = fs.path(filename)

        try:
            # Read the uploaded file (CSV or Excel)
            if subject_file.name.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif subject_file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                messages.error(request, "Invalid file format. Please upload a CSV or Excel file.")
                return redirect("upload_subjects")

            # Check required columns
            required_columns = {"Subject", "Subject Code", "Department", "Semester", "Faculty IDs"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "File must have columns: Subject, Subject Code, Department, Semester, Faculty IDs")
                return redirect("upload_subjects")

            # Process the data
            for _, row in df.iterrows():
                subject_name = row["Subject"].strip()
                subject_code = row["Subject Code"].strip()
                department_code = row["Department"].strip().lower()  # Department column contains the department code
                semester_number = int(row["Semester"])
                faculty_ids = row["Faculty IDs"].split(",")  # Split faculty IDs

                # Get the department using the department code (case insensitive)
                department = Department.objects.filter(code__iexact=department_code).first()
                if not department:
                    messages.error(request, f"Department with code '{department_code}' not found. Skipping subject '{subject_name}'.")
                    continue  # Skip this row if department is missing

                # Get or create the semester
                semester, _ = Semester.objects.get_or_create(number=semester_number)

                # Get or create two classes (Div A & B)
                division_a, _ = Division.objects.get_or_create(name="A")
                division_b, _ = Division.objects.get_or_create(name="B")

                class_a, _ = Class.objects.get_or_create(department=department, semester=semester, division=division_a)
                class_b, _ = Class.objects.get_or_create(department=department, semester=semester, division=division_b)

                # Create subject with subject code and assign it to both classes
                subject_a, _ = Subject.objects.get_or_create(name=subject_name, code=subject_code, class_info=class_a)
                subject_b, _ = Subject.objects.get_or_create(name=subject_name, code=subject_code, class_info=class_b)

                # Assign faculty members
                for fac_id in faculty_ids:
                    fac_id = fac_id.strip()
                    faculty = FacultyDb.objects.filter(facid=fac_id).first()
                    if faculty:
                        FacultySubject.objects.get_or_create(faculty=faculty, subject=subject_a)
                        FacultySubject.objects.get_or_create(faculty=faculty, subject=subject_b)
                    else:
                        messages.warning(request, f"Faculty ID {fac_id} not found, skipping.")

            messages.success(request, "Subjects and faculty assignments uploaded successfully.")
            return redirect("upload_subjects")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("upload_subjects")

    return render(request, "Admin/subject.html")
#---------------------------------------------------------------------------------------#
def timetable(request):
    classes = Class.objects.all()
    return render(request, "Admin/timetable.html", {"classes": classes})

def save_timetable(request):
    if request.method == "POST" and request.FILES.get("timetable_file"):
        timetable_file = request.FILES["timetable_file"]
        class_info_id = request.POST.get("class_info")  # Get class from form

        try:
            class_info = Class.objects.get(id=class_info_id)  # Validate class selection
        except Class.DoesNotExist:
            messages.error(request, "Invalid class selection.")
            return redirect("timetable")

        try:
            # Read uploaded file (CSV or Excel)
            if timetable_file.name.endswith(".csv"):
                df = pd.read_csv(timetable_file)
            elif timetable_file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(timetable_file)
            else:
                messages.error(request, "Invalid file format. Please upload a CSV or Excel file.")
                return redirect("timetable")

            # Check required columns
            required_columns = {"Day", "Period", "Subject Code", "Faculty ID"}
            if not required_columns.issubset(df.columns):
                messages.error(request, "Invalid file format. Missing required columns.")
                return redirect("timetable")

            # Process each row
            for _, row in df.iterrows():
                day = row["Day"]
                period = row["Period"]
                subject_code = row["Subject Code"]
                faculty_id = row["Faculty ID"]

                # Retrieve faculty
                faculty = FacultyDb.objects.filter(facid=faculty_id).first()
                if not faculty:
                    messages.error(request, f"Faculty ID {faculty_id} not found.")
                    continue

                # Retrieve subject (now filtered by class)
                subjects = Subject.objects.filter(code=subject_code, class_info=class_info)
                if subjects.exists():
                    for subject in subjects:
                        TimeTable.objects.create(
                            class_info=class_info,
                            day=day,
                            period=period,
                            subject=subject,
                            faculty=faculty
                        )
                else:
                    messages.error(request, f"Subject {subject_code} not found for the selected class.")

            messages.success(request, "Timetable uploaded successfully!")
            return redirect("timetable")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect("timetable")

    return redirect("timetable")


######################################## ADMINDB VIEWS COMPLETE ######################################################
######################################## FACULTY VIEWS START ######################################################
import datetime

def profilefac(request):
    """Faculty Profile View with Timetable for Duty Leave"""
    if request.session.get('user_type') == 'faculty':
        faculty_id = request.session.get('id')
        try:
            faculty = FacultyDb.objects.get(facid=faculty_id)

            # Get today's weekday name
            today = datetime.datetime.today().strftime('%A')

            # Get faculty's timetable for today
            faculty_timetable_today = TimeTable.objects.filter(faculty=faculty, day=today)

            return render(request, 'Faculty/profilefac.html', {
                'fullname': faculty.fullname,
                'facultyid': faculty.facid,
                'department': faculty.department if faculty.department else "N/A",  # Fixed 'department' attribute
                'faculty_timetable_today': faculty_timetable_today,  # Passing today's timetable
            })
        except FacultyDb.DoesNotExist:
            messages.error(request, "Faculty profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')


def factimetable(request):
    if request.session.get('user_type') == 'faculty':
        faculty_id = request.session.get('id')
        try:
            faculty = FacultyDb.objects.get(facid=faculty_id)
            timetable_entries = TimeTable.objects.filter(faculty=faculty).order_by('day', 'period')

            # Define number of periods per day
            total_periods_per_day = {
                "Monday": 7,
                "Tuesday": 7,
                "Wednesday": 7,
                "Thursday": 7,
                "Friday": 6
            }

            # Organize timetable by weekdays with placeholders for missing periods
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            timetable_data = {}

            for day in day_order:
                timetable_data[day] = []
                for period in range(1, total_periods_per_day[day] + 1):  # ✅ Loop correctly per day
                    period_entry = next(
                        (entry for entry in timetable_entries if entry.day == day and entry.period == period),
                        None
                    )
                    if period_entry:
                        timetable_data[day].append({
                            'period': period,
                            'subject_code': period_entry.subject.code,
                            'department_code': period_entry.class_info.department.code,
                            'semester': period_entry.class_info.semester.number,
                            'division': period_entry.class_info.division.name,
                            'class_id': period_entry.class_info.id,
                            'subject_id': period_entry.subject.id
                        })
                    else:
                        timetable_data[day].append({'period': period, 'no_class': True})  # ✅ Add No Class entry

            return render(request, 'Faculty/factimetable.html', {
                'timetable_data': timetable_data
            })
        except FacultyDb.DoesNotExist:
            messages.error(request, "Faculty profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')



def class_timetable(request):
    """Fetch and display the timetable for a selected class."""
    if request.session.get('user_type') == 'faculty':
        selected_class_id = request.GET.get('class_id')  # Get selected class from the dropdown

        classes = Class.objects.all()  # Fetch all available classes

        timetable_data = None
        selected_class = None

        if selected_class_id:
            try:
                selected_class = Class.objects.get(id=selected_class_id)
                timetable_entries = TimeTable.objects.filter(class_info=selected_class).order_by('day', 'period')

                # Organize timetable by weekdays
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                timetable_data = {day: [] for day in day_order}

                for entry in timetable_entries:
                    timetable_data[entry.day].append({
                        'subject_code': entry.subject.code,
                        'faculty': entry.faculty.fullname
                    })
            except Class.DoesNotExist:
                messages.error(request, "Invalid class selected.")

        return render(request, 'Faculty/class_timetable.html', {
            'classes': classes,
            'timetable_data': timetable_data,
            'selected_class': selected_class
        })
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')
    
from django.shortcuts import  get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import StudentDb, TimeTable, AttendanceSheet, Attendance, Class, Subject

def takeattendance(request, period_number, class_id, subject_id):
    faculty_id = request.session.get('id')

    if request.session.get('user_type') != 'faculty':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    class_info = get_object_or_404(Class, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)
    students = StudentDb.objects.filter(class_info=class_info)

    if request.method == "POST":
        date = timezone.now().date()
        day = timezone.now().strftime('%A')

        for student in students:
            is_present = request.POST.get(f"student_{student.studentid}") == "on"
            AttendanceSheet.objects.create(
                class_info=class_info,
                subject=subject,
                date=date,
                day=day,
                period_number=period_number,
                student=student,
                is_present=is_present
            )

            # Update summary attendance
            attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)
            attendance.total_hours += 1
            if is_present:
                attendance.total_present += 1
            else:
                attendance.total_absent += 1
            attendance.save()

        messages.success(request, "Attendance recorded successfully!")
        return redirect('factimetable')

    return render(request, 'Faculty/takeattendance.html', {
        'students': students,
        'class_info': class_info,
        'subject': subject,
        'period_number': period_number
    })


def facattendance(request):
    """Fetch attendance records for a selected class taught by the faculty."""
    if request.session.get('user_type') != 'faculty':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    faculty_id = request.session.get('id')
    faculty = get_object_or_404(FacultyDb, facid=faculty_id)

    # Get unique classes the faculty teaches
    timetable_entries = TimeTable.objects.filter(faculty=faculty).select_related('class_info', 'subject')
    classes = {entry.class_info for entry in timetable_entries}

    selected_class_id = request.GET.get('class_id')  # Get selected class from dropdown
    attendance_data = []

    if selected_class_id:
        selected_class = get_object_or_404(Class, id=selected_class_id)
        subjects = {entry.subject for entry in timetable_entries if entry.class_info == selected_class}
        
        for subject in subjects:
            students = Attendance.objects.filter(subject=subject, student__class_info=selected_class)
            for record in students:
                attendance_data.append({
                    "student_name": record.student.fullname,
                    "student_id": record.student.studentid,
                    "class": f"{selected_class.department.code} Sem {selected_class.semester.number} {selected_class.division.name}",
                    "subject": subject.code,
                    "total_hours": record.total_hours,
                    "total_present": record.total_present,
                    "total_absent": record.total_absent,
                    "percentage": f"{(record.total_present / record.total_hours * 100) if record.total_hours > 0 else 0:.2f}%"
                })

    return render(request, "Faculty/facattendance.html", {
        "classes": classes,
        "attendance_data": attendance_data,
        "selected_class_id": int(selected_class_id) if selected_class_id else None
    })
def apply_duty_leave(request):
    if request.method == "POST":
        faculty = FacultyDb.objects.get(facid=request.session['id'])
        leave_periods = request.POST.getlist('leave_periods')
        today = now().date()

        for period_id in leave_periods:
            period = TimeTable.objects.get(id=period_id)
            LeavePeriods.objects.create(
                faculty=faculty,
                date=today,
                period=period.period,
                class_info=period.class_info,
                subject=period.subject
            )

        messages.success(request, "Duty leave applied successfully.")
        return redirect('profilefac')

def substitute_period(request):
    if request.method == "POST":
        faculty = FacultyDb.objects.get(facid=request.session['id'])
        leave_period_id = request.POST.get('leave_period')
        substitution_type = request.POST.get('substitution_type')

        leave_period = LeavePeriods.objects.get(id=leave_period_id)

        if substitution_type == "free_period":
            return redirect('takeattendance', period_number=leave_period.period, class_id=leave_period.class_info.id, subject_id=leave_period.subject.id)
        elif substitution_type == "my_subject":
            return redirect('takeattendance', period_number=leave_period.period, class_id=leave_period.class_info.id, subject_id=faculty.subject.id)
def goSubstitute(request):
    leave_periods = LeavePeriods.objects.all()  # Fetch all leave periods
    return render(request, "Faculty/goSubstitute.html", {"leave_periods": leave_periods})
def takeattendance2(request):
    if request.session.get("user_type") != "faculty":
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    if request.method == "POST":
        leave_period_id = request.POST.get("leave_period_id")
        substitute_option = request.POST.get("substitute_option")

        # Fetch Leave Period data
        leave_period = get_object_or_404(LeavePeriods, id=leave_period_id)
        class_info = leave_period.class_info
        date = timezone.now().date()
        day = timezone.now().strftime('%A')

        if substitute_option == "free":
            # Use the class and subject from the faculty on leave
            subject = leave_period.subject
            faculty = leave_period.faculty  # Faculty who is on leave

        elif substitute_option == "my_period":
            # Fetch faculty from session
            faculty_id = request.session.get("id")
            faculty = get_object_or_404(FacultyDb, facid=faculty_id)

            # ✅ Correct query: Fetch subject for the faculty in the session
            faculty_subjects = FacultySubject.objects.filter(faculty=faculty, subject__class_info=class_info)
            
            if faculty_subjects.exists():
                subject = faculty_subjects.first().subject  # Select the first valid subject
            else:
                messages.error(request, "No subject assigned to you for this class.")
                return redirect("goSubstitute")

        else:
            messages.error(request, "Invalid selection.")
            return redirect("goSubstitute")

        # Fetch students in the class
        students = StudentDb.objects.filter(class_info=class_info)

        # ✅ Instead of redirecting, render takeattendance2.html
        return render(request, "Faculty/takeattendance2.html", {
            "students": students,
            "class_info": class_info,
            "subject": subject,
            "period_number": leave_period.period,
            "date": date,
            "day": day
        })

    return redirect("goSubstitute")
def submitAttendance(request):
    if request.method == "POST":
        leave_period_id = request.POST.get("leave_period_id")
        period_number = request.POST.get("period_number")
        class_id = request.POST.get("class_id")
        subject_id = request.POST.get("subject_id")

        class_info = get_object_or_404(Class, id=class_id)
        subject = get_object_or_404(Subject, id=subject_id)
        students = StudentDb.objects.filter(class_info=class_info)

        date = timezone.now().date()
        day = timezone.now().strftime('%A')

        for student in students:
            is_present = request.POST.get(f"student_{student.studentid}") == "on"
            
            # Save attendance sheet entry
            AttendanceSheet.objects.create(
                class_info=class_info,
                subject=subject,
                date=date,
                day=day,
                period_number=period_number,
                student=student,
                is_present=is_present
            )

            # Update summary attendance
            attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)
            attendance.total_hours += 1
            if is_present:
                attendance.total_present += 1
            else:
                attendance.total_absent += 1
            attendance.save()

        messages.success(request, "Attendance submitted successfully!")
        return redirect("factimetable")  # Redirect to Faculty Timetable

    else:
        messages.error(request, "Invalid request.")
        return redirect("factimetable")



#---------------------------------------------------------------------------------------#
######################################## FACULTY VIEWS COMPLETE ######################################################
######################################## STUDENT VIEWS START ######################################################
def profilestu(request):
    """Student Profile View"""
    if request.session.get('user_type') == 'student':
        student_id = request.session.get('id')
        try:
            student = StudentDb.objects.get(studentid=student_id)
            return render(request, 'Student/profilestu.html', {
                'fullname': student.fullname,
                'studentid': student.studentid,
                'department': student.class_info.department.name.upper() if student.class_info.department else "N/A",
                'semester': student.class_info.semester.number if student.class_info.semester else "N/A",
                'division': student.class_info.division.name if student.class_info.division else "N/A"
            })
        except StudentDb.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')
#---------------------------------------------------------------------------------------#
def stutimetable(request):
    """Fetch and display the timetable for the logged-in student's class in correct order"""
    if request.session.get('user_type') == 'student':
        student_id = request.session.get('id')
        try:
            student = StudentDb.objects.get(studentid=student_id)
            class_info = student.class_info  # Get the class the student belongs to
            timetable = TimeTable.objects.filter(class_info=class_info).order_by('day', 'period')

            # Define correct order for weekdays
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            timetable_data = {day: [] for day in day_order}  # Initialize empty lists in correct order

            for entry in timetable:
                # Ensure Friday has only 6 periods
                if entry.day == "Friday" and len(timetable_data[entry.day]) >= 6:
                    continue
                
                timetable_data[entry.day].append({
                    'subject_code': entry.subject.code,
                    'subject_name': entry.subject.name,
                    'faculty': entry.faculty.fullname
                })

            return render(request, 'Student/stutimetable.html', {
                'timetable_data': timetable_data
            })
        except StudentDb.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('login')
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('login')


#---------------------------------------------------------------------------------------#
def stuattendance(request):
    if request.session.get('user_type') != 'student':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    student_id = request.session.get('id')
    student = StudentDb.objects.get(studentid=student_id)
    
    # Get subjects the student is enrolled in
    subjects = Subject.objects.filter(class_info=student.class_info)

    attendance_data = []
    for subject in subjects:
        # Count total classes conducted
        total_hours = Attendance.objects.filter(subject=subject).count()
        attendance = Attendance.objects.filter(student=student, subject=subject).first()

        attendance_data.append({
            "subject_name": subject.name,
            "subject_code": subject.code,
            "total_hours": total_hours,
            "total_present": attendance.total_present if attendance else 0,
            "total_absent": attendance.total_absent if attendance else 0,
            "subject_id": subject.id
        })

    return render(request, "Student/stuattendance.html", {"attendance_data": attendance_data})

from django.http import JsonResponse

def get_class_attendance(request, subject_id):
    subject = Subject.objects.get(id=subject_id)
    attendance_records = AttendanceSheet.objects.filter(subject=subject)

    data = [
        {"student_name": record.student.fullname, "is_present": record.is_present}
        for record in attendance_records
    ]

    return JsonResponse(data, safe=False)

######################################## STUDENT VIEWS COMPLETE ######################################################
