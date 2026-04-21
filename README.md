# Lost and Found Management System

A full-stack web application designed to manage lost and found items within a university campus.
This system provides a structured workflow to report, track, and recover lost items efficiently.

---

## 🚀 Features

* User authentication (Admin & User roles)
* Report Lost Items
* Report Found Items
* View all lost and found items
* Smart matching between lost and found entries
* Claim request system
* Admin approval/rejection workflow
* Email notification on claim approval
* Session-based authentication (persistent login)

---

## 🧠 System Workflow

1. User reports a lost item
2. Another user reports a found item
3. System displays matching items
4. User requests a claim
5. Admin verifies and approves/rejects
6. User receives notification and collects the item

---

## 🛠 Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Flask (Python)
* **Database:** MySQL

---

## 🗄 Database Design

Main tables:

* USERS
* ITEMS
* CATEGORIES
* LOCATIONS
* LOST_REPORTS
* FOUND_REPORTS
* CLAIMS

Relational design with foreign keys ensures data integrity.

---

## ⚙️ Installation & Setup

1. Clone the repository:

```
git clone <your-repo-link>
cd lost-and-found
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Setup MySQL database:

* Create database: `lost_found_db`
* Run SQL script (`data_setup.sql`)

4. Configure database in `app.py`:

```
host="localhost"
user="root"
password="your_password"
database="lost_found_db"
```

5. Run the application:

```
python app.py
```

6. Open in browser:

```
http://127.0.0.1:5000
```

---

## 🔐 Admin Access

* Email: [harsha@srmap.edu.in](mailto:harsha@srmap.edu.in)
* Password: harsha@23

---

## ⚠️ Validation

* Email must follow proper format
* Password must be at least 8 characters
* Duplicate users are restricted

---

## 📌 Future Improvements

* Image upload for items
* OTP-based verification
* Advanced matching using AI
* Mobile application version

---

## 📄 Conclusion

This project focuses on solving a real-world problem by implementing a complete lost-and-found workflow instead of just displaying data.

---

## 🤝 Contributions

Open to suggestions and improvements.
# lost_and_found
