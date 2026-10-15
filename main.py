"""Diday - Your Budget Saver
AI Personal Finance Assistant
Entry point: single-instance check, login flow, app bootstrap.
"""

import sys
import os
import logging

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup file logging so errors are visible even with console=False (exe mode)
def _setup_logging():
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
    else:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "diday.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Also catch unhandled exceptions
    def _exception_hook(exc_type, exc_value, exc_tb):
        logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _exception_hook

_setup_logging()
logger = logging.getLogger("diday")

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSharedMemory, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from core.security import SecurityManager
from core.database import DatabaseManager
from core.ai_engine import AIEngine
from core.backup import BackupManager
from ui.login_window import SetupWizard, LoginDialog, RecoveryDialog
from ui.main_window import MainWindow
from ui.tray_icon import SystemTrayManager
from utils.constants import (
    APP_NAME, ENCRYPTED_DB_PATH, DATA_DIR, BACKUP_DIR,
    ASSETS_DIR, STYLES_DIR,
)


def _create_app_icon() -> QIcon:
    """Create app icon with cat on teal circle."""
    from PySide6.QtCore import QRect, Qt
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = max(1, size // 20)
        painter.setBrush(QColor("#14B8A6"))
        painter.setPen(QColor("transparent"))
        painter.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)
        painter.setPen(QColor("#0F172A"))
        painter.setFont(QFont("Segoe UI Emoji", int(size * 0.52)))
        painter.drawText(QRect(0, -int(size * 0.04), size, size),
                         Qt.AlignmentFlag.AlignCenter, "\U0001f431")
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def load_stylesheet() -> str:
    """Load the dark theme QSS."""
    qss_path = os.path.join(STYLES_DIR, "dark_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    # Single instance check
    shared_memory = QSharedMemory("Diday_BudgetSaver_SingleInstance_v1")
    if not shared_memory.create(1):
        # Another instance is running
        app = QApplication(sys.argv)
        QMessageBox.information(None, APP_NAME, "Diday is already running.\nCheck your system tray.")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(_create_app_icon())
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Load dark theme
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    # Ensure data directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    security = SecurityManager()

    # First run check — or recovery if database is missing but backups exist
    if not os.path.exists(ENCRYPTED_DB_PATH):
        # Check if backups are available for recovery
        backup_files = [
            f for f in os.listdir(BACKUP_DIR) if f.startswith("finance_") and f.endswith(".db.enc")
        ] if os.path.exists(BACKUP_DIR) else []

        if backup_files:
            # Database missing but backups found — offer recovery
            logger.info(f"Database missing but {len(backup_files)} backup(s) found. Showing recovery dialog.")
            recovery = RecoveryDialog()
            if recovery.exec() != RecoveryDialog.DialogCode.Accepted:
                sys.exit(0)

            if recovery.result_action == RecoveryDialog.START_FRESH:
                # User chose to start fresh — show setup wizard
                wizard = SetupWizard(security)
                if wizard.exec() != SetupWizard.DialogCode.Accepted:
                    sys.exit(0)
            # else: RESTORE — backup was copied to ENCRYPTED_DB_PATH, proceed to login
        else:
            # No database and no backups — true first run
            wizard = SetupWizard(security)
            if wizard.exec() != SetupWizard.DialogCode.Accepted:
                sys.exit(0)

    # Login — loop to allow "Create New Account" from the sign-in screen
    while True:
        login = LoginDialog(security)
        result = login.exec()

        if result == LoginDialog.DialogCode.Accepted:
            break  # Successful sign-in

        if login.CREATE_NEW_ACCOUNT:
            # User wants to create a new account — show SetupWizard then loop back
            wizard = SetupWizard(security)
            if wizard.exec() != SetupWizard.DialogCode.Accepted:
                sys.exit(0)
            # SetupWizard created new finance.db + salt.bin, loop back to sign-in
            continue

        # User closed the dialog normally — exit
        sys.exit(0)

    # Decrypt database
    try:
        logger.info("Decrypting database...")
        temp_db_path = security.decrypt_database(ENCRYPTED_DB_PATH)
        logger.info(f"Database decrypted to temp file: {temp_db_path}")
    except ValueError as e:
        logger.error(f"Database decryption failed: {e}")
        QMessageBox.critical(None, "Error", str(e))
        security.cleanup()
        sys.exit(1)

    # Initialize components
    db = DatabaseManager(temp_db_path)
    logger.info("Database manager initialized.")

    # Get API key (empty string is fine — app works offline)
    try:
        encrypted_key = db.get_setting("api_key_encrypted")
        api_key = security.decrypt_string(encrypted_key) if encrypted_key else ""
    except Exception as e:
        logger.warning(f"Could not decrypt API key, running in offline mode: {e}")
        api_key = ""

    ai = AIEngine(api_key)

    # Main window
    window = MainWindow(db, ai, security, ENCRYPTED_DB_PATH)
    window.show()

    # System tray
    tray = SystemTrayManager(window, db)
    tray.show()

    # Periodic auto-save (re-encrypt database every 60 seconds)
    save_timer = QTimer()
    def auto_save():
        try:
            db.checkpoint()  # Flush WAL to main .db file first
            security.encrypt_database(temp_db_path, ENCRYPTED_DB_PATH)
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
    save_timer.timeout.connect(auto_save)
    save_timer.start(60_000)  # Every 60 seconds

    # Cleanup on exit
    def cleanup():
        try:
            logger.info("Shutting down — saving database...")

            # Auto backup check before closing DB
            backup_enabled = db.get_setting("backup_enabled")

            # Close DB first — this flushes WAL to the main .db file
            db.close()
            logger.info("Database closed (WAL flushed).")

            # NOW encrypt the complete .db file
            security.encrypt_database(temp_db_path, ENCRYPTED_DB_PATH)
            logger.info("Database encrypted successfully.")

            # Auto backup
            if backup_enabled == "1":
                try:
                    backup_mgr = BackupManager()
                    backup_mgr.create_backup(ENCRYPTED_DB_PATH, BACKUP_DIR)
                    logger.info("Backup created.")
                except Exception as e:
                    logger.error(f"Backup failed: {e}")

            security.cleanup()
            logger.info("Cleanup complete.")
        except Exception as e:
            logger.critical(f"Cleanup failed: {e}")

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
