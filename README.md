
# OSAS – Online Student Attendance System


OSAS is a Django-based web application developed to make student attendance tracking efficient and user-friendly. It supports real-time updates, administrative controls, and bulk data management—ideal for academic institutions.

---

🌟 Features

👨‍🏫 For Faculties:

* Mark attendance and print reports based on the classes they teach.
* Manage duty leave and substitution options.
* View personal timetables.
* Access the Django Admin Panel to make object-level changes.
* Use a custom secondary admin login panel to upload data (students, subjects, faculties, timetables) via Excel sheets.

🎓 For Students:

* View and print their attendance in real time.

---

🔧 Tech Stack

* Backend: Django (Python)
* Database: SQLite (default Django DB)
* Frontend: HTML, CSS, JavaScript

---

🚀 Getting Started

1. Clone the Repository

   ```bash
   git clone https://github.com/ArjunDas2003/osas.git
   cd osas
   ```

2. (Optional) Create a Virtual Environment

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Apply Migrations

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create Superuser

   ```bash
   python manage.py createsuperuser
   ```

6. Run the Development Server

   ```bash
   python manage.py runserver
   ```

7. Visit the App:

   * User Interface: http://127.0.0.1:8000/
   * Django Admin Panel: http://127.0.0.1:8000/admin/

---

 📥 Contributing

Pull requests are welcome! Feel free to fork the repo and submit enhancements or bug fixes. Open an issue for major changes before starting work.



