import os
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error as MySQLError
import datetime

# Initialize Flask to serve static files from the root directory (one level up from backend)
app = Flask(__name__, static_folder='../', static_url_path='')
app.secret_key = 'harsha_secure_session_key'
CORS(app, supports_credentials=True)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, message):
    try:
        sender = "harsha_admin@gmail.com" # Mock sender
        password = "your_app_password"
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        
        # Uncomment below in production when real credentials are provided
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(sender, password)
        # server.send_message(msg)
        # server.quit()
        print(f"=== MOCK EMAIL SENT TO {to_email} ===\nSubject: {subject}\n{message}\n=============================")
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="harsha@23",
        database="lost_found_db"
    )

# ==========================================
# 0. ROOT ROUTE - Serves the Frontend
# ==========================================
@app.route('/', methods=['GET'])
def index():
    return send_from_directory('../', 'index.html')

# ==========================================
# 1. USER AUTHENTICATION
# ==========================================
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON Payload'}), 400
            
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone', '')

        if not all([name, email, password]):
            return jsonify({'status': 'error', 'error': 'Name, email, and password are required'}), 400

        # Email format validation
        if "@" not in email or "." not in email:
            return jsonify({'status': 'error', 'error': 'Invalid email format. Must contain "@" and "."'}), 400

        # Password length validation
        if len(password) < 8:
            return jsonify({'status': 'error', 'error': 'Password must be at least 8 characters long'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("INSERT INTO USERS (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                       (name, email, phone, password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({'status': 'success', 'message': 'User created successfully', 'user_id': user_id}), 201
    except mysql.connector.IntegrityError:
        if 'conn' in locals() and conn.is_connected(): conn.close()
        return jsonify({'status': 'error', 'error': 'Email address already exists in the system'}), 409
    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.close()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON Payload'}), 400
            
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({'status': 'error', 'error': 'Email and password are required'}), 400

        # Normalize email for comparison
        email_normalized = email.strip().lower()
        password_normalized = password.strip()

        print(f"DEBUG: Login attempt - Email: '{email_normalized}', Password: '{password_normalized}'")

        if email_normalized == "harsha@srmap.edu.in" and password_normalized == "harsha@23":
            session["user_id"] = 1
            session["role"] = "admin"
            print("DEBUG: Admin login successful (hardcoded)")
            return jsonify({
                "status": "success",
                "role": "admin",
                "user": {"user_id": 1, "name": "Admin", "email": email_normalized}
            })

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM USERS WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = 'user'
            session['name'] = user['name']
            session['email'] = user['email']
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'role': 'user',
                'user': {
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email']
                }
            }), 200


        else:
            return jsonify({'status': 'error', 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200

@app.route('/check-session', methods=['GET'])
def check_session():
    if "user_id" in session:
        return jsonify({
            'status': 'success',
            'role': session.get('role'),
            'user': {
                'user_id': session['user_id'],
                'name': session.get('name'),
                'email': session.get('email')
            }
        }), 200
    return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401

@app.route('/admin', methods=['POST'])
def admin_route():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"status": "success", "message": "Welcome to Admin Dashboard"}), 200


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login_route():
    return jsonify({"status": "success", "message": "Admin login endpoint active"}), 200


# ==========================================
# Helper func: Create ITEM record
# ==========================================
def create_item(cursor, name, description, category_id):
    cursor.execute(
        "INSERT INTO ITEMS (item_name, description, category_id) VALUES (%s, %s, %s)",
        (name, description, category_id)
    )
    return cursor.lastrowid


# ==========================================
# 2. LOST ITEMS
# ==========================================
@app.route('/report-lost', methods=['POST'])
def report_lost():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        user_id = data.get('user_id')
        item_name = data.get('item_name')
        description = data.get('description', '')
        category_id = data.get('category_id')
        location_id = data.get('location_id')
        lost_date = data.get('lost_date', datetime.date.today().isoformat())

        if not all([user_id, item_name, category_id, location_id]):
            return jsonify({'status': 'error', 'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        item_id = create_item(cursor, item_name, description, category_id)
        
        cursor.execute(
            "INSERT INTO LOST_REPORTS (user_id, item_id, location_id, lost_date) VALUES (%s, %s, %s, %s)",
            (user_id, item_id, location_id, lost_date)
        )
        report_id = cursor.lastrowid

        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Lost item reported successfully', 
            'lost_id': report_id
        }), 201
    except MySQLError as e:
        print("DEBUG ERROR report_lost (MySQL):", str(e))
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': 'Database error: ' + str(e)}), 400
    except Exception as e:
        print("DEBUG ERROR report_lost:", str(e))
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==========================================
# 3. FOUND ITEMS
# ==========================================
@app.route('/report-found', methods=['POST'])
def report_found():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        user_id = data.get('user_id')
        item_name = data.get('item_name')
        description = data.get('description', '')
        category_id = data.get('category_id')
        location_id = data.get('location_id')
        found_date = data.get('found_date', datetime.date.today().isoformat())

        if not all([user_id, item_name, category_id, location_id]):
            return jsonify({'status': 'error', 'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        item_id = create_item(cursor, item_name, description, category_id)
        
        cursor.execute(
            "INSERT INTO FOUND_REPORTS (user_id, item_id, location_id, found_date) VALUES (%s, %s, %s, %s)",
            (user_id, item_id, location_id, found_date)
        )
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Found item reported successfully', 'found_id': report_id}), 201
    except MySQLError as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': 'Database error: ' + str(e)}), 400
    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==========================================
# 4. FETCH ITEMS
# ==========================================
@app.route('/items', methods=['GET'])
def get_items():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        lost_query = """
            SELECT 
                lr.lost_id AS report_id,
                DATE_FORMAT(lr.lost_date, '%b %d, %Y') AS report_date,
                i.item_name,
                i.description,
                c.category_name,
                l.location_name,
                u.name AS reported_by,
                u.email AS reported_email,
                'Lost' AS status
            FROM LOST_REPORTS lr
            JOIN ITEMS i ON lr.item_id = i.item_id
            JOIN CATEGORIES c ON i.category_id = c.category_id
            JOIN LOCATIONS l ON lr.location_id = l.location_id
            JOIN USERS u ON lr.user_id = u.user_id
            WHERE lr.lost_id NOT IN (SELECT lost_id FROM CLAIMS WHERE status = 'Approved' and lost_id IS NOT NULL);
        """
        found_query = """
            SELECT 
                fr.found_id AS report_id,
                DATE_FORMAT(fr.found_date, '%b %d, %Y') AS report_date,
                i.item_name,
                i.description,
                c.category_name,
                l.location_name,
                u.name AS reported_by,
                u.email AS reported_email,
                'Found' AS status
            FROM FOUND_REPORTS fr
            JOIN ITEMS i ON fr.item_id = i.item_id
            JOIN CATEGORIES c ON i.category_id = c.category_id
            JOIN LOCATIONS l ON fr.location_id = l.location_id
            JOIN USERS u ON fr.user_id = u.user_id
            WHERE fr.found_id NOT IN (SELECT found_id FROM CLAIMS WHERE status = 'Approved' and found_id IS NOT NULL);
        """

        cursor.execute(lost_query)
        lost_items = cursor.fetchall()
        
        cursor.execute(found_query)
        found_items = cursor.fetchall()
        
        conn.close()
        
        print("=== DEBUG LOG FOR /items ===")
        print("Lost items count:", len(lost_items))
        print("Lost items:", lost_items)
        print("Found items count:", len(found_items))
        print("Found items:", found_items)
        print("============================")
        
        return jsonify({
            'lost': lost_items,
            'found': found_items
        }), 200
    except Exception as e:
        print("DEBUG LOG /items ERROR:", str(e))
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==========================================
# 5. CLAIM SYSTEM
# ==========================================
@app.route('/claim', methods=['POST'])
def make_claim():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        user_id = data.get('user_id')
        lost_id = data.get('lost_id')
        found_id = data.get('found_id')
        
        if not user_id or (not lost_id and not found_id):
            return jsonify({'status': 'error', 'error': 'user_id, and either lost_id/found_id are required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if lost_id:
            cursor.execute("SELECT * FROM LOST_REPORTS WHERE lost_id = %s", (lost_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Lost item does not exist'}), 404
            cursor.execute("SELECT * FROM CLAIMS WHERE lost_id = %s AND user_id = %s AND status != 'Rejected'", (lost_id, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'You already have an active claim for this item'}), 400
        
        if found_id:
            cursor.execute("SELECT * FROM FOUND_REPORTS WHERE found_id = %s", (found_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Found item does not exist'}), 404
            cursor.execute("SELECT * FROM CLAIMS WHERE found_id = %s AND user_id = %s AND status != 'Rejected'", (found_id, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'You already have an active claim for this item'}), 400

        claim_date = datetime.date.today().isoformat()
        cursor.execute(
            "INSERT INTO CLAIMS (user_id, lost_id, found_id, claim_date, status) VALUES (%s, %s, %s, %s, 'Pending')",
            (user_id, lost_id, found_id, claim_date)
        )
        conn.commit()
        claim_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Claim registered as Pending', 'claim_id': claim_id}), 201
    except MySQLError as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': 'Database error: ' + str(e)}), 400
    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/claims', methods=['GET'])
def get_claims():
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                CL.claim_id,
                CL.claim_date,
                CL.status as claim_status,
                COALESCE(U_lost.name, U_found.name) as claimant_name,
                COALESCE(U_lost.email, U_found.email) as claimant_email,
                COALESCE(I_lost.item_name, I_found.item_name) as item_name,
                CASE WHEN CL.lost_id IS NOT NULL THEN 'Lost Item Claim' ELSE 'Found Item Claim' END as claim_type
            FROM CLAIMS CL
            LEFT JOIN LOST_REPORTS LR ON CL.lost_id = LR.lost_id
            LEFT JOIN FOUND_REPORTS FR ON CL.found_id = FR.found_id
            LEFT JOIN USERS U_lost ON LR.user_id = U_lost.user_id
            LEFT JOIN USERS U_found ON FR.user_id = U_found.user_id
            LEFT JOIN ITEMS I_lost ON LR.item_id = I_lost.item_id
            LEFT JOIN ITEMS I_found ON FR.item_id = I_found.item_id
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        claims_list = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'claims': claims_list}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/update-claim', methods=['POST'])
def update_claim():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
            
        claim_id = data.get('claim_id')
        status = data.get('status')
        
        if not claim_id or status not in ['Approved', 'Rejected', 'Pending']:
            return jsonify({'status': 'error', 'error': 'Valid claim_id and claim status are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify claim exists and fetch associated IDs natively
        cursor.execute("SELECT * FROM CLAIMS WHERE claim_id = %s", (claim_id,))
        claim_data = cursor.fetchone()
        if not claim_data:
            conn.close()
            return jsonify({'status': 'error', 'error': 'Claim not found'}), 404
            
        cursor.execute("UPDATE CLAIMS SET status = %s WHERE claim_id = %s", (status, claim_id))
        
        email_sent = False
        if status == 'Approved':
            lost_id = claim_data.get('lost_id')
            found_id = claim_data.get('found_id')
            
            # As explicitly instructed: JOIN to fetch user email based on lost_id (or found_id contextually)
            email_query = """
                SELECT u.email, u.name, i.item_name, l.location_name
                FROM USERS u
                JOIN LOST_REPORTS lr ON u.user_id = lr.user_id
                JOIN ITEMS i ON lr.item_id = i.item_id
                JOIN LOCATIONS l ON lr.location_id = l.location_id
                WHERE lr.lost_id = %s
            """
            if lost_id:
                cursor.execute(email_query, (lost_id,))
            else:
                email_query = """
                    SELECT u.email, u.name, i.item_name, l.location_name
                    FROM USERS u
                    JOIN FOUND_REPORTS fr ON u.user_id = fr.user_id
                    JOIN ITEMS i ON fr.item_id = i.item_id
                    JOIN LOCATIONS l ON fr.location_id = l.location_id
                    WHERE fr.found_id = %s
                """
                cursor.execute(email_query, (found_id,))
                
            email_data = cursor.fetchone()
            
            if email_data:
                to_email = email_data['email']
                subject = "Lost Item Claim Approved"
                message = f"""Hello {email_data['name']},

Your claim for '{email_data['item_name']}' has been officially approved!

Collection Location: {email_data['location_name']}

Please bring a valid ID and reference your ticket block to securely collect your item.

Regards,
L&F Campus Admin"""
                send_email(to_email, subject, message)
                email_sent = True

        conn.commit()
        conn.close()
        
        payload = {'status': 'success', 'message': f'Claim #{claim_id} updated.'}
        if status == 'Approved':
             payload['email_dispatched'] = email_sent
             
        return jsonify(payload), 200
    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback(); conn.close()
        return jsonify({'status': 'error', 'error': str(e)}), 500



# ==========================================
# Fetch reference logic for dropdowns
# ==========================================
@app.route('/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM CATEGORIES")
        cats = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'categories': cats}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM LOCATIONS")
        locs = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'locations': locs}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# Custom Error Handling for invalid route access
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "The requested API route does not exist."}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": "error", "message": "Method not allowed for this route."}), 405

# Run Application
if __name__ == '__main__':
    app.run(debug=True, port=5001)
