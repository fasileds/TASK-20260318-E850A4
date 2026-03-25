import subprocess
from pathlib import Path
from app.core.config import settings
from app.core.security import now_utc

def run_db_backup() -> str:
    """Runs pg_dump and returns the path to the backup file."""
    now = now_utc().strftime("%Y%m%d_%H%M%S")
    backup_file = Path(settings.backup_root) / f"backup_{now}.sql"
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Simple pg_dump command based on DATABASE_URL
    # Format: postgresql+psycopg2://user:pass@host:port/dbname
    conn_str = settings.database_url.replace("postgresql+psycopg2://", "postgresql://")
    
    subprocess.run(
        ["pg_dump", "--dbname", conn_str, "-f", str(backup_file)],
        check=True,
        capture_output=True,
        text=True
    )
    return str(backup_file)
