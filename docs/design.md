# Design Documentation: Activity Registration and Funding Audit Platform

This documentation outlines the architectural design, core modules, and security model of the Activity Registration and Funding Audit Management Platform.

## 1. System Architecture
The platform is built as a modular, offline-capable application using a fully containerized stack:
*   **Frontend:** React (Vite) for a fast, responsive user interface. Built with a role-based dashboard system and real-time form validation.
*   **Backend:** FastAPI (Python 3.13) providing high-performance, asynchronous RESTful interfaces.
*   **Database:** PostgreSQL (v15) for persisted storage of relational entities and audit logs.
*   **Storage:** Local disk-based storage root for all uploaded materials and invoice attachments.

## 2. Role-Based Access Model
Four distinct roles are implemented to manage the "closed-loop" lifecycle:
1.  **Applicant:** Submits registrations using a guided form wizard and uploads supporting materials via checklists.
2.  **Reviewer:** Processes applications through a formal review state machine. Supports batch reviews and comment tracking.
3.  **Financial Administrator:** Records transactions, uploads invoices, and monitors budgets with automatic overspending flags.
4.  **System Administrator:** Manages system-level alerts, quality metrics, encrypted configurations, and local backups.

## 3. Core Modules & Workflows
### A. Application Registration & Versioning
Applicants follow a checklist-based upload process. Each material item supports up to **three versions**, after which the oldest is deleted to maintain storage efficiency. Files are validated for both type (PDF, JPG, PNG) and size (≤20MB single, ≤200MB total).

### B. Review State Machine
Applications move through a defined lifecycle:
`Draft` → `Submitted` → `Supplemented` → `Approved/Rejected` → `Canceled` → `Promoted from Waitlist`.

### C. Funding Audit Loop
Each registration is linked to a `FundingAccount`. The system automatically sets a **110% overspending threshold** flag. Financial admins must provide secondary confirmation when adding expenses that exceed this budget limit.

## 4. Security & Privacy Model
*   **Authentication:** Only username/password based with Argon2/Bcrypt hashing.
*   **Access Frequency Control:** Accounts are locked for **30 minutes** after **10 failed login attempts** within a **5-minute window**.
*   **Data Masking:** Sensitive fields (like ID numbers and contact info) are masked (`********`) when returned to any non-administrator or non-owner user via the API.
*   **Data Integrity:** SHA-256 fingerprints are saved for every submitted material version to perform duplicate submission detection before storage.
*   **Encryption:** Sensitive configuration keys are encrypted at rest using a custom cryptographic provider.
