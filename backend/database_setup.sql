CREATE DATABASE IF NOT EXISTS lost_found_db;
USE lost_found_db;

CREATE TABLE USERS (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password VARCHAR(100) NOT NULL,
    CONSTRAINT chk_email_format CHECK (email LIKE '%@%.%'),
    CONSTRAINT chk_password_length CHECK (CHAR_LENGTH(password) >= 8)
);

CREATE TABLE CATEGORIES (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50)
);

CREATE TABLE LOCATIONS (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(50)
);

CREATE TABLE ITEMS (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(50),
    description VARCHAR(100),
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES CATEGORIES(category_id) ON DELETE SET NULL
);

CREATE TABLE LOST_REPORTS (
    lost_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    item_id INT,
    location_id INT,
    lost_date DATE,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES ITEMS(item_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES LOCATIONS(location_id) ON DELETE SET NULL
);

CREATE TABLE FOUND_REPORTS (
    found_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    item_id INT,
    location_id INT,
    found_date DATE,
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES ITEMS(item_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES LOCATIONS(location_id) ON DELETE SET NULL
);

CREATE TABLE CLAIMS (
    claim_id INT AUTO_INCREMENT PRIMARY KEY,
    lost_id INT,
    found_id INT,
    claim_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (lost_id) REFERENCES LOST_REPORTS(lost_id) ON DELETE CASCADE,
    FOREIGN KEY (found_id) REFERENCES FOUND_REPORTS(found_id) ON DELETE CASCADE
);

-- =========================================
-- INSERT DUMMY DATA
-- =========================================

-- 1. Insert Users
INSERT INTO USERS (name, email, phone, password) VALUES
('Harsha', 'harsha@gmail.com', '9100000001', '123456789'),
('Vardhan', 'vardhan@gmail.com', '9100000002', '123456789'),
('Reddy', 'reddy@gmail.com', '9100000003', '123456789'),
('Harshi', 'harshi@gmail.com', '9100000004', '123456789');

-- 2. Insert Categories
INSERT INTO CATEGORIES (category_name) VALUES
('Electronics'),
('Accessories'),
('Bags');

-- 3. Insert Locations
INSERT INTO LOCATIONS (location_name) VALUES
('Library'),
('Cafeteria'),
('Bus Stop');

-- 4. Insert Items
-- Note: category_id 1=Electronics, 2=Accessories, 3=Bags
INSERT INTO ITEMS (item_name, description, category_id) VALUES
('Mobile', 'Samsung Phone', 1),
('Wallet', 'Leather Wallet', 2),
('Backpack', 'Blue Bag', 3);

-- 5. Insert Lost Reports
-- Harsha (1) lost Mobile (1) in Library (1)
-- Vardhan (2) lost Wallet (2) in Cafeteria (2)
-- Reddy (3) lost Backpack (3) in Bus Stop (3)
INSERT INTO LOST_REPORTS (user_id, item_id, location_id, lost_date) VALUES
(1, 1, 1, '2026-04-10'),
(2, 2, 2, '2026-04-11'),
(3, 3, 3, '2026-04-12');

-- 6. Insert Found Reports
-- Harshi (4) found Mobile (1) in Library (1)
-- Harsha (1) found Wallet (2) in Cafeteria (2)
-- Vardhan (2) found Backpack (3) in Bus Stop (3)
INSERT INTO FOUND_REPORTS (user_id, item_id, location_id, found_date) VALUES
(4, 1, 1, '2026-04-11'),
(1, 2, 2, '2026-04-12'),
(2, 3, 3, '2026-04-13');

-- 7. Insert Claims
-- Match lost Mobile with found Mobile -> Approved
-- Match lost Wallet with found Wallet -> Pending
-- Match lost Backpack with found Backpack -> Rejected
INSERT INTO CLAIMS (lost_id, found_id, claim_date, status) VALUES
(1, 1, '2026-04-12', 'Approved'),
(2, 2, '2026-04-13', 'Pending'),
(3, 3, '2026-04-14', 'Rejected');
