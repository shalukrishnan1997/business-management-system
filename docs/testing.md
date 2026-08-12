# Testing (Phase 23)

Hardened API coverage plus light frontend unit tests.

## Backend

```bash
cd backend
pytest
```

Uses `config.settings.testing` (SQLite in-memory) via `pytest.ini`.

### What was hardened

| Area | Location |
|------|----------|
| Shared helpers | `apps/common/tests/helpers.py` (`auth_header`, `make_user`, `seed_party_catalog`) |
| E2E workflow | `apps/common/tests/test_workflow_integration.py` — purchase receive → sale complete → invoice from sale → payment |
| RBAC denials | `apps/common/tests/test_rbac_denials.py` — viewer / sales / inventory write blocks |
| Invoice cancel | `apps/invoices/tests/test_invoices.py` — cancel + block already-cancelled / paid |
| Report matrix | `apps/reports/tests/test_reports.py` — all 6 types × csv/xlsx/pdf |

Existing per-module APITestCase suites remain the primary coverage for auth, catalog, stock, docs, expenses, employees, notifications, and audit.

## Frontend

```bash
cd frontend
npm test
```

Vitest covers pure helpers (`formatMoney`, `cleanParams` in `utils/`). UI E2E is out of scope for Phase 23.

## Notes

- Prefer `pytest` over `manage.py test` so tests always use the testing settings module.
- Prefer JWT `auth_header` + `APIClient` credentials to match production auth.
- `factory-boy` is available in requirements for future factories; helpers cover the common seed path for now.
