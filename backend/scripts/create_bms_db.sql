-- Create BMS database and application user (run as MySQL root)
CREATE DATABASE IF NOT EXISTS bms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'bms_user'@'localhost' IDENTIFIED BY 'change_me';
CREATE USER IF NOT EXISTS 'bms_user'@'127.0.0.1' IDENTIFIED BY 'change_me';

GRANT ALL PRIVILEGES ON bms_db.* TO 'bms_user'@'localhost';
GRANT ALL PRIVILEGES ON bms_db.* TO 'bms_user'@'127.0.0.1';
FLUSH PRIVILEGES;
