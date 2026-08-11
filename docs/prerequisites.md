# Software prerequisites

Verified / needed on this machine for later phases.

## Required

| Tool | Purpose | Notes for this machine |
|------|---------|------------------------|
| Git | Version control | Install/init in Phase 1 |
| Python 3.11+ | Backend | Detected: **Python 3.14.3** — if a package fails to install, use 3.12 via pyenv or official installer |
| Node.js 20+ | Frontend | Detected: **v24.14.1** |
| MySQL 8 | Database | **Not on PATH yet** — install in Phase 3 |
| Redis | Celery broker | Optional until Phase 17; use Celery eager mode earlier |

## Windows tips

1. **MySQL:** [MySQL Installer](https://dev.mysql.com/downloads/installer/) or WSL2 MySQL. Add `bin` to PATH so `mysql` works in PowerShell.
2. **PyMySQL:** Preferred driver on Windows (no C compiler required for mysqlclient).
3. **Redis:** WSL Redis, Docker, or Memurai when we enable real Celery workers.
4. **Visual C++ Build Tools:** Only needed if you switch to `mysqlclient` or other C-extension packages.

## Phase 2 will install (Python)

Django, DRF, SimpleJWT, django-filter, drf-spectacular, django-cors-headers, python-decouple, PyMySQL, Pillow, celery, redis, reportlab, openpyxl, pytest-django, …

## Phase 18 will install (Node)

React, Vite, React Router, Axios, TanStack Query, React Hook Form, Zod, Tailwind, Recharts, …
