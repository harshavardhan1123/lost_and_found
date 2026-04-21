import codecs

def update_backend():
    with codecs.open('backend/app.py', 'r', 'utf-8') as f:
        content = f.read()

    # 1. Add email imports and helper function
    if "import smtplib" not in content:
        import_str = """import smtplib\nfrom email.mime.text import MIMEText\nfrom email.mime.multipart import MIMEMultipart\n\ndef send_email(to_email, subject, message):\n    try:\n        sender = "harsha_admin@gmail.com" # Mock sender\n        password = "your_app_password"\n        msg = MIMEMultipart()\n        msg['From'] = sender\n        msg['To'] = to_email\n        msg['Subject'] = subject\n        msg.attach(MIMEText(message, 'plain'))\n        \n        # Uncomment below in production when real credentials are provided\n        # server = smtplib.SMTP('smtp.gmail.com', 587)\n        # server.starttls()\n        # server.login(sender, password)\n        # server.send_message(msg)\n        # server.quit()\n        print(f"=== MOCK EMAIL SENT TO {to_email} ===\\nSubject: {subject}\\n{message}\\n=============================")\n        return True\n    except Exception as e:\n        print("Email sending failed:", e)\n        return False\n\n"""
        content = content.replace("def get_db_connection():", import_str + "def get_db_connection():")

    # 2. Update POST /claim to insert user_id and prevent duplicates
    claim_str = """@app.route('/claim', methods=['POST'])
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
        return jsonify({'status': 'error', 'error': str(e)}), 500"""

    import re
    content = re.sub(
        r'@app.route\(\'/claim\', methods=\[\'POST\'\]\)\ndef make_claim\(\):[\s\S]+?return jsonify\(\{.*?status.*?error.*?str\(e\).*?\}\), 500',
        claim_str,
        content
    )

    # 3. Update /items to exclude approved Claims
    lost_query = """        lost_query = \"\"\"
            SELECT 
                lr.lost_id AS report_id,
                DATE_FORMAT(lr.lost_date, '%b %d, %Y') AS report_date,
                i.item_name,
                i.description,
                c.category_name,
                l.location_name,
                u.name AS reported_by,
                'Lost' AS status
            FROM LOST_REPORTS lr
            JOIN ITEMS i ON lr.item_id = i.item_id
            JOIN CATEGORIES c ON i.category_id = c.category_id
            JOIN LOCATIONS l ON lr.location_id = l.location_id
            JOIN USERS u ON lr.user_id = u.user_id
            WHERE lr.lost_id NOT IN (SELECT lost_id FROM CLAIMS WHERE status = 'Approved' and lost_id IS NOT NULL);
        \"\"\""""

    found_query = """        found_query = \"\"\"
            SELECT 
                fr.found_id AS report_id,
                DATE_FORMAT(fr.found_date, '%b %d, %Y') AS report_date,
                i.item_name,
                i.description,
                c.category_name,
                l.location_name,
                u.name AS reported_by,
                'Found' AS status
            FROM FOUND_REPORTS fr
            JOIN ITEMS i ON fr.item_id = i.item_id
            JOIN CATEGORIES c ON i.category_id = c.category_id
            JOIN LOCATIONS l ON fr.location_id = l.location_id
            JOIN USERS u ON fr.user_id = u.user_id
            WHERE fr.found_id NOT IN (SELECT found_id FROM CLAIMS WHERE status = 'Approved' and found_id IS NOT NULL);
        \"\"\""""

    content = re.sub(r'\s+lost_query = """[\s\S]+?JOIN USERS u ON lr\.user_id = u\.user_id;\n\s+"""', '\n' + lost_query, content)
    content = re.sub(r'\s+found_query = """[\s\S]+?JOIN USERS u ON fr\.user_id = u\.user_id;\n\s+"""', '\n' + found_query, content)

    # 4. Update /update-claim to send email on approval
    update_claim_str = """@app.route('/update-claim', methods=['POST'])
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
            email_query = \"\"\"
                SELECT u.email, u.name, i.item_name, l.location_name
                FROM USERS u
                JOIN LOST_REPORTS lr ON u.user_id = lr.user_id
                JOIN ITEMS i ON lr.item_id = i.item_id
                JOIN LOCATIONS l ON lr.location_id = l.location_id
                WHERE lr.lost_id = %s
            \"\"\"
            if lost_id:
                cursor.execute(email_query, (lost_id,))
            else:
                email_query = \"\"\"
                    SELECT u.email, u.name, i.item_name, l.location_name
                    FROM USERS u
                    JOIN FOUND_REPORTS fr ON u.user_id = fr.user_id
                    JOIN ITEMS i ON fr.item_id = i.item_id
                    JOIN LOCATIONS l ON fr.location_id = l.location_id
                    WHERE fr.found_id = %s
                \"\"\"
                cursor.execute(email_query, (found_id,))
                
            email_data = cursor.fetchone()
            
            if email_data:
                to_email = email_data['email']
                subject = "Lost Item Claim Approved"
                message = f"Hello {email_data['name']},\\n\\nYour claim for '{email_data['item_name']}' has been officially approved!\\n\\nCollection Location: {email_data['location_name']}\\n\\nPlease bring a valid ID and reference your ticket block to securely collect your item.\\n\\nRegards,\\nL&F Campus Admin"
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
        return jsonify({'status': 'error', 'error': str(e)}), 500"""

    content = re.sub(
        r'@app.route\(\'/update-claim\', methods=\[\'POST\'\]\)\ndef update_claim\(\):[\s\S]+?return jsonify\(\{.*?status.*?error.*?str\(e\).*?\}\), 500',
        update_claim_str,
        content
    )

    with codecs.open('backend/app.py', 'w', 'utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_backend()
