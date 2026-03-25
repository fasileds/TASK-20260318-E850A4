# Activity Registration and Funding Audit Management Platform

An integrated, offline-capable platform for full-cycle management of activity applications and funding audits.

## 🚀 One-Click Start Command

To start the entire platform (Frontend, Backend, and Database) at once, ensure you have Docker installed and run:

```bash
docker-compose up --build
```

---

## 🌐 Service Addresses

Once the containers are successfully running, you can access the platform at these addresses:

| Service | Access URL |
| :--- | :--- |
| **Frontend UI (React)** | [http://localhost:3000](http://localhost:3000) |
| **Backend API (FastAPI Docs)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **PostgreSQL Database** | `localhost:5432` (Accessed via Docker network) |

---

## ✅ Verification Method (How to Test)

A reviewer can verify that the project is working correctly using the following methods:

### 1. Functional Testing (Manual Login)
Use these demo accounts to verify each role-specific dashboard:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Applicant** | `applicant_demo` | `Applicant@123` |
| **Reviewer** | `reviewer_demo` | `Reviewer@123` |
| **Finance Admin** | `finance_demo` | `Finance@123` |
| **System Admin** | `admin_demo` | `Admin@123` |

**Verification Steps:**
- **Applicant:** Log in and attempt to upload a file over 20MB (should be rejected).
- **Reviewer:** Batch-select multiple applications and approve them at once.
- **Finance:** Add a transaction that exceeds the 110% budget threshold; confirm you see the **secondary confirmation pop-up**.

### 2. Automated Compliance Testing
To verify all business rules (Material versioning, 72-hour windows, lockout logic, and data masking), run the unified test suite:
```bash
bash run_tests.sh
```

---

## 🔒 Security & Quality Compliance
- **Access Frequency Control:** Account locks for 30 minutes after 10 failed attempts within 5 minutes.
- **Role-Based Masking:** Sensitive fields (IDs, Phone Numbers) are hidden from non-admin users.
- **SHA-256 Fingerprints:** Duplicate file submissions are automatically detected and blocked.
- **Rules & Alerts:** System triggers local alerts for overspending and low approval rates.


## One-Click Startup with Docker Compose

From project root:

```bash
docker-compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Database: PostgreSQL 15 on `localhost:5432` (inside Compose network as `db`)

Environment wiring:

- Backend `DATABASE_URL` is injected by Compose using service name `db`.
- Frontend API base URL is injected at build time via `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

## Compliance Test Framework

Test layout:

- Backend unit tests: `backend/tests/unit`
- Backend API tests: `backend/tests/api`
- Frontend tests: `frontend/src/__tests__`

One-command execution:

```bash
./run_tests.sh
```

The script prints a pass/fail line for each mandatory requirement marker and then runs frontend tests.
