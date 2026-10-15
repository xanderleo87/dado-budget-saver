"""Backup manager: timestamped encrypted backups with retention."""

import os
import shutil
from datetime import datetime
from utils.constants import MAX_BACKUPS, DATA_DIR


class BackupManager:
    """Manages automatic and manual database backups."""

    def create_backup(self, encrypted_db_path: str, backup_dir: str) -> str:
        """Copy the encrypted DB file and salt to backup directory with timestamp."""
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Backup encrypted database
        backup_name = f"finance_{timestamp}.db.enc"
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(encrypted_db_path, backup_path)

        # Backup salt.bin alongside the database
        salt_src = os.path.join(DATA_DIR, "salt.bin")
        if os.path.exists(salt_src):
            salt_backup_name = f"salt_{timestamp}.bin"
            salt_backup_path = os.path.join(backup_dir, salt_backup_name)
            shutil.copy2(salt_src, salt_backup_path)

        self.prune_old_backups(backup_dir)
        return backup_path

    def prune_old_backups(self, backup_dir: str, keep: int = MAX_BACKUPS):
        """Delete oldest backups beyond the retention limit."""
        if not os.path.exists(backup_dir):
            return

        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.startswith("finance_") and f.endswith(".db.enc")],
            reverse=True,
        )

        for old in backups[keep:]:
            try:
                os.remove(os.path.join(backup_dir, old))
                # Also remove matching salt file
                timestamp = old.replace("finance_", "").replace(".db.enc", "")
                salt_file = os.path.join(backup_dir, f"salt_{timestamp}.bin")
                if os.path.exists(salt_file):
                    os.remove(salt_file)
            except OSError:
                pass

    def get_available_backups(self, backup_dir: str) -> list[dict]:
        """List available backups with metadata."""
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.startswith("finance_") and f.endswith(".db.enc"):
                path = os.path.join(backup_dir, f)
                stat = os.stat(path)
                # Check for matching salt backup
                timestamp = f.replace("finance_", "").replace(".db.enc", "")
                salt_path = os.path.join(backup_dir, f"salt_{timestamp}.bin")
                backups.append({
                    "filename": f,
                    "path": path,
                    "salt_path": salt_path if os.path.exists(salt_path) else None,
                    "size": stat.st_size,
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
        return backups
