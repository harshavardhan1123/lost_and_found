import mysql.connector

def alter_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="harsha@23",
        database="lost_found_db"
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE CLAIMS ADD COLUMN user_id INT")
        cursor.execute("ALTER TABLE CLAIMS ADD FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE")
        conn.commit()
        print("Schema altered successfully: user_id added to CLAIMS.")
    except Exception as e:
        print("Schema alteration error (may already exist):", e)
    finally:
        conn.close()

if __name__ == '__main__':
    alter_db()
