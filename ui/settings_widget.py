"""Settings widget for password, backup, and export management."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGroupBox, QCheckBox, QSpinBox,
    QComboBox, QFileDialog, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.database import DatabaseManager
from core.security import SecurityManager
from utils.constants import COLORS, APP_VERSION, DATA_DIR, BACKUP_DIR


class SettingsWidget(QWidget):
    """App settings: API key, password, notifications, backup, export."""

    def __init__(self, db: DatabaseManager, security: SecurityManager,
                 encrypted_db_path: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.security = security
        self.encrypted_db_path = encrypted_db_path
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        header = QLabel("\u2726 Settings")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"background: transparent; color: {COLORS['magic_glow']}; letter-spacing: 2px;")
        layout.addWidget(header)

        # API Configuration
        api_group = self._create_group("API Configuration")
        api_layout = api_group.layout()

        api_row = QHBoxLayout()
        api_label = QLabel("Claude API Key:")
        api_label.setFixedWidth(120)
        api_label.setStyleSheet("background: transparent;")
        api_row.addWidget(api_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-ant-...")
        self.api_key_input.setMinimumHeight(36)
        encrypted = self.db.get_setting("api_key_encrypted")
        if encrypted:
            try:
                key = self.security.decrypt_string(encrypted)
                self.api_key_input.setText(key)
            except Exception:
                self.api_key_input.setPlaceholderText("Failed to decrypt")
        api_row.addWidget(self.api_key_input, 1)

        show_btn = QPushButton("Show")
        show_btn.setFixedWidth(60)
        show_btn.setObjectName("secondaryButton")
        show_btn.clicked.connect(self._toggle_api_key_visibility)
        api_row.addWidget(show_btn)

        update_btn = QPushButton("Update")
        update_btn.setFixedWidth(70)
        update_btn.clicked.connect(self._update_api_key)
        api_row.addWidget(update_btn)

        api_layout.addLayout(api_row)

        model_row = QHBoxLayout()
        model_label = QLabel("AI Model:")
        model_label.setFixedWidth(120)
        model_label.setStyleSheet("background: transparent;")
        model_row.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
        ])
        self.model_combo.setMinimumHeight(36)
        model_row.addWidget(self.model_combo, 1)
        api_layout.addLayout(model_row)

        layout.addWidget(api_group)

        # Password
        pwd_group = self._create_group("Security")
        pwd_layout = pwd_group.layout()

        pwd_row = QHBoxLayout()
        current_label = QLabel("Current:")
        current_label.setFixedWidth(70)
        current_label.setStyleSheet("background: transparent;")
        pwd_row.addWidget(current_label)
        self.current_pwd = QLineEdit()
        self.current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_pwd.setMinimumHeight(36)
        pwd_row.addWidget(self.current_pwd)

        new_label = QLabel("New:")
        new_label.setFixedWidth(40)
        new_label.setStyleSheet("background: transparent;")
        pwd_row.addWidget(new_label)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd.setMinimumHeight(36)
        pwd_row.addWidget(self.new_pwd)

        change_btn = QPushButton("Change")
        change_btn.setFixedWidth(80)
        change_btn.clicked.connect(self._change_password)
        pwd_row.addWidget(change_btn)

        pwd_layout.addLayout(pwd_row)
        layout.addWidget(pwd_group)

        # Notifications
        notif_group = self._create_group("Notifications")
        notif_layout = notif_group.layout()

        reminder_row = QHBoxLayout()
        self.reminder_check = QCheckBox("Hourly Reminder")
        self.reminder_check.setChecked(self.db.get_setting("reminder_enabled") == "1")
        reminder_row.addWidget(self.reminder_check)

        reminder_row.addWidget(QLabel("Every"))
        self.reminder_interval = QSpinBox()
        self.reminder_interval.setRange(15, 180)
        self.reminder_interval.setValue(int(self.db.get_setting("reminder_interval") or 60))
        self.reminder_interval.setSuffix(" min")
        self.reminder_interval.setMinimumHeight(32)
        reminder_row.addWidget(self.reminder_interval)
        reminder_row.addStretch()
        notif_layout.addLayout(reminder_row)

        summary_row = QHBoxLayout()
        self.summary_check = QCheckBox("Daily Summary Notification")
        self.summary_check.setChecked(True)
        summary_row.addWidget(self.summary_check)
        summary_row.addStretch()
        notif_layout.addLayout(summary_row)

        save_notif_btn = QPushButton("Save Notification Settings")
        save_notif_btn.clicked.connect(self._save_notifications)
        notif_layout.addWidget(save_notif_btn)

        layout.addWidget(notif_group)

        # Data Management
        data_group = self._create_group("Data Management")
        data_layout = data_group.layout()

        backup_row = QHBoxLayout()
        backup_btn = QPushButton("Backup Now")
        backup_btn.clicked.connect(self._backup_now)
        backup_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore from Backup")
        restore_btn.setObjectName("secondaryButton")
        restore_btn.clicked.connect(self._restore_backup)
        backup_row.addWidget(restore_btn)
        backup_row.addStretch()
        data_layout.addLayout(backup_row)

        export_row = QHBoxLayout()
        csv_btn = QPushButton("Export to CSV")
        csv_btn.clicked.connect(self._export_csv)
        export_row.addWidget(csv_btn)

        pdf_btn = QPushButton("Export to PDF")
        pdf_btn.clicked.connect(self._export_pdf)
        export_row.addWidget(pdf_btn)
        export_row.addStretch()
        data_layout.addLayout(export_row)

        clear_row = QHBoxLayout()
        clear_chat_btn = QPushButton("Clear Chat History")
        clear_chat_btn.setObjectName("dangerButton")
        clear_chat_btn.clicked.connect(self._clear_chat)
        clear_row.addWidget(clear_chat_btn)
        clear_row.addStretch()
        data_layout.addLayout(clear_row)

        layout.addWidget(data_group)

        # About
        about_group = self._create_group("About")
        about_layout = about_group.layout()
        about_text = QLabel(
            f"Diday v{APP_VERSION}\n"
            "Your Budget Saver\n"
            "Powered by Claude API | Built with PySide6"
        )
        about_text.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; font-size: 12px;")
        about_layout.addWidget(about_text)
        layout.addWidget(about_group)

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                background: rgba(30, 41, 59, 0.65);
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                margin-top: 14px;
                padding-top: 20px;
                font-weight: bold;
                color: {COLORS['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        return group

    def _toggle_api_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _update_api_key(self):
        new_key = self.api_key_input.text().strip()
        if not new_key.startswith("sk-"):
            QMessageBox.warning(self, "Invalid", "API key must start with 'sk-'")
            return
        try:
            encrypted = self.security.encrypt_string(new_key)
            self.db.set_setting("api_key_encrypted", encrypted)
            QMessageBox.information(self, "Success", "API key updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update: {e}")

    def _change_password(self):
        current = self.current_pwd.text()
        new = self.new_pwd.text()
        if len(new) < 6:
            QMessageBox.warning(self, "Invalid", "New password must be at least 6 characters.")
            return

        stored_hash = self.db.get_setting("password_hash")
        if not self.security.verify_password(current, stored_hash):
            QMessageBox.warning(self, "Invalid", "Current password is incorrect.")
            return

        new_hash = self.security.hash_password(new)
        self.db.set_setting("password_hash", new_hash)

        new_salt = self.security.generate_salt()
        self.db.set_setting("salt", new_salt.hex())

        salt_path = os.path.join(DATA_DIR, "salt.bin")
        with open(salt_path, "wb") as f:
            f.write(new_salt)

        self.security.derive_fernet_key(new, new_salt)

        try:
            api_key = self.api_key_input.text().strip()
            if api_key:
                encrypted = self.security.encrypt_string(api_key)
                self.db.set_setting("api_key_encrypted", encrypted)
        except Exception:
            pass

        self.current_pwd.clear()
        self.new_pwd.clear()
        QMessageBox.information(self, "Success", "Password changed successfully.")

    def _save_notifications(self):
        self.db.set_setting("reminder_enabled", "1" if self.reminder_check.isChecked() else "0")
        self.db.set_setting("reminder_interval", str(self.reminder_interval.value()))
        QMessageBox.information(self, "Saved", "Notification settings saved.")

    def _backup_now(self):
        try:
            from core.backup import BackupManager
            backup = BackupManager()
            path = backup.create_backup(self.encrypted_db_path, BACKUP_DIR)
            QMessageBox.information(self, "Backup", f"Backup created:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed: {e}")

    def _restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", BACKUP_DIR, "Database files (*.db *.db.enc)"
        )
        if path:
            reply = QMessageBox.question(
                self, "Restore",
                "This will replace your current data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    import shutil
                    shutil.copy2(path, self.encrypted_db_path)
                    QMessageBox.information(self, "Restored", "Backup restored. Please restart the app.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Restore failed: {e}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", os.path.expanduser("~/Desktop/expenses.csv"), "CSV files (*.csv)"
        )
        if path:
            try:
                from core.export import ExportManager
                exporter = ExportManager()
                exporter.export_csv(self.db, path)
                QMessageBox.information(self, "Exported", f"CSV exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", os.path.expanduser("~/Desktop/finance_report.pdf"), "PDF files (*.pdf)"
        )
        if path:
            try:
                from core.export import ExportManager
                exporter = ExportManager()
                exporter.export_pdf(self.db, path)
                QMessageBox.information(self, "Exported", f"PDF exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def _clear_chat(self):
        reply = QMessageBox.question(
            self, "Clear Chat",
            "This will delete all chat history. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_chat_history()
            QMessageBox.information(self, "Cleared", "Chat history cleared.")
