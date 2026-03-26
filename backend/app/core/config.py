from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Activity Registration and Funding Audit Management Platform"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/activity_audit"
    local_storage_root: str = "./storage"
    backup_root: str = "./backups"
    max_single_file_mb: int = 20
    max_total_file_mb: int = 200
    max_material_versions: int = 3
    supplement_window_hours: int = 72
    login_window_minutes: int = 5
    login_max_failed_attempts: int = 10
    login_lock_minutes: int = 30
    overspending_ratio_threshold: float = 1.1
    quality_metrics_interval_hours: int = 24
    enable_quality_scheduler: bool = True
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_paths(self) -> None:
        Path(self.local_storage_root).mkdir(parents=True, exist_ok=True)
        Path(self.backup_root).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_paths()
