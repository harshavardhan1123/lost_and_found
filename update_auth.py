import codecs

def update_backend():
    with codecs.open('backend/app.py', 'r', 'utf-8') as f:
        content = f.read()

    # 1. Imports and Config
    content = content.replace(
        "from flask import Flask, request, jsonify\nfrom flask_cors import CORS",
        "from flask import Flask, request, jsonify, session\nfrom flask_cors import CORS"
    )
    content = content.replace(
        "app = Flask(__name__)\nCORS(app)",
        "app = Flask(__name__)\napp.secret_key = 'harsha_secure_session_key'\nCORS(app, supports_credentials=True)"
    )

    # 2. Login route session mapping
    login_str = """        if email == "harsha@srmap.edu.in" and password == "harsha@23":
            session['user_id'] = 0
            session['role'] = 'admin'
            session['name'] = 'Admin'
            session['email'] = email
            return jsonify({
                "status": "success",
                "message": "Admin login successful",
                "role": "admin",
                "user": {"user_id": 0, "name": "Admin", "email": email}
            }), 200

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
            }), 200"""
    
    import re
    content = re.sub(
        r'\s+if email == "harsha@srmap.edu.in" and password == "harsha@23":[\s\S]+?\}\), 200',
        login_str,
        content,
        count=1
    )

    # 3. Add Logout & Check Session, modify admin_route
    admin_str = """@app.route('/logout', methods=['GET'])
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
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401
    if session.get('role') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    return jsonify({"status": "success", "message": "Welcome to Admin Dashboard"}), 200"""

    content = re.sub(
        r'@app.route\(\'/admin\', methods=\[\'POST\'\]\)[\s\S]+?\}\), 500',
        admin_str,
        content
    )

    # 4. Protect data endpoints
    endpoints_to_protect = [
        "@app.route('/items', methods=['GET'])\ndef get_items():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    try:",
        "@app.route('/claims', methods=['GET'])\ndef get_claims():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    if session.get('role') != 'admin':\n        return jsonify({'error': 'Unauthorized access'}), 403\n    try:",
        "@app.route('/update-claim', methods=['POST'])\ndef update_claim():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    if session.get('role') != 'admin':\n        return jsonify({'error': 'Unauthorized access'}), 403\n    try:",
        "@app.route('/report-lost', methods=['POST'])\ndef report_lost():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    try:",
        "@app.route('/report-found', methods=['POST'])\ndef report_found():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    try:",
        "@app.route('/claim', methods=['POST'])\ndef make_claim():\n    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n    try:"
    ]

    content = content.replace("@app.route('/items', methods=['GET'])\ndef get_items():\n    try:", endpoints_to_protect[0])
    content = content.replace("@app.route('/claims', methods=['GET'])\ndef get_claims():\n    try:", endpoints_to_protect[1])
    content = content.replace("@app.route('/update-claim', methods=['POST'])\ndef update_claim():\n    try:", endpoints_to_protect[2])
    content = content.replace("@app.route('/report-lost', methods=['POST'])\ndef report_lost():\n    try:", endpoints_to_protect[3])
    content = content.replace("@app.route('/report-found', methods=['POST'])\ndef report_found():\n    try:", endpoints_to_protect[4])
    content = content.replace("@app.route('/claim', methods=['POST'])\ndef make_claim():\n    try:", endpoints_to_protect[5])

    with codecs.open('backend/app.py', 'w', 'utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_backend()
