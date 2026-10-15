"""AI Engine: Offline keyword-based parser for Diday budget tracker."""

from core.offline_parser import parse_message


class AIEngine:
    """Manages message processing using offline keyword parser."""

    def __init__(self, api_key: str = ""):
        # API key kept for future use but not used in offline mode
        self._api_key = api_key
        self._has_api = False  # Always offline mode

    def process_message(self, user_message: str, context: dict) -> dict:
        """Process a user message using the offline keyword parser."""
        username = context.get("username", "hooman")
        return parse_message(user_message, username=username)
