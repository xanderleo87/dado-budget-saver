"""Export manager: CSV and PDF export."""

import csv
import os
from datetime import datetime

from core.database import DatabaseManager
from utils.helpers import format_currency, current_month_year, month_display


class ExportManager:
    """Handles CSV and PDF export of financial data."""

    def export_csv(self, db: DatabaseManager, filepath: str,
                   start_date: str = None, end_date: str = None):
        """Export expenses and loans to CSV."""
        if not start_date:
            start_date = "2000-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        expenses = db.get_expenses(start_date=start_date, end_date=end_date, limit=10000)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Description", "Merchant", "Category", "Amount"])
            for e in expenses:
                writer.writerow([
                    e.get("date", ""),
                    e.get("description", ""),
                    e.get("merchant", ""),
                    e.get("category_name", ""),
                    e.get("amount", 0),
                ])

            # Loans section
            writer.writerow([])
            writer.writerow(["--- LOANS ---"])
            writer.writerow(["Platform", "Borrowed", "Paid", "Remaining", "Status", "Date"])
            loans = db.get_loans()
            for l in loans:
                writer.writerow([
                    l.get("platform", ""),
                    l.get("amount_borrowed", 0),
                    l.get("amount_paid", 0),
                    l.get("remaining", 0),
                    l.get("status", ""),
                    l.get("date", ""),
                ])

    def export_pdf(self, db: DatabaseManager, filepath: str,
                   month_year: str = None):
        """Export a formatted PDF financial report."""
        if not month_year:
            month_year = current_month_year()

        year, mo = month_year.split("-")
        start = f"{month_year}-01"
        if int(mo) == 12:
            end_month = f"{int(year)+1}-01-01"
        else:
            end_month = f"{year}-{int(mo)+1:02d}-01"

        from datetime import timedelta
        end_date = (datetime.strptime(end_month, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            # Fallback: write a simple text file
            self._export_text_report(db, filepath, start, end_date, month_year)
            return

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Title"],
            fontSize=18, spaceAfter=20,
        )
        elements.append(Paragraph(f"Diday Financial Report", title_style))
        elements.append(Paragraph(f"{month_display(month_year)}", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        # Summary
        summary = db.get_expense_summary(start, end_date)
        total = summary["total"]
        elements.append(Paragraph(f"Total Spending: {format_currency(total)}", styles["Heading3"]))
        elements.append(Spacer(1, 8))

        # Category breakdown table
        if summary["categories"]:
            cat_data = [["Category", "Amount", "% of Total"]]
            for c in summary["categories"]:
                pct = f"{c['total']/total*100:.1f}%" if total > 0 else "0%"
                cat_data.append([c["name"], format_currency(c["total"]), pct])

            cat_table = Table(cat_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            cat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#313244")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#45475A")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.HexColor("#1E1E2E"), rl_colors.HexColor("#262637")]),
                ("TEXTCOLOR", (0, 1), (-1, -1), rl_colors.HexColor("#CDD6F4")),
            ]))
            elements.append(cat_table)
            elements.append(Spacer(1, 16))

        # Expense details
        expenses = db.get_expenses(start_date=start, end_date=end_date, limit=500)
        if expenses:
            elements.append(Paragraph("Expense Details", styles["Heading3"]))
            elements.append(Spacer(1, 8))

            exp_data = [["Date", "Description", "Category", "Amount"]]
            for e in expenses:
                exp_data.append([
                    e.get("date", ""),
                    e.get("description", "")[:40],
                    e.get("category_name", ""),
                    format_currency(e.get("amount", 0)),
                ])

            exp_table = Table(exp_data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1*inch])
            exp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#313244")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#45475A")),
                ("TEXTCOLOR", (0, 1), (-1, -1), rl_colors.HexColor("#333333")),
            ]))
            elements.append(exp_table)
            elements.append(Spacer(1, 16))

        # Loans
        loans = db.get_loans()
        if loans:
            elements.append(Paragraph("Loan Summary", styles["Heading3"]))
            elements.append(Spacer(1, 8))

            loan_data = [["Platform", "Borrowed", "Paid", "Remaining", "Status"]]
            for l in loans:
                loan_data.append([
                    l.get("platform", ""),
                    format_currency(l.get("amount_borrowed", 0)),
                    format_currency(l.get("amount_paid", 0)),
                    format_currency(l.get("remaining", 0)),
                    l.get("status", "").upper(),
                ])

            loan_table = Table(loan_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
            loan_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#313244")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#45475A")),
                ("TEXTCOLOR", (0, 1), (-1, -1), rl_colors.HexColor("#333333")),
            ]))
            elements.append(loan_table)

        # Footer
        elements.append(Spacer(1, 24))
        footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=rl_colors.gray)
        elements.append(Paragraph(
            f"Generated by Diday on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            footer_style,
        ))

        doc.build(elements)

    def _export_text_report(self, db, filepath, start, end, month_year):
        """Fallback text export if reportlab is not installed."""
        with open(filepath.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write(f"Diday Financial Report - {month_display(month_year)}\n")
            f.write("=" * 50 + "\n\n")

            summary = db.get_expense_summary(start, end)
            f.write(f"Total Spending: {format_currency(summary['total'])}\n\n")

            f.write("Category Breakdown:\n")
            for c in summary["categories"]:
                f.write(f"  {c['name']}: {format_currency(c['total'])}\n")

            f.write("\nExpenses:\n")
            for e in db.get_expenses(start_date=start, end_date=end, limit=500):
                f.write(f"  {e['date']} | {e['description']} | {format_currency(e['amount'])}\n")

            f.write("\nLoans:\n")
            for l in db.get_loans():
                f.write(f"  {l['platform']}: Borrowed {format_currency(l['amount_borrowed'])}, "
                        f"Remaining {format_currency(l['remaining'])} ({l['status']})\n")
