import sqlite3
import os

DB_PATH = 'lost_and_found.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 1. Modify existing tables to enforce strict constraints AND new status columns
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS USERS (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS CATEGORIES (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS LOCATIONS (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ITEMS (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Lost',
            FOREIGN KEY (category_id) REFERENCES CATEGORIES(category_id)
        );

        CREATE TABLE IF NOT EXISTS LOST_REPORTS (
            lost_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            lost_date DATE NOT NULL,
            report_status TEXT DEFAULT 'Open' NOT NULL, -- Open / Matched / Claimed
            FOREIGN KEY (user_id) REFERENCES USERS(user_id),
            FOREIGN KEY (item_id) REFERENCES ITEMS(item_id),
            FOREIGN KEY (location_id) REFERENCES LOCATIONS(location_id)
        );

        CREATE TABLE IF NOT EXISTS FOUND_REPORTS (
            found_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            found_date DATE NOT NULL,
            report_status TEXT DEFAULT 'Available' NOT NULL, -- Available / Claimed
            FOREIGN KEY (user_id) REFERENCES USERS(user_id),
            FOREIGN KEY (item_id) REFERENCES ITEMS(item_id),
            FOREIGN KEY (location_id) REFERENCES LOCATIONS(location_id)
        );

        CREATE TABLE IF NOT EXISTS CLAIMS (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_id INTEGER,
            found_id INTEGER,
            user_id INTEGER NOT NULL,
            claim_date DATE NOT NULL,
            status TEXT DEFAULT 'Pending' NOT NULL,
            FOREIGN KEY (lost_id) REFERENCES LOST_REPORTS(lost_id),
            FOREIGN KEY (found_id) REFERENCES FOUND_REPORTS(found_id),
            FOREIGN KEY (user_id) REFERENCES USERS(user_id)
        );
    ''')

    # 2. Alter commands for safe upgrades of existing datasets
    try:
        cursor.execute("ALTER TABLE ITEMS ADD COLUMN status TEXT DEFAULT 'Lost' NOT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE LOST_REPORTS ADD COLUMN report_status TEXT DEFAULT 'Open' NOT NULL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE FOUND_REPORTS ADD COLUMN report_status TEXT DEFAULT 'Available' NOT NULL")
    except sqlite3.OperationalError:
        pass

    # 3. Add robust optimized index strategies
    cursor.executescript('''
        CREATE INDEX IF NOT EXISTS idx_items_category ON ITEMS(category_id);
        CREATE INDEX IF NOT EXISTS idx_lost_location ON LOST_REPORTS(location_id);
        CREATE INDEX IF NOT EXISTS idx_found_location ON FOUND_REPORTS(location_id);
        CREATE INDEX IF NOT EXISTS idx_items_status ON ITEMS(status);
        CREATE INDEX IF NOT EXISTS idx_lost_status ON LOST_REPORTS(report_status);
        CREATE INDEX IF NOT EXISTS idx_found_status ON FOUND_REPORTS(report_status);
    ''')

    # Seed core metadata
    cat_count = cursor.execute("SELECT COUNT(*) FROM CATEGORIES").fetchone()[0]
    if cat_count == 0:
        cursor.executescript('''
            INSERT INTO CATEGORIES (category_name) VALUES 
            ('Electronics'), ('Accessories'), ('Clothing'), ('Books'), ('Other');

            INSERT INTO LOCATIONS (location_name) VALUES 
            ('Science Library'), ('Main Cafeteria'), ('Engineering Building'), ('Campus Gym'), ('Campus Gate 2');
        ''')

    conn.commit()
    conn.close()
    print("Database accurately scaled with claim constraints, indexing, and status architectures.")

if __name__ == '__main__':
    init_db()
