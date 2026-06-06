-- ============================================================
-- payment_db_init.sql
-- Tạo database thứ hai mô phỏng hệ thống thanh toán riêng biệt.
--
-- Mục đích thesis: chứng minh direct MySQL access (Metasploit)
-- cho phép attacker thấy NHIỀU HƠN so với khai thác SQLi qua web.
--
-- Access control:
--   ctf_user  (web app)   → CHỈ có ctf_blog  ← SQLi bị giới hạn ở đây
--   pentestuser (attacker) → ctf_blog + payment_db ← Metasploit mở ra cái này
--   root                  → toàn bộ server
--
-- Script này được mount vào /docker-entrypoint-initdb.d/
-- và chạy tự động khi MySQL container khởi tạo lần đầu.
-- ============================================================

-- ── Tạo payment_db ───────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS payment_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE payment_db;

-- ── Bảng credit_cards ────────────────────────────────────────
-- Dữ liệu nhạy cảm chỉ accessible qua direct MySQL access.
-- Không thể dump được bằng SQLi qua web app vì ctf_user không có quyền.
CREATE TABLE IF NOT EXISTS credit_cards (
    ccid        INT          AUTO_INCREMENT PRIMARY KEY,
    cardholder  VARCHAR(100) NOT NULL,
    ccnumber    VARCHAR(19)  NOT NULL,
    ccv         VARCHAR(4)   NOT NULL,
    expiration  VARCHAR(7)   NOT NULL,
    card_type   VARCHAR(20)  NOT NULL
);

INSERT INTO credit_cards (cardholder, ccnumber, ccv, expiration, card_type) VALUES
('John Martinez',  '4532-1234-5678-9012', '123',  '09/2026', 'VISA'),
('Sarah Chen',     '5425-2334-3010-9903', '456',  '12/2025', 'MASTERCARD'),
('Anonymous User', '3714-496353-98431',   '7890', '03/2027', 'AMEX'),
('David Kim',      '6011-1111-1111-1117', '789',  '06/2026', 'DISCOVER'),
('Elena Volkov',   '4916-3385-0608-2007', '321',  '11/2025', 'VISA');

-- ── Bảng flags ───────────────────────────────────────────────
-- FLAG 2: chỉ tìm được khi dùng Metasploit truy cập MySQL trực tiếp.
-- Không thể tìm được qua SQLi web vì ctf_user bị giới hạn trong ctf_blog.
CREATE TABLE IF NOT EXISTS flags (
    id    INT          AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100) NOT NULL,
    value VARCHAR(100) NOT NULL,
    note  TEXT
);

INSERT INTO flags (name, value, note) VALUES
(
    'METASPLOIT_FLAG',
    'HTB{M3t4spl01t_MySQL_0wned}',
    'Captured via direct MySQL access using Metasploit mysql_login + mysql_sql. This database is NOT reachable through web app SQL injection — ctf_user has no SELECT privilege on payment_db. Only pentestuser (found via brute force) can access this.'
);

-- ── Tạo pentestuser ─────────────────────────────────────────
-- Account này bị developer để quên trên production.
-- Dùng mysql_native_password để hash ngắn (41 chars) → crackable với hashcat -m 300.
-- Hash sẽ được dump bằng SQLi ở Phase 4.7, crack ở Phase 5.2 → dùng ở Phase 7.
CREATE USER IF NOT EXISTS 'pentestuser'@'%' IDENTIFIED WITH mysql_native_password BY 'weak123';

-- pentestuser có quyền trên cả hai database
GRANT ALL PRIVILEGES ON ctf_blog.*   TO 'pentestuser'@'%';
GRANT ALL PRIVILEGES ON payment_db.* TO 'pentestuser'@'%';

-- ctf_user (web app) KHÔNG có quyền trên payment_db
-- (không cần REVOKE vì ctf_user chưa được grant payment_db)

-- [CTF] Developer misconfiguration: ctf_user được cấp quyền đọc mysql.user
-- → SQLi có thể dump authentication_string của pentestuser
-- → đây là bridge giữa SQLi phase và Metasploit phase
GRANT SELECT ON mysql.user TO 'ctf_user'@'%';

FLUSH PRIVILEGES;
