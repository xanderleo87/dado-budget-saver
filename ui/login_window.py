"""Login dialog, first-run setup wizard, and backup recovery with aurora background."""

import os
import shutil
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QWidget, QListWidget,
    QListWidgetItem, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.security import SecurityManager
from core.database import DatabaseManager
from core.backup import BackupManager
from ui.components.animated_bg import AuroraBackground
from utils.constants import COLORS, ENCRYPTED_DB_PATH, DATA_DIR, BACKUP_DIR

logger = logging.getLogger("diday")


# ---------------------------------------------------------------------------
# Shared gradient button style
# ---------------------------------------------------------------------------
_GRADIENT_BTN_STYLE = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14B8A6, stop:1 #EC4899);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2DD4BF, stop:1 #F472B6);
    }
"""


def _make_header(layout):
    """Add the shared sparkle + cat + DIDAY title + subtitle + neon line."""
    sparkle_top = QLabel("\u2726 \u2727 \u2726")
    sparkle_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
    sparkle_top.setStyleSheet(f"color: {COLORS['pink']}; font-size: 18px; background: transparent;")
    layout.addWidget(sparkle_top)

    icon_label = QLabel("\U0001f431")
    icon_label.setFont(QFont("Segoe UI", 42))
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_label.setStyleSheet("background: transparent;")
    layout.addWidget(icon_label)

    title = QLabel("D I D A Y")
    title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet(f"color: {COLORS['magic_glow']}; background: transparent; letter-spacing: 6px;")
    layout.addWidget(title)

    subtitle = QLabel("Your Strict Money Saver!")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet(f"color: {COLORS['pink_hover']}; background: transparent; font-size: 13px; letter-spacing: 2px;")
    layout.addWidget(subtitle)

    neon_line = QFrame()
    neon_line.setFixedHeight(2)
    neon_line.setStyleSheet(f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 transparent, stop:0.3 {COLORS['accent']},
            stop:0.7 {COLORS['pink']}, stop:1 transparent);
    """)
    layout.addWidget(neon_line)


def _make_field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; background: transparent;")
    return lbl


def _make_error_label() -> QLabel:
    lbl = QLabel("")
    lbl.setStyleSheet(f"color: {COLORS['red']}; font-size: 12px; background: transparent;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


# ===========================================================================
# SetupWizard  —  Sign Up (first-run)
# ===========================================================================
class SetupWizard(QDialog):
    """First-run setup: create username, password and optionally enter API key."""

    def __init__(self, security: SecurityManager, parent=None):
        super().__init__(parent)
        self.security = security
        self.db: DatabaseManager | None = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Diday - Sign Up")
        self.setFixedSize(460, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(f"background-color: {COLORS['background']};")

        # Aurora background
        self.aurora = AuroraBackground(self)
        self.aurora.setGeometry(0, 0, 460, 600)
        self.aurora.lower()

        # Content overlay
        content = QWidget(self)
        content.setGeometry(0, 0, 460, 600)
        content.setStyleSheet("background: transparent;")
        content.raise_()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(10)

        _make_header(layout)
        layout.addSpacing(4)

        # Username
        layout.addWidget(_make_field_label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your name")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(_make_field_label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Minimum 6 characters")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)

        # Confirm password
        layout.addWidget(_make_field_label("Confirm Password"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Re-enter password")
        self.confirm_input.setMinimumHeight(40)
        layout.addWidget(self.confirm_input)

        # API Key
        layout.addWidget(_make_field_label("Claude API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-ant-... (optional)")
        self.api_key_input.setMinimumHeight(40)
        layout.addWidget(self.api_key_input)

        api_hint = QLabel("Optional — app works offline too")
        api_hint.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; background: transparent; font-style: italic;")
        layout.addWidget(api_hint)

        layout.addSpacing(6)

        # Sign Up button
        self.setup_btn = QPushButton("Sign Up")
        self.setup_btn.setMinimumHeight(44)
        self.setup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_btn.setStyleSheet(_GRADIENT_BTN_STYLE)
        self.setup_btn.clicked.connect(self._on_setup)
        layout.addWidget(self.setup_btn)

        # Error label
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        layout.addStretch()

    def _on_setup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        api_key = self.api_key_input.text().strip()

        if not username:
            self.error_label.setText("Please enter a username.")
            return
        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return
        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return
        if api_key and not api_key.startswith("sk-"):
            self.error_label.setText("API key should start with sk- (or leave empty for offline mode).")
            return

        try:
            # Create database
            os.makedirs(DATA_DIR, exist_ok=True)
            import tempfile
            temp_fd, temp_path = tempfile.mkstemp(suffix=".db", prefix="diday_setup_")
            os.close(temp_fd)

            self.db = DatabaseManager(temp_path)
            self.db.initialize_defaults()

            # Store username
            self.db.set_setting("username", username)

            # Store password hash
            password_hash = self.security.hash_password(password)
            self.db.set_setting("password_hash", password_hash)

            # Generate salt and derive key
            salt = self.security.generate_salt()
            self.db.set_setting("salt", salt.hex())
            salt_path = os.path.join(DATA_DIR, "salt.bin")
            with open(salt_path, "wb") as sf:
                sf.write(salt)
            self.security.derive_fernet_key(password, salt)

            # Encrypt and store API key
            encrypted_key = self.security.encrypt_string(api_key if api_key else "")
            self.db.set_setting("api_key_encrypted", encrypted_key)

            # Default settings
            self.db.set_setting("currency", "PHP")
            self.db.set_setting("currency_symbol", "\u20b1")
            self.db.set_setting("reminder_enabled", "1")
            self.db.set_setting("reminder_interval", "60")
            self.db.set_setting("daily_summary_time", "20:00")
            self.db.set_setting("backup_enabled", "1")
            self.db.set_setting("db_version", "1")

            # Welcome message
            self.db.add_chat_message(
                "assistant",
                f"Hey {username}! I'm Diday, your budget saver! "
                "Just tell me what you spent and I'll handle the rest.\n\n"
                "Try saying:\n"
                '- "spent 120 on food"\n'
                '- "loaned 1000 in Billease"\n'
                '- "earned 25000 salary"\n'
                '- "How much did I spend this month?"\n\n'
                'Type "help" anytime to see all the keywords I understand! nya~'
            )

            # Close DB and encrypt
            self.db.close()
            self.security.encrypt_database(temp_path, ENCRYPTED_DB_PATH)

            # Clean up temp
            os.remove(temp_path)

            self.aurora.stop()
            self.accept()

        except Exception as e:
            self.error_label.setText(f"Setup failed: {str(e)}")

    def get_db(self):
        return self.db


# ===========================================================================
# LoginDialog  —  Sign In (returning user)
# ===========================================================================
class LoginDialog(QDialog):
    """Username + password sign-in screen with aurora background."""

    # Custom result flag: True when user chose to create a new account
    CREATE_NEW_ACCOUNT = False

    def __init__(self, security: SecurityManager, parent=None):
        super().__init__(parent)
        self.security = security
        self._attempts = 0
        self.CREATE_NEW_ACCOUNT = False
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Diday - Sign In")
        self.setFixedSize(400, 440)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(f"background-color: {COLORS['background']};")

        # Aurora background
        self.aurora = AuroraBackground(self)
        self.aurora.setGeometry(0, 0, 400, 440)
        self.aurora.lower()

        # Content overlay
        content = QWidget(self)
        content.setGeometry(0, 0, 400, 440)
        content.setStyleSheet("background: transparent;")
        content.raise_()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        _make_header(layout)
        layout.addSpacing(6)

        # Username
        layout.addWidget(_make_field_label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(42)
        layout.addWidget(self.username_input)

        # Password
        layout.addWidget(_make_field_label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setMinimumHeight(42)
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)

        # Sign In button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(_GRADIENT_BTN_STYLE)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)

        # Error label
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Create New Account link at the bottom
        self.new_account_btn = QPushButton("Create New Account")
        self.new_account_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_account_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['accent']};
                border: none;
                font-size: 12px;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_hover']};
            }}
        """)
        self.new_account_btn.clicked.connect(self._on_create_new_account)
        layout.addWidget(self.new_account_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Focus username field first
        self.username_input.setFocus()

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self.error_label.setText("Please enter your username.")
            return
        if not password:
            self.error_label.setText("Please enter your password.")
            return

        try:
            salt_path = os.path.join(DATA_DIR, "salt.bin")

            if not os.path.exists(salt_path):
                self.error_label.setText("Salt file missing. Cannot decrypt.")
                return

            with open(salt_path, "rb") as f:
                salt = f.read()

            self.security.derive_fernet_key(password, salt)

            # Try to decrypt the database to verify credentials
            temp_path = self.security.decrypt_database(ENCRYPTED_DB_PATH)

            # Verify by opening and reading stored username + password hash
            db = DatabaseManager(temp_path)
            stored_hash = db.get_setting("password_hash")
            stored_username = db.get_setting("username") or ""
            db.close()

            password_ok = stored_hash and self.security.verify_password(password, stored_hash)
            username_ok = stored_username.lower() == username.lower()

            if password_ok and username_ok:
                # Clean up this verification temp file;
                # main.py will decrypt again for the working copy
                self.security.cleanup()
                # Re-derive the key since cleanup cleared state
                self.security.derive_fernet_key(password, salt)
                self.aurora.stop()
                self.accept()
            else:
                self.security.cleanup()
                self._attempts += 1
                remaining = max(0, 5 - self._attempts)
                self.error_label.setText(
                    f"Incorrect username or password. {remaining} attempts remaining."
                )
                if self._attempts >= 5:
                    self.login_btn.setEnabled(False)
                    self.error_label.setText("Too many attempts. Please restart the app.")
                self.password_input.clear()
                self.password_input.setFocus()

        except ValueError:
            self._attempts += 1
            self.security.cleanup()
            remaining = max(0, 5 - self._attempts)
            self.error_label.setText(
                f"Incorrect username or password. {remaining} attempts remaining."
            )
            self.password_input.clear()
            self.password_input.setFocus()

        except Exception as e:
            self.error_label.setText(f"Error: {str(e)}")

    def _on_create_new_account(self):
        reply = QMessageBox.warning(
            self,
            "Create New Account",
            "This will erase your current data and create a fresh account.\n"
            "A backup of your current data will be saved first.\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Backup current data before wiping
                if os.path.exists(ENCRYPTED_DB_PATH):
                    backup_mgr = BackupManager()
                    os.makedirs(BACKUP_DIR, exist_ok=True)
                    backup_mgr.create_backup(ENCRYPTED_DB_PATH, BACKUP_DIR)
                    logger.info("Created backup before new account creation.")

                # Remove current database and salt
                if os.path.exists(ENCRYPTED_DB_PATH):
                    os.remove(ENCRYPTED_DB_PATH)
                salt_path = os.path.join(DATA_DIR, "salt.bin")
                if os.path.exists(salt_path):
                    os.remove(salt_path)

                self.CREATE_NEW_ACCOUNT = True
                self.aurora.stop()
                self.reject()  # reject so main.py knows to show SetupWizard
            except Exception as e:
                self.error_label.setText(f"Error: {str(e)}")


# ===========================================================================
# RecoveryDialog  —  shown when DB is missing but backups exist
# ===========================================================================
class RecoveryDialog(QDialog):
    """Shown when finance.db is missing but backups exist. Lets user restore data."""

    RESTORE = 1
    START_FRESH = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result_action = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Diday - Recover Your Data")
        self.setFixedSize(480, 520)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(f"background-color: {COLORS['background']};")

        # Aurora background
        self.aurora = AuroraBackground(self)
        self.aurora.setGeometry(0, 0, 480, 520)
        self.aurora.lower()

        # Content overlay
        content = QWidget(self)
        content.setGeometry(0, 0, 480, 520)
        content.setStyleSheet("background: transparent;")
        content.raise_()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(12)

        # Sparkle decoration
        sparkle_top = QLabel("\u2726 \u2727 \u2726")
        sparkle_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sparkle_top.setStyleSheet(f"color: {COLORS['pink']}; font-size: 18px; background: transparent;")
        layout.addWidget(sparkle_top)

        # Cat icon
        icon_label = QLabel("\U0001f431")
        icon_label.setFont(QFont("Segoe UI", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)

        # Title
        title = QLabel("Data Recovery")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['magic_glow']}; background: transparent; letter-spacing: 3px;")
        layout.addWidget(title)

        # Explanation
        msg = QLabel(
            "Your database file is missing, but backups were found!\n"
            "Select a backup to restore your loans, income, and expenses."
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; background: transparent;")
        layout.addWidget(msg)

        # Neon line
        neon_line = QFrame()
        neon_line.setFixedHeight(2)
        neon_line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 {COLORS['accent']},
                stop:0.7 {COLORS['pink']}, stop:1 transparent);
        """)
        layout.addWidget(neon_line)

        # Backup list label
        layout.addWidget(_make_field_label("Available Backups"))

        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.backup_list.setMinimumHeight(150)
        self.backup_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['surface_hover']};
            }}
        """)
        layout.addWidget(self.backup_list)

        # Populate backups
        backup_mgr = BackupManager()
        self._backups = backup_mgr.get_available_backups(BACKUP_DIR)
        for b in self._backups:
            size_kb = b["size"] / 1024
            item = QListWidgetItem(f"{b['date']}   ({size_kb:.0f} KB)")
            item.setData(Qt.ItemDataRole.UserRole, {
                "path": b["path"],
                "salt_path": b.get("salt_path"),
            })
            self.backup_list.addItem(item)

        if self._backups:
            self.backup_list.setCurrentRow(0)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.setMinimumHeight(44)
        self.restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restore_btn.setStyleSheet(_GRADIENT_BTN_STYLE)
        self.restore_btn.clicked.connect(self._on_restore)
        btn_layout.addWidget(self.restore_btn)

        self.fresh_btn = QPushButton("Start Fresh")
        self.fresh_btn.setMinimumHeight(44)
        self.fresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_dim']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_hover']};
                color: {COLORS['text']};
            }}
        """)
        self.fresh_btn.clicked.connect(self._on_start_fresh)
        btn_layout.addWidget(self.fresh_btn)

        layout.addLayout(btn_layout)

        # Error label
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        layout.addStretch()

    def _on_restore(self):
        selected = self.backup_list.currentItem()
        if not selected:
            self.error_label.setText("Please select a backup to restore.")
            return

        data = selected.data(Qt.ItemDataRole.UserRole)
        backup_path = data["path"]
        salt_path = data.get("salt_path")

        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            shutil.copy2(backup_path, ENCRYPTED_DB_PATH)
            logger.info(f"Restored backup from {backup_path} to {ENCRYPTED_DB_PATH}")

            # Restore salt.bin alongside the database
            dest_salt = os.path.join(DATA_DIR, "salt.bin")
            if salt_path and os.path.exists(salt_path):
                shutil.copy2(salt_path, dest_salt)
                logger.info(f"Restored salt from {salt_path}")
            elif not os.path.exists(dest_salt):
                # Old backup without salt file and no existing salt.bin
                self.error_label.setText(
                    "Warning: salt file not found for this backup. "
                    "You may need to start fresh."
                )
                return

            self._result_action = self.RESTORE
            self.aurora.stop()
            self.accept()
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            self.error_label.setText(f"Restore failed: {str(e)}")

    def _on_start_fresh(self):
        reply = QMessageBox.warning(
            self,
            "Start Fresh",
            "This will create a new empty database.\n"
            "Your backups will still be available in the data/backups folder.\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._result_action = self.START_FRESH
            self.aurora.stop()
            self.accept()

    @property
    def result_action(self):
        return self._result_action
