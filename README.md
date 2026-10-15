# Dado — Your Budget Saver

A private desktop budget tracker for Windows. You talk to it in plain language
("spent 250 on lunch", "paid 2000 on my loan") and it records the expense,
updates your budgets and shows where the money went.

Everything stays on your own computer, in an encrypted database.

## Features

- **Chat-style input**: a built-in keyword parser turns everyday sentences into expenses,
  income, loan payments and budget changes, with fuzzy category matching for typos
- **Dashboard**: summary cards plus matplotlib charts by category and over time
- **Loans**: track what you owe and every payment against it
- **History**: search, edit and delete past entries
- **Export**: PDF reports (ReportLab) and CSV
- **Backups**: automatic encrypted backups
- **Tray icon** and single-instance launch

## Security

- Login password is hashed with **bcrypt**
- The database key comes from the password through **PBKDF2**, and the SQLite file
  is encrypted at rest with **Fernet** (AES-128 + HMAC)
- The database is decrypted to a temporary file only while the app is open,
  then re-encrypted on save and close

## Tech stack

Python 3.11 · PySide6 (Qt) · SQLite · cryptography · bcrypt · matplotlib · ReportLab · thefuzz

## Project layout

```
main.py            entry point: single-instance check, login, app start
core/
  database.py      7 tables: settings, categories, expenses, loans,
                   loan_payments, budgets, chat_history
  security.py      bcrypt, PBKDF2 and Fernet helpers
  offline_parser.py  natural-language parser for chat input
  ai_engine.py     message router (an optional Claude API mode is planned)
  export.py        PDF and CSV export
  backup.py        encrypted backups
ui/                PySide6 windows and widgets (chat, dashboard, loans, history, settings)
utils/             constants and helpers
```

## Run it

```bash
pip install -r requirements.txt
python main.py
```

The first launch opens a setup wizard where you create your password.
Your data is written to `data/` (ignored by git).

## Build a Windows .exe

```bash
pip install pyinstaller
pyinstaller dado.spec
```

`installer.iss` builds an installer with Inno Setup.

## Author

Alexander III Empleo
