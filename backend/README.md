# Backend

Django + Django REST Framework API for the Business Management System.

## Phase 3 status

- MySQL 8 (Laragon) connected via PyMySQL
- Database: `bms_db`
- Env flag: `USE_MYSQL=True`
- Helper scripts: `scripts/start-mysql.ps1`, `scripts/stop-mysql.ps1`

## Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set USE_MYSQL=True and DB_* credentials
.\scripts\start-mysql.ps1
python manage.py migrate
python manage.py runserver
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/api/v1/health/ | Smoke test |
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/api/redoc/ | ReDoc |
| http://127.0.0.1:8000/admin/ | Django admin |

## Tests

```powershell
pytest
```

## Structure

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── pytest.ini
├── scripts/
│   ├── start-mysql.ps1
│   ├── stop-mysql.ps1
│   ├── create_bms_db.sql
│   └── my.ini
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── db_backend.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    └── common/
```

Full MySQL guide: `../docs/mysql-setup.md`
