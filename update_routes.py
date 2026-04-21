import codecs
import re

def update_backend():
    with codecs.open('backend/app.py', 'r', 'utf-8') as f:
        content = f.read()

    # 1. Provide the dummy /admin-login route requested by user
    admin_login_route = """@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login_route():
    return jsonify({"status": "success", "message": "Admin login endpoint active"}), 200

"""
    if "def admin_login_route" not in content:
        content = content.replace("@app.route('/admin', methods=['POST'])", admin_login_route + "@app.route('/admin', methods=['POST'])")

    # 2. Update login to exactly match requirements
    login_str = """        if email == "harsha@srmap.edu.in" and password == "harsha@23":
            session["user_id"] = 1
            session["role"] = "admin"
            return jsonify({"role": "admin"})"""
            
    content = re.sub(
        r'\s+if email == "harsha@srmap.edu.in" and password == "harsha@23":[\s\S]+?\}\), 200',
        login_str,
        content,
        count=1
    )

    # 3. Protect ONLY /admin and nothing else
    admin_route_replacement = """@app.route('/admin', methods=['POST'])
def admin_route():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"status": "success", "message": "Welcome to Admin Dashboard"}), 200"""
    
    content = re.sub(
        r'@app.route\(\'/admin\', methods=\[\'POST\'\]\)\ndef admin_route\(\):[\s\S]+?return jsonify\(\{"status": "success", "message": "Welcome to Admin Dashboard"\}\), 200',
        admin_route_replacement,
        content
    )

    # 4. Remove 'user_id' not in session restrictions for all other routes
    content = content.replace("    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\n", "")
    content = content.replace("    if 'user_id' not in session:\n        return jsonify({'error': 'Unauthorized', 'redirect': '/login'}), 401\r\n", "")

    # For claims and update-claim, remove admin restriction if present
    content = content.replace("    if session.get('role') != 'admin':\n        return jsonify({'error': 'Unauthorized access'}), 403\n", "")
    content = content.replace("    if session.get('role') != 'admin':\n        return jsonify({'error': 'Unauthorized access'}), 403\r\n", "")

    with codecs.open('backend/app.py', 'w', 'utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_backend()
