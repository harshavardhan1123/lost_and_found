import mysql.connector

def upgrade_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="harsha@23",
            database="lost_found_db"
        )
        cursor = conn.cursor()
        
        print("Starting database upgrade...")
        
        # 1. Update existing users with short passwords to comply with new constraint
        print("Updating existing short passwords to 'password123'...")
        cursor.execute("UPDATE USERS SET password = 'password123' WHERE CHAR_LENGTH(password) < 8")
        
        # 2. Add constraints
        print("Adding email format constraint...")
        try:
            cursor.execute("ALTER TABLE USERS MODIFY email VARCHAR(100) NOT NULL")
            cursor.execute("ALTER TABLE USERS ADD CONSTRAINT chk_email_format CHECK (email LIKE '%@%.%')")
        except mysql.connector.Error as err:
            print(f"Note (Email Constraint): {err}")
            
        print("Adding password length constraint...")
        try:
            cursor.execute("ALTER TABLE USERS MODIFY password VARCHAR(100) NOT NULL")
            cursor.execute("ALTER TABLE USERS ADD CONSTRAINT chk_password_length CHECK (CHAR_LENGTH(password) >= 8)")
        except mysql.connector.Error as err:
            print(f"Note (Password Constraint): {err}")
            
        conn.commit()
        print("Database upgrade completed successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    upgrade_db()
