# API Specification: Activity Registration and Funding Audit Platform

This document describes the primary RESTful endpoints provided by the FastAPI backend. All endpoints are secured by Role-Based Access Control (RBAC).

## 1. Authentication (Auth) 👤
Endpoints for session management and login security.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/auth/login` | Authenticates users; checks for 10-fail lockout logic. |

## 2. Registrations & Materials 📄
Managing the lifecycle of applications and supporting documents.

| Method | Endpoint | Roles | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/registrations` | Applicant | Create a new registration from form data. |
| `PATCH` | `/registrations/{id}` | Applicant | Update registration; subject to deadline lock. |
| `POST` | `/registrations/{id}/submit` | Applicant | Finalize submission; locks materials. |
| `POST` | `/registrations/{id}/supplement`| Applicant | One-time 72-hour correction submission. |
| `POST` | `/materials/{id}/upload` | Applicant | Upload material with version control (max 3). |

## 3. Reviews & Workflow ⚖️
Processing and auditing submitted applications.

| Method | Endpoint | Roles | Description |
| :--- | :--- | : :--- |
| `GET` | `/registrations` | Reviewer+ | List all applications for review. |
| `POST` | `/reviews/batch` | Reviewer | Batch process (up to 50) application statuses. |

## 4. Funding & Audit 💰
Financial transaction tracking and invoice management.

| Method | Endpoint | Roles | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/funding/accounts` | Finance | Create budget accounts for activities. |
| `POST` | `/funding/transactions` | Finance | Record income/expense; returns overspending flag. |
| `POST` | `/funding/invoices/upload` | Finance | Upload invoice attachments to local disk. |
| `GET` | `/funding/statistics` | Finance+ | Statistics by category and time (year/month). |

## 5. System & Quality ⚙️
System-level operations, metrics, and administration.

| Method | Endpoint | Roles | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/system/quality/refresh` | Admin | Manually trigger quality metric recalculation. |
| `GET` | `/system/alerts` | Admin+ | Access alerts for overspending or low quality. |
| `POST` | `/system/backup` | Admin | Produce an encrypted system state backup. |
| `GET` | `/system/reports/{type}` | Admin+ | Export reconciliation, audit, or compliance reports. |
| `GET` | `/system/audit/access` | Admin | View traceable access audit logs. |

---
**Note:** A full, interactive API Swagger UI is available at `/docs` when the server is running.
