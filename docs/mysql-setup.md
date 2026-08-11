# MySQL Setup Guide — Business Management System

## Goal (Phase 3)

Run Django against **MySQL 8** using environment variables and **PyMySQL** (no `mysqlclient` C compiler on Windows).

## This machine (Laragon)

Detected install:

- Binaries: `C:\laragon\bin\mysql\mysql-8.4.3-winx64`
- Data dir: `C:\laragon\data\mysql-8.4.3`
- Config: `C:\laragon\bin\mysql\mysql-8.4.3-winx64\my.ini`
- Database: `bms_db`
- App user: `bms_user` / password in `backend/.env` (not committed)

### Start MySQL (if port 3306 is down)

PowerShell:

```powershell
cd "c:\Users\Admin\Desktop\Projects\Business Management system\backend"
.\scripts\start-mysql.ps1
```

Or manually:

```powershell
Start-Process -FilePath "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysqld.exe" `
  -ArgumentList '--defaults-file=C:\laragon\bin\mysql\mysql-8.4.3-winx64\my.ini' `
  -WindowStyle Hidden
```

You can also open **Laragon** and start MySQL from its UI (if you prefer).

### Stop MySQL

```powershell
.\scripts\stop-mysql.ps1
```

### Create DB / user (already done once)

```sql
CREATE DATABASE IF NOT EXISTS bms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'bms_user'@'localhost' IDENTIFIED BY 'your_password';
CREATE USER IF NOT EXISTS 'bms_user'@'127.0.0.1' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bms_db.* TO 'bms_user'@'localhost';
GRANT ALL PRIVILEGES ON bms_db.* TO 'bms_user'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Root was initialized with an **empty password** for local development only (`--initialize-insecure`). Set a real root password before any non-local use.

---

## Windows (general)

### Option A — Laragon (used here)

1. Install [Laragon](https://laragon.org/)
2. Start MySQL from Laragon
3. Create `bms_db` via HeidiSQL / mysql CLI / Adminer
4. Copy `.env.example` → `.env` and set `USE_MYSQL=True` + `DB_*`

### Option B — MySQL Installer

1. Download [MySQL Installer](https://dev.mysql.com/downloads/installer/)
2. Install MySQL Server 8.x
3. Add `...\MySQL\MySQL Server 8.x\bin` to PATH
4. Create database and user as above

### Option C — winget

```powershell
winget install Oracle.MySQL
```

Then configure service and create DB/user.

---

## WSL / Linux

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql -e "CREATE DATABASE bms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
# create user + grants...
```

---

## Django wiring

`backend/config/settings/db_backend.py` installs PyMySQL as `MySQLdb`.

`development.py` switches engines when:

```env
USE_MYSQL=True
```

Verify:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py dbshell
# or
python manage.py migrate
python manage.py check --database default
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Can't connect to MySQL server on '127.0.0.1'` | Start mysqld / Laragon; check port 3306 |
| `Access denied for user` | Check `DB_USER` / `DB_PASSWORD` / host (`127.0.0.1` vs `localhost`) |
| `Unknown database 'bms_db'` | Run `CREATE DATABASE` |
| Charset issues | Use `utf8mb4` DB + `OPTIONS.charset` in settings |
