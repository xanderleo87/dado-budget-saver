"""Chat interface widget with message bubbles and AI integration."""

import json
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QScrollArea, QLabel, QFrame,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QPropertyAnimation, Property
from PySide6.QtGui import QFont, QPainter, QColor, QRadialGradient, QPen

from core.database import DatabaseManager
from core.ai_engine import AIEngine
from ui.components.message_bubble import MessageBubble, TypingIndicator
from utils.constants import COLORS
from utils.helpers import format_currency, today_str, current_month_year, now_ph


class GlowingAvatar(QWidget):
    """Cat avatar with animated teal glow ring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._glow_opacity = 1.0
        self._glow_direction = -1  # -1 = fading out, 1 = fading in
        self.setFixedSize(72, 72)
        self.setStyleSheet("background: transparent;")

        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._animate_glow)
        self._glow_timer.start(50)

    def _animate_glow(self):
        self._glow_opacity += self._glow_direction * 0.025
        if self._glow_opacity <= 0.3:
            self._glow_opacity = 0.3
            self._glow_direction = 1
        elif self._glow_opacity >= 1.0:
            self._glow_opacity = 1.0
            self._glow_direction = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = 30

        # Outer glow ring — pulsing teal
        glow_alpha = int(100 * self._glow_opacity)
        for i in range(3):
            r = radius + 6 - i * 2
            color = QColor(20, 184, 166, glow_alpha - i * 20)
            pen = QPen(color, 2.5 - i * 0.5)
            painter.setPen(pen)
            painter.setBrush(QColor(0, 0, 0, 0))
            painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # Dark circle background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#0A0E1A"))
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        # Border ring
        border_color = QColor(20, 184, 166, int(200 * self._glow_opacity))
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        # Cat emoji
        painter.setPen(QColor("#F0F4F8"))
        font = QFont("Segoe UI Emoji", 28)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "\U0001f431")

        # Status dot — bottom-right (teal = active)
        dot_r = 7
        dot_x = int(cx + radius - dot_r + 2)
        dot_y = int(cy + radius - dot_r + 2)
        painter.setPen(QPen(QColor("#0A0E1A"), 2))
        painter.setBrush(QColor("#14B8A6"))
        painter.drawEllipse(dot_x - dot_r, dot_y - dot_r, dot_r * 2, dot_r * 2)

        painter.end()


class AIWorker(QThread):
    """Background thread for Claude API calls."""
    response_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, ai_engine: AIEngine, user_message: str, context: dict):
        super().__init__()
        self.ai_engine = ai_engine
        self.user_message = user_message
        self.context = context

    def run(self):
        try:
            response = self.ai_engine.process_message(self.user_message, self.context)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatWidget(QWidget):
    """Main chat interface."""
    data_changed = Signal()

    def __init__(self, db: DatabaseManager, ai: AIEngine, parent=None):
        super().__init__(parent)
        self.db = db
        self.ai = ai
        self.worker = None
        self.typing_indicator = None
        self._last_user_message = ""
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("ChatWidget { background: transparent; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat header with Coraline hero-style branding
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(22, 181, 179, 0.15),
                    stop:0.5 rgba(233, 30, 140, 0.1),
                    stop:1 transparent);
                border: none;
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 16, 0, 12)
        header_layout.setSpacing(2)

        # Sparkle decoration
        sparkle = QLabel("\u2726 \u2727 \u2726")
        sparkle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sparkle.setStyleSheet(f"color: {COLORS['pink']}; font-size: 14px; background: transparent;")
        header_layout.addWidget(sparkle)

        # Cat avatar with glow
        avatar_container = QHBoxLayout()
        avatar_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cat_avatar = GlowingAvatar()
        avatar_container.addWidget(self.cat_avatar)
        header_layout.addLayout(avatar_container)

        # Bot name with neon glow look
        bot_name = QLabel("\u2728 Diday the Cat \u2728")
        bot_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        bot_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_name.setStyleSheet(f"color: {COLORS['magic_glow']}; background: transparent; letter-spacing: 2px;")
        header_layout.addWidget(bot_name)

        layout.addWidget(header_frame)

        # Quick action chips
        chips_layout = QHBoxLayout()
        chips_layout.setContentsMargins(16, 10, 16, 6)
        chips_layout.setSpacing(8)

        for text, msg in [
            ("Today's Summary", "How much did I spend today?"),
            ("Budget Check", "Check my budget status"),
            ("Loan Status", "What's my loan status?"),
            ("Income Summary", "Show my income summary"),
            ("Savings Advice", "How are my savings looking?"),
        ]:
            chip = QPushButton(text)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['accent']}22, stop:1 {COLORS['pink']}15);
                    color: {COLORS['magic_glow']};
                    border: none;
                    border-radius: 16px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['accent']}44, stop:1 {COLORS['pink']}33);
                    border: none;
                    color: white;
                }}
            """)
            chip.clicked.connect(lambda checked, m=msg: self._send_quick(m))
            chips_layout.addWidget(chip)

        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        # Chat messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(2)

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, 1)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("chatInput")
        self.input_field.setPlaceholderText('Type a message... (e.g., "spent 50 on grab")')
        self.input_field.setMinimumHeight(44)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("\u27a4")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setFixedSize(44, 44)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_frame)

    def _load_history(self):
        """Load chat history from database."""
        messages = self.db.get_chat_history(limit=50)
        for msg in messages:
            ts = ""
            if msg.get("timestamp"):
                try:
                    dt = datetime.strptime(msg["timestamp"], "%Y-%m-%d %H:%M:%S")
                    ts = dt.strftime("%I:%M %p")
                except ValueError:
                    ts = ""
            bubble = MessageBubble(msg["message"], msg["role"], ts)
            self.messages_layout.addWidget(bubble)

        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _send_quick(self, message: str):
        """Send a quick action message."""
        self.input_field.setText(message)
        self.send_message()

    def send_message(self):
        """Send user message to AI."""
        text = self.input_field.text().strip()
        if not text or self.worker is not None:
            return

        self._last_user_message = text
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        # Display user message
        now = now_ph().strftime("%I:%M %p")
        bubble = MessageBubble(text, "user", now)
        self.messages_layout.addWidget(bubble)

        # Show typing indicator
        self.typing_indicator = TypingIndicator()
        self.messages_layout.addWidget(self.typing_indicator)
        self._scroll_to_bottom()

        # Build context
        context = self._build_context()

        # Start AI worker
        self.worker = AIWorker(self.ai, text, context)
        self.worker.response_ready.connect(self._handle_response)
        self.worker.error_occurred.connect(self._handle_error)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _build_context(self) -> dict:
        """Build context for AI engine."""
        today = today_str()
        month = current_month_year()
        year, mo = month.split("-")
        start = f"{month}-01"
        if int(mo) == 12:
            end = f"{int(year)+1}-01-01"
        else:
            end = f"{year}-{int(mo)+1:02d}-01"
        from datetime import timedelta
        end_date = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        return {
            "recent_expenses": self.db.get_expenses(limit=15),
            "active_loans": self.db.get_loans(status="active"),
            "budgets": self.db.get_budgets(month),
            "chat_history": self.db.get_chat_history(limit=10),
            "recent_income": self.db.get_income(limit=10),
            "monthly_income_total": self.db.get_total_income(start, end_date),
            "monthly_spending_total": self.db.get_total_spent(start, end_date),
            "username": self.db.get_setting("username") or "hooman",
        }

    def _handle_response(self, response: dict):
        """Process AI response: execute action and display message."""
        # Remove typing indicator
        if self.typing_indicator:
            self.messages_layout.removeWidget(self.typing_indicator)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None

        # Execute action
        action = response.get("action", {})
        action_result = self._execute_action(action)

        # Display message
        message = response.get("message", "Done!")

        # If action_result has extra info, append it
        if action_result and action_result.get("extra_message"):
            message += "\n" + action_result["extra_message"]

        now = now_ph().strftime("%I:%M %p")
        bubble = MessageBubble(message, "assistant", now)
        self.messages_layout.addWidget(bubble)
        self._scroll_to_bottom()

        # Save to chat history
        self.db.add_chat_message("user", self._last_user_message)
        self.db.add_chat_message(
            "assistant", message,
            action_type=action.get("type"),
            action_data=json.dumps(action.get("data")) if action.get("data") else None,
        )

        # Signal data change
        if action.get("type") in ("expense_add", "expense_delete", "expense_edit",
                                   "loan_add", "loan_payment", "loan_delete",
                                   "budget_set",
                                   "income_add", "income_edit", "income_delete",
                                   "rename_expense", "rename_category", "rename_loan"):
            self.data_changed.emit()

    def _handle_error(self, error: str):
        """Handle AI error."""
        if self.typing_indicator:
            self.messages_layout.removeWidget(self.typing_indicator)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None

        now = now_ph().strftime("%I:%M %p")
        bubble = MessageBubble(f"Error: {error}", "assistant", now)
        self.messages_layout.addWidget(bubble)
        self._scroll_to_bottom()

    def _worker_finished(self):
        """Re-enable input after worker finishes."""
        self.worker = None
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def _execute_action(self, action: dict) -> dict | None:
        """Execute a database action based on AI response."""
        action_type = action.get("type", "none")
        data = action.get("data", {})

        if not data or action_type == "none":
            return None

        try:
            if action_type == "expense_add":
                category_name = data.get("category", "Other")
                category_id = self.db.get_category_id(category_name)
                self.db.add_expense(
                    amount=float(data.get("amount", 0)),
                    category_id=category_id,
                    description=data.get("description", ""),
                    date=data.get("date", today_str()),
                    merchant=data.get("merchant"),
                )
                return {"success": True}

            elif action_type == "expense_delete":
                results = self.db.search_expenses(
                    description_like=data.get("search_description"),
                    amount=data.get("search_amount"),
                    date=data.get("search_date"),
                    limit=5,
                )
                if len(results) == 1:
                    self.db.delete_expense(results[0]["id"])
                    return {"success": True}
                elif len(results) > 1:
                    return {
                        "extra_message": f"Found {len(results)} matching expenses. "
                        "Please be more specific about which one to remove."
                    }
                else:
                    return {"extra_message": "No matching expense found."}

            elif action_type == "expense_edit":
                results = self.db.search_expenses(
                    description_like=data.get("search_description"),
                    limit=5,
                )
                if results:
                    updates = data.get("updates", {})
                    if "category" in updates:
                        updates["category_id"] = self.db.get_category_id(updates.pop("category"))
                    self.db.update_expense(results[0]["id"], **updates)
                    return {"success": True}

            elif action_type == "loan_add":
                self.db.add_loan(
                    platform=data.get("platform", "Unknown"),
                    amount_borrowed=float(data.get("amount_borrowed", 0)),
                    date=data.get("date", today_str()),
                    due_date=data.get("due_date"),
                )
                return {"success": True}

            elif action_type == "loan_payment":
                loan = self.db.find_loan_by_platform(data.get("platform", ""))
                if loan:
                    self.db.add_loan_payment(
                        loan_id=loan["id"],
                        amount=float(data.get("amount", 0)),
                        date=data.get("date", today_str()),
                    )
                    return {"success": True}
                else:
                    return {
                        "extra_message": f"No active loan found for '{data.get('platform')}'."
                    }

            elif action_type == "loan_delete":
                platform = data.get("platform", "")
                loan = self.db.find_loan_by_platform(platform)
                if loan:
                    with self.db._lock:
                        self.db.conn.execute("DELETE FROM loans WHERE id = ?", (loan["id"],))
                        self.db.conn.commit()
                    return {"success": True}
                else:
                    return {"extra_message": f"No active loan found for '{platform}'."}

            elif action_type == "budget_set":
                category_name = data.get("category", "Other")
                category_id = self.db.get_category_id(category_name)
                self.db.set_budget(
                    category_id=category_id,
                    monthly_limit=float(data.get("monthly_limit", 0)),
                    month_year=current_month_year(),
                )
                return {"success": True}

            # --- New action types ---
            elif action_type == "income_add":
                self.db.add_income(
                    amount=float(data.get("amount", 0)),
                    source=data.get("source", "Unknown"),
                    date=data.get("date", today_str()),
                    description=data.get("description"),
                    is_recurring=data.get("is_recurring", False),
                    notes=data.get("notes"),
                )
                return {"success": True}

            elif action_type == "income_edit":
                results = self.db.search_income(
                    source_like=data.get("search_source"),
                    limit=5,
                )
                if results:
                    updates = data.get("updates", {})
                    self.db.update_income(results[0]["id"], **updates)
                    return {"success": True}
                else:
                    return {"extra_message": "No matching income found."}

            elif action_type == "income_delete":
                results = self.db.search_income(
                    source_like=data.get("search_source"),
                    amount=data.get("search_amount"),
                    date=data.get("search_date"),
                    limit=5,
                )
                if len(results) == 1:
                    self.db.delete_income(results[0]["id"])
                    return {"success": True}
                elif len(results) > 1:
                    return {
                        "extra_message": f"Found {len(results)} matching income entries. "
                        "Please be more specific."
                    }
                else:
                    return {"extra_message": "No matching income found."}

            elif action_type == "rename_expense":
                old = data.get("old_name", "")
                new = data.get("new_name", "")
                count = self.db.rename_expense(old, new)
                if count > 0:
                    return {"success": True, "extra_message": f"Renamed {count} expense(s)."}
                else:
                    return {"extra_message": f"No expenses found matching '{old}'."}

            elif action_type == "rename_category":
                old = data.get("old_name", "")
                new = data.get("new_name", "")
                if self.db.rename_category(old, new):
                    return {"success": True}
                else:
                    return {"extra_message": f"Category '{old}' not found."}

            elif action_type == "rename_loan":
                old = data.get("old_name", "")
                new = data.get("new_name", "")
                count = self.db.rename_loan_platform(old, new)
                if count > 0:
                    return {"success": True, "extra_message": f"Renamed {count} loan(s)."}
                else:
                    return {"extra_message": f"No loans found matching '{old}'."}

        except Exception as e:
            return {"extra_message": f"Action failed: {str(e)}"}

        return None

    def _scroll_to_bottom(self):
        """Scroll chat to the bottom."""
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
