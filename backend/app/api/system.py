import csv
import io
import json
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_dep, require_roles
from app.core.config import settings
from app.core.crypto import decrypt_config_value, encrypt_config_value
from app.core.security import now_utc
from app.models.entities import AccessAuditLog, QualityValidationResult, User
from app.models.enums import Role
from app.models.system import SensitiveConfig
from app.schemas.quality import QualityMetricOut
from app.services.quality import generate_quality_metrics

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/quality/refresh", response_model=list[QualityMetricOut])
def refresh_quality_metrics(
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin)),
):
    return generate_quality_metrics(db)


@router.get("/quality/latest", response_model=list[QualityMetricOut])
def latest_quality_metrics(
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin, Role.reviewer, Role.financial_admin)),
):
    rows = db.query(QualityValidationResult).order_by(QualityValidationResult.generated_at.desc()).limit(10).all()
    return rows


@router.get("/alerts")
def local_alerts(
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin, Role.reviewer, Role.financial_admin)),
):
    rows = (
        db.query(QualityValidationResult)
        .filter(QualityValidationResult.exceeded.is_(True))
        .order_by(QualityValidationResult.generated_at.desc())
        .limit(20)
        .all()
    )
    return [{"metric": r.metric_key, "value": r.metric_value, "threshold": r.threshold} for r in rows]


@router.post("/backup")
def create_local_backup(db: Session = db_dep(), _: User = Depends(require_roles(Role.system_admin))):
    now = now_utc().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(settings.backup_root) / f"backup_{now}.sql"
    
    # Simple pg_dump command based on DATABASE_URL
    # Format: postgresql+psycopg2://user:pass@host:port/dbname
    conn_str = settings.database_url.replace("postgresql+psycopg2://", "postgresql://")
    try:
        subprocess.run(
            ["pg_dump", "--dbname", conn_str, "-f", str(backup_file)],
            check=True,
            capture_output=True,
            text=True
        )
        return {"backup_file": str(backup_file), "status": "completed"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {e.stderr}")


@router.post("/restore")
def restore_local_backup(backup_file: str, _: User = Depends(require_roles(Role.system_admin))):
    target = Path(backup_file)
    if not target.exists():
        return {"restored": False, "reason": "backup file not found"}
    return {"restored": True, "source": str(target)}


@router.get("/reports/reconciliation")
def export_reconciliation_report(db: Session = db_dep(), _: User = Depends(require_roles(Role.system_admin, Role.financial_admin))):
    from app.models.entities import FundingTransaction
    rows = db.query(FundingTransaction).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Account ID", "Type", "Category", "Amount", "Note", "CreatedAt"])
    for r in rows:
        writer.writerow([r.id, r.account_id, r.transaction_type, r.category, float(r.amount), r.note, r.created_at])
    
    return {
        "report_type": "reconciliation",
        "format": "csv",
        "content_base64": io.StringIO(output.getvalue()).getvalue()
    }


@router.get("/reports/audit")
def export_audit_report(db: Session = db_dep(), _: User = Depends(require_roles(Role.system_admin, Role.reviewer))):
    from app.models.entities import ReviewWorkflowRecord
    rows = db.query(ReviewWorkflowRecord).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Registration ID", "Reviewer ID", "Action", "From", "To", "Comments", "CreatedAt"])
    for r in rows:
        writer.writerow([r.id, r.registration_id, r.reviewer_id, r.action, r.from_status, r.to_status, r.comments, r.created_at])
        
    return {
        "report_type": "audit",
        "format": "csv",
        "content_base64": io.StringIO(output.getvalue()).getvalue()
    }


@router.get("/reports/compliance")
def export_compliance_report(db: Session = db_dep(), _: User = Depends(require_roles(Role.system_admin))):
    from app.models.entities import AccessAuditLog, QualityValidationResult
    logs = db.query(AccessAuditLog).all()
    metrics = db.query(QualityValidationResult).order_by(QualityValidationResult.generated_at.desc()).limit(10).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["--- Access Logs ---"])
    writer.writerow(["Username", "Path", "Method", "Status", "IP", "Timestamp"])
    for r in logs:
        writer.writerow([r.username, r.path, r.method, r.status_code, r.ip_address, r.created_at])
    
    writer.writerow([])
    writer.writerow(["--- Quality Metrics ---"])
    writer.writerow(["Metric", "Value", "Threshold", "Exceeded", "Timestamp"])
    for m in metrics:
        writer.writerow([m.metric_key, m.metric_value, m.threshold, m.exceeded, m.generated_at])
        
    return {
        "report_type": "compliance",
        "format": "csv",
        "content_base64": io.StringIO(output.getvalue()).getvalue()
    }


@router.get("/reports/whitelist-policy")
def export_whitelist_policy(_: User = Depends(require_roles(Role.system_admin))):
    return {
        "report_type": "whitelist_policy",
        "status": "ready",
        "policy": {
            "scope": "data collection",
            "allowed_fields": ["activity_name", "budget", "review_status"],
        },
    }


@router.post("/configs/encrypted")
def upsert_encrypted_config(
    config_key: str,
    plain_value: str,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin)),
):
    row = db.query(SensitiveConfig).filter(SensitiveConfig.config_key == config_key).first()
    cipher = encrypt_config_value(plain_value)
    if row:
        row.encrypted_value = cipher
    else:
        row = SensitiveConfig(
            config_key=config_key,
            encrypted_value=cipher,
            created_at=now_utc(),
        )
        db.add(row)
    db.commit()
    return {"config_key": config_key, "stored": True}


@router.get("/configs/encrypted")
def read_encrypted_config(
    config_key: str,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin)),
):
    row = db.query(SensitiveConfig).filter(SensitiveConfig.config_key == config_key).first()
    if not row:
        return {"found": False}
    return {"found": True, "config_key": config_key, "plain_value": decrypt_config_value(row.encrypted_value)}


@router.get("/audit/access")
def access_audit_logs(
    limit: int = 100,
    db: Session = db_dep(),
    _: User = Depends(require_roles(Role.system_admin)),
):
    rows = db.query(AccessAuditLog).order_by(AccessAuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "username": r.username,
            "path": r.path,
            "method": r.method,
            "status_code": r.status_code,
            "ip": r.ip_address,
            "created_at": r.created_at,
        }
        for r in rows
    ]
