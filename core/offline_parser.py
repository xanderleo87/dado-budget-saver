"""Offline keyword-based message parser — Diday's brain, no API needed."""

import re
import random
from datetime import datetime, timedelta
from utils.helpers import today_str, now_ph

# --- Category detection from keywords ---
CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "jollibee", "mcdo", "mcdonald", "kfc", "chowking", "mang inasal",
        "greenwich", "pizza", "burger", "food", "kain", "ulam", "lunch",
        "dinner", "breakfast", "snack", "eat", "ate", "meal", "rice",
        "coffee", "starbucks", "milktea", "milk tea", "samgyup", "ramen",
        "siomai", "sisig", "adobo", "restaurant", "karinderya", "merienda",
        "lechon", "pares", "tapsi", "tapsilog", "longganisa", "taho",
        "fishball", "kwek kwek", "isaw", "balut", "bibingka",
    ],
    "Transport": [
        "grab", "angkas", "jeep", "jeepney", "pamasahe", "fare", "taxi",
        "bus", "mrt", "lrt", "tricycle", "gas", "gasoline", "fuel", "diesel",
        "parking", "toll", "uber", "commute", "transpo", "sakay",
    ],
    "Communication": [
        "globe", "smart", "tnt", "tm", "dito", "load", "data", "wifi",
        "internet", "pldt", "converge", "sim", "prepaid", "postpaid",
    ],
    "Shopping": [
        "shopee", "lazada", "sm", "mall", "uniqlo", "zalora", "shein",
        "clothes", "shoes", "bag", "damit", "bili", "bought", "shop",
        "tshirt", "dress", "jacket", "accessories",
    ],
    "Utilities": [
        "meralco", "water", "electric", "kuryente", "tubig", "maynilad",
        "manila water", "bill", "utility",
    ],
    "Entertainment": [
        "netflix", "spotify", "movie", "cinema", "game", "gaming", "xbox",
        "ps5", "steam", "youtube", "premium", "concert", "gala", "outing",
        "karaoke", "videoke", "libreng", "libre",
    ],
    "Health": [
        "medicine", "gamot", "doctor", "clinic", "hospital", "pharmacy",
        "mercury", "watsons", "checkup", "dental", "vitamins", "supplement",
    ],
    "Education": [
        "tuition", "school", "book", "course", "seminar", "training",
        "review", "exam", "class", "notebook", "pen", "paper",
    ],
    "Housing": [
        "rent", "upa", "condo", "apartment", "dorm", "mortgage", "boarding",
    ],
    "Groceries": [
        "grocery", "palengke", "market", "puregold", "savemore", "robinsons",
        "s&r", "landers", "metro mart",
    ],
    "Personal": [
        "salon", "barber", "gupit", "haircut", "skincare", "gym",
        "shampoo", "soap", "conditioner", "toothpaste", "lotion",
        "deodorant", "makeup", "cosmetics", "perfume", "laundry",
        "parlor",
    ],
}

# --- Loan platform normalization ---
LOAN_PLATFORMS = {
    "billease": "Billease", "tala": "Tala", "cashalo": "Cashalo",
    "tonik": "Tonik", "maya": "Maya", "gcash": "GCash",
    "cimb": "CIMB", "uno": "UNO Digital Bank", "revi": "Revi",
    "home credit": "Home Credit", "sss": "SSS", "pagibig": "Pag-IBIG",
}

# --- Diday cat responses (use {name} for the user's name) ---
GREETING_RESPONSES = [
    "Meow~! Hi {name}! I'm Diday, your budget cat! What did you spend today? nya~",
    "Nya~ Hey {name}! Ready to track your pera? Tell me about your expenses, income, or loans!",
    "PURRRR~ Hello {name}! Your favorite budget cat is here! What's up? Type 'help' if you need a guide!",
    "Meow meow {name}! *stretches* I'm awake and ready to guard your wallet! nya~",
]

EXPENSE_RESPONSES = [
    "Meow! Noted that expense, {name}. {amount} on {cat}... I'm watching you! nya~",
    "Hiss... another {amount} gone on {cat}. Your wallet is getting thinner, {name}!",
    "Nya~ logged {amount} for {cat}. Don't make this a habit, okay {name}?",
    "*scribbles in cat notebook* {amount} on {cat}. I hope this was necessary, {name}!",
    "Purr... fine, I logged {amount} on {cat}. But I'm keeping score! nya~",
]

INCOME_RESPONSES = [
    "PURRRR! {amount} came in from {src}! Now DON'T spend it all, {name}! nya~",
    "Meow meow! {amount} from {src}! Time to save, not splurge! I'm watching!",
    "Nya~ {amount} from {src}! Your wallet is happy and so am I! Now guard it, {name}!",
]

LOAN_ADD_RESPONSES = [
    "Hiss! Another loan?! {amount} from {plat}... {name}, utang is not income! nya~",
    "Meow... {amount} borrowed from {plat}. I logged it but I'm NOT happy about it!",
    "*sad cat noises* {amount} from {plat}. Please pay this back soon, {name}!",
]

LOAN_PAYMENT_RESPONSES = [
    "PURRRR! Paying {amount} to {plat}! Good job {name}! Keep going! nya~",
    "Meow! {amount} paid to {plat}! Responsible {name} gets head pats!",
    "Nya~ {amount} to {plat}! One step closer to being debt-free! I'm so proud!",
]

BUDGET_RESPONSES = [
    "Nya~ Budget set! {amount} for {cat} this month. I'll scold you if you go over!",
    "Meow! {cat} budget is now {amount}. Cross the line and you'll hear from me, {name}!",
]

QUERY_RESPONSES = [
    "Nya~ let me check my records for you, {name}!",
    "Meow! Here's what I found in my cat ledger!",
]

DELETE_RESPONSES = [
    "Meow! Done, {name}! I deleted that {what} for you. *shreds paper*",
    "Nya~ Poof! That {what} is gone! *bats it off the table*",
]

CONFUSED_RESPONSES = [
    "Nya? I didn't quite get that, {name}. Try: 'spent 100 on food' or 'sahod 25000'. Type 'help' for a guide!",
    "Meow? Sorry {name}, I can't parse that. Try: 'gastos 50 sa grab' or 'loan 1000 billease'. Type 'help'!",
    "Hiss? Tell me about expenses, income, or loans! Type 'help' to see all keywords I understand! nya~",
]


def _detect_category(text: str) -> str:
    """Auto-detect expense category from message text."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return "Other"


def _detect_merchant(text: str) -> str:
    """Try to detect a merchant name from the text."""
    merchants = [
        "jollibee", "mcdo", "mcdonald's", "kfc", "chowking", "mang inasal",
        "greenwich", "starbucks", "grab", "angkas", "shopee", "lazada",
        "meralco", "globe", "smart", "pldt", "converge", "netflix", "spotify",
        "sm", "uniqlo", "puregold", "savemore", "mercury", "watsons",
    ]
    text_lower = text.lower()
    for m in merchants:
        if m in text_lower:
            return m.title()
    return ""


def _normalize_platform(text: str) -> str:
    """Normalize loan platform name."""
    text_lower = text.lower().strip()
    for key, name in LOAN_PLATFORMS.items():
        if key in text_lower:
            return name
    # Return capitalized original if no match
    return text.strip().title() if text.strip() else "Unknown"


def _parse_date(text: str) -> str:
    """Parse date references from message text, default to today."""
    text_lower = text.lower()
    today = now_ph()

    if "yesterday" in text_lower or "kahapon" in text_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    m = re.search(r'(\d+)\s+days?\s+ago', text_lower)
    if m:
        return (today - timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

    return today_str()


def _extract_amount(text: str) -> float | None:
    """Extract a numeric amount from text, supporting 'k' shorthand."""
    # Handle "5k", "1.5k", "10k" patterns first
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text.lower())
    if k_match:
        return float(k_match.group(1)) * 1000

    # Find all number-like tokens
    numbers = re.findall(r'(?:[\u20b1\$]\s*)?([\d,]+(?:\.\d{1,2})?)', text)
    for n in numbers:
        val = float(n.replace(",", ""))
        if val > 0:
            return val
    return None


def _fmt(amount: float) -> str:
    """Format amount for display."""
    return f"\u20b1{amount:,.2f}"


def _preprocess(text: str) -> str:
    """Clean up message text before pattern matching."""
    text = text.strip()
    # Strip common filler prefixes (case-insensitive)
    text = re.sub(r'^(?:i\s+just\s+|just\s+|i\s+)', '', text, flags=re.IGNORECASE).strip()
    return text


HELP_MESSAGE = """Nya~ Here's how to talk to me, {name}! I understand these keywords:

EXPENSES:
  - "spent 120 on food"
  - "spend 644 on shampoo"
  - "gastos 50 sa grab"
  - "bought coffee 80"
  - "kain sa jollibee 150"
  - "jollibee 150" (shortcut!)
  - "120 food" (amount + item)

INCOME:
  - "earned 25000 salary"
  - "sahod 25k" / "sweldo 25000"
  - "got paid 15000 freelance"
  - "income 5000 bonus"
  - "allowance 3000"

LOANS (add):
  - "loan 1400 to shai"
  - "loaned 1000 in billease"
  - "lent 500 to my friend"
  - "utang 5k sa tala"
  - "borrowed 2000 from gcash"

LOAN PAYMENTS:
  - "paid 500 to billease"
  - "bayad 1000 sa tala"
  - "payment 500 gcash"

BUDGETS:
  - "budget 5000 for food"
  - "set budget 3000 for transport"

DELETE:
  - "delete expense lunch"
  - "delete loan billease"
  - "delete income freelance"
  - "remove expense grab"

QUERIES:
  - "how much did I spend"
  - "total spent today/this week"
  - "loan status"
  - "budget status"
  - "income summary"

DATES:
  - "yesterday" / "kahapon"
  - "3 days ago"
  - (defaults to today if no date)

SHORTCUTS:
  - "k" = thousand (5k = 5,000)

Type any of these and I'll track it for you! nya~"""


def parse_message(user_message: str, username: str = "hooman") -> dict:
    """Parse a user message into a structured action response.

    Returns dict with 'message' and 'action' keys.
    """
    raw_text = user_message.strip()
    text = _preprocess(raw_text)
    text_lower = text.lower()
    raw_lower = raw_text.lower().strip()
    amount = _extract_amount(text)
    date = _parse_date(text)
    name = username

    # --- HELP: show keyword guide ---
    help_keywords = ["help", "tulong", "guide", "how to", "commands", "keywords",
                     "what can you do", "how do i", "paano"]
    if any(raw_lower == kw or raw_lower.startswith(kw) for kw in help_keywords):
        return {
            "message": HELP_MESSAGE.format(name=name),
            "action": {"type": "none", "data": {}},
        }

    # --- GREETINGS ---
    greeting_keywords = ["hello", "hi", "hey", "yo", "hoy", "uy", "kamusta",
                         "kumusta", "good morning", "good afternoon", "good evening",
                         "magandang umaga", "magandang hapon", "magandang gabi",
                         "what's up", "sup", "musta"]
    if any(raw_lower == kw or raw_lower.startswith(kw + " ") or raw_lower.startswith(kw + "!") for kw in greeting_keywords):
        return {
            "message": random.choice(GREETING_RESPONSES).format(name=name),
            "action": {"type": "none", "data": {}},
        }

    # --- DELETE: "delete expense/loan/income X" ---
    delete_match = re.match(
        r'(?:delete|remove|tanggal|bura)\s+(expense|loan|income|gastos|utang)\s+(.+)',
        text_lower
    )
    if delete_match:
        what_type = delete_match.group(1)
        search_term = delete_match.group(2).strip()

        if what_type in ("expense", "gastos"):
            msg = random.choice(DELETE_RESPONSES).format(name=name, what="expense")
            return {
                "message": msg,
                "action": {
                    "type": "expense_delete",
                    "data": {"search_description": search_term, "search_date": None, "search_amount": None},
                },
            }
        elif what_type in ("loan", "utang"):
            msg = random.choice(DELETE_RESPONSES).format(name=name, what="loan")
            return {
                "message": msg,
                "action": {
                    "type": "loan_delete",
                    "data": {"platform": _normalize_platform(search_term)},
                },
            }
        elif what_type == "income":
            msg = random.choice(DELETE_RESPONSES).format(name=name, what="income")
            return {
                "message": msg,
                "action": {
                    "type": "income_delete",
                    "data": {"search_source": search_term, "search_amount": None, "search_date": None},
                },
            }

    # --- LOAN PAYMENT: "paid X to Y" / "bayad X sa Y" ---
    loan_pay_patterns = [
        r'(?:paid|bayad|payment|hulog|nagbayad|naghulog)\s+.*?(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*(?:to|sa|for|kay)\s+(.+)',
        r'(?:paid|bayad|payment|hulog|nagbayad|naghulog)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s+(.+)',
    ]
    for pat in loan_pay_patterns:
        m = re.search(pat, text_lower)
        if m:
            raw_amt = m.group(1).replace(",", "")
            pay_amount = float(raw_amt)
            # Check if "k" follows the number
            after_num = text_lower[m.end(1):]
            if after_num.lstrip().startswith("k"):
                pay_amount *= 1000
            platform = _normalize_platform(m.group(2))
            msg = random.choice(LOAN_PAYMENT_RESPONSES).format(
                amount=_fmt(pay_amount), plat=platform, name=name
            )
            return {
                "message": msg,
                "action": {
                    "type": "loan_payment",
                    "data": {
                        "platform": platform,
                        "amount": pay_amount,
                        "date": date,
                    },
                },
            }

    # --- LOAN ADD: flexible patterns ---
    _loan_kw = r'(?:loan(?:ed)?|lent|lend|utang|borrow(?:ed)?|hiram|umutang|pinahiram|nag\s*loan|nag\s*utang|gave)'
    loan_patterns = [
        _loan_kw + r'\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*(?:to|from|sa|kay|in|para\s+sa|para\s+kay)\s+(.+)',
        _loan_kw + r'\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s+(.+)',
    ]
    for pat in loan_patterns:
        m = re.search(pat, text_lower)
        if m:
            raw_amt = m.group(1).replace(",", "")
            loan_amount = float(raw_amt)
            after_num = text_lower[m.end(1):]
            if after_num.lstrip().startswith("k"):
                loan_amount *= 1000
            raw_target = m.group(2).strip()
            # Clean up filler words
            cleaned = re.sub(
                r'^(?:my\s+)?(?:workmate|friend|kaibigan|officemate|classmate|ka\s*work|tropa|barkada|colleague)?\s*(?:named?|na\s+si|si|na)?\s*',
                '', raw_target
            ).strip()
            platform = _normalize_platform(cleaned) if cleaned else _normalize_platform(raw_target)
            msg = random.choice(LOAN_ADD_RESPONSES).format(
                amount=_fmt(loan_amount), plat=platform, name=name
            )
            return {
                "message": msg,
                "action": {
                    "type": "loan_add",
                    "data": {
                        "platform": platform,
                        "amount_borrowed": loan_amount,
                        "date": date,
                        "due_date": None,
                    },
                },
            }

    # --- INCOME: "earned/sahod/sweldo/got paid X" ---
    income_patterns = [
        r'(?:earned?|sahod|sweldo|income|salary|received|got\s+paid|kinita|suweldo|allowance|commission|bonus|sideline|freelance)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*(.*)',
        r'(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s+(?:sahod|sweldo|salary|income|allowance)',
    ]
    for pat in income_patterns:
        m = re.search(pat, text_lower)
        if m:
            raw_amt = m.group(1).replace(",", "")
            inc_amount = float(raw_amt)
            after_num = text_lower[m.end(1):]
            if after_num.lstrip().startswith("k"):
                inc_amount *= 1000
            rest = m.group(2).strip() if m.lastindex >= 2 else ""
            # Detect source
            source = "Salary"
            source_keywords = {
                "salary": "Salary", "sahod": "Salary", "sweldo": "Salary",
                "suweldo": "Salary", "freelance": "Freelance", "bonus": "Bonus",
                "sideline": "Sideline", "allowance": "Allowance",
                "commission": "Commission", "income": "Income",
            }
            for kw, src in source_keywords.items():
                if kw in text_lower:
                    source = src
                    break

            description = rest if rest else f"{source.lower()} income"
            description = re.sub(r'^(?:from|for|sa|as|para)\s+', '', description).strip()
            if not description:
                description = f"{source.lower()} income"

            msg = random.choice(INCOME_RESPONSES).format(
                amount=_fmt(inc_amount), src=source, name=name
            )
            return {
                "message": msg,
                "action": {
                    "type": "income_add",
                    "data": {
                        "amount": inc_amount,
                        "source": source,
                        "description": description,
                        "date": date,
                        "is_recurring": source == "Salary",
                    },
                },
            }

    # --- BUDGET: "set budget X for Y" / "budget Y X" ---
    budget_patterns = [
        r'(?:set\s+)?budget\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*(?:for|sa|on)\s+(.+)',
        r'(?:set\s+)?budget\s+(.+?)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?',
    ]
    for i, pat in enumerate(budget_patterns):
        m = re.search(pat, text_lower)
        if m:
            if i == 0:
                raw_amt = m.group(1).replace(",", "")
                budget_amount = float(raw_amt)
                after_num = text_lower[m.end(1):]
                if after_num.lstrip().startswith("k"):
                    budget_amount *= 1000
                cat_text = m.group(2).strip()
            else:
                cat_text = m.group(1).strip()
                raw_amt = m.group(2).replace(",", "")
                budget_amount = float(raw_amt)
                after_num = text_lower[m.end(2):]
                if after_num.lstrip().startswith("k"):
                    budget_amount *= 1000
            category = _detect_category(cat_text)
            if category == "Other":
                for cat_name in CATEGORY_KEYWORDS:
                    if cat_text.lower() in cat_name.lower() or cat_name.lower() in cat_text.lower():
                        category = cat_name
                        break
            msg = random.choice(BUDGET_RESPONSES).format(
                amount=_fmt(budget_amount), cat=category, name=name
            )
            return {
                "message": msg,
                "action": {
                    "type": "budget_set",
                    "data": {
                        "category": category,
                        "monthly_limit": budget_amount,
                    },
                },
            }

    # --- QUERY: "how much", "total", "summary", "status" ---
    query_keywords = [
        "how much", "total", "summary", "status", "magkano", "spent",
        "breakdown", "report", "history", "loan status", "budget status",
    ]
    if any(kw in text_lower for kw in query_keywords) and amount is None:
        query_type = "total_spent"
        if "loan" in text_lower:
            query_type = "loan_status"
        elif "budget" in text_lower:
            query_type = "budget_status"
        elif "income" in text_lower or "sahod" in text_lower:
            query_type = "income_summary"
        elif "breakdown" in text_lower or "category" in text_lower:
            query_type = "category_breakdown"
        elif "recent" in text_lower or "history" in text_lower:
            query_type = "recent_expenses"

        period = "this_month"
        if "today" in text_lower:
            period = "today"
        elif "week" in text_lower:
            period = "this_week"
        elif "last month" in text_lower:
            period = "last_month"

        msg = random.choice(QUERY_RESPONSES).format(name=name)
        return {
            "message": msg,
            "action": {
                "type": "query",
                "data": {
                    "query_type": query_type,
                    "period": period,
                },
            },
        }

    # --- EXPENSE: many patterns, most flexible ---
    expense_patterns = [
        # "spent/spend/gastos 120 on/to/sa food"
        (r'(?:spent?|spending|gastos?|nagastos?|binili|bought|buy|buying|bumili)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*(?:on|to|sa|for|at|kay)\s+(.+)', 'amt_first'),
        # "bought/gastos coffee 80"
        (r'(?:spent?|spending|gastos?|bought|buy|buying|binili|bumili)\s+(.+?)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*$', 'desc_first'),
        # "ate at jollibee 150" / "kain sa jollibee 150"
        (r'(?:ate|kain|kumain|nag\s*kain)\s+(?:at|sa)?\s*(.+?)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*$', 'desc_first'),
        # "jollibee 150" / "grab 50" (merchant + amount, short form)
        (r'^(\w[\w\s]*?)\s+(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s*$', 'desc_first'),
        # "120 food" / "50 grab" (amount + description)
        (r'^(\d[\d,]*(?:\.\d{1,2})?)\s*k?\s+(?:on|sa|for|to)?\s*(.+)', 'amt_first'),
    ]

    for pat, mode in expense_patterns:
        m = re.search(pat, text_lower)
        if m:
            if mode == 'amt_first':
                raw_amt = m.group(1).replace(",", "")
                exp_amount = float(raw_amt)
                after_num = text_lower[m.end(1):]
                if after_num.lstrip().startswith("k"):
                    exp_amount *= 1000
                desc = m.group(2).strip()
            else:
                desc = m.group(1).strip()
                raw_amt = m.group(2).replace(",", "")
                exp_amount = float(raw_amt)
                after_num = text_lower[m.end(2):]
                if after_num.lstrip().startswith("k"):
                    exp_amount *= 1000

            if exp_amount <= 0:
                continue

            category = _detect_category(desc)
            merchant = _detect_merchant(desc)
            msg = random.choice(EXPENSE_RESPONSES).format(
                amount=_fmt(exp_amount), cat=category, name=name
            )
            return {
                "message": msg,
                "action": {
                    "type": "expense_add",
                    "data": {
                        "amount": exp_amount,
                        "category": category,
                        "merchant": merchant,
                        "description": desc,
                        "date": date,
                    },
                },
            }

    # --- FALLBACK: confused cat ---
    return {
        "message": random.choice(CONFUSED_RESPONSES).format(name=name),
        "action": {"type": "none", "data": {}},
    }
