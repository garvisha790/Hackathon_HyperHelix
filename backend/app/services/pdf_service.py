"""Generate professional ledger PDF reports with Taxodo branding."""
import io
from datetime import date, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# ── Taxodo brand palette ──────────────────────────────────────────
TAXODO_PRIMARY = colors.HexColor("#0d9488")      # teal-600
TAXODO_PRIMARY_DARK = colors.HexColor("#0f766e")  # teal-700
TAXODO_INK = colors.HexColor("#1a2332")
TAXODO_MUTED = colors.HexColor("#6b7280")
TAXODO_SUBTLE = colors.HexColor("#f0fdfa")        # teal-50
TAXODO_BORDER = colors.HexColor("#d1d5db")
TAXODO_ZEBRA = colors.HexColor("#f8fafc")
TAXODO_TOTAL_BG = colors.HexColor("#ccfbf1")      # teal-100
WHITE = colors.white


def _fmt_currency(val: float) -> str:
    """Indian comma grouping for currency."""
    if val == 0:
        return ""
    val = round(val, 2)
    s = f"{val:,.2f}"
    parts = s.split(".")
    integer = parts[0].replace(",", "")
    is_neg = integer.startswith("-")
    if is_neg:
        integer = integer[1:]
    if len(integer) <= 3:
        grouped = integer
    else:
        grouped = integer[-3:]
        integer = integer[:-3]
        while integer:
            grouped = integer[-2:] + "," + grouped
            integer = integer[:-2]
    result = f"{grouped}.{parts[1]}"
    return f"-₹{result}" if is_neg else f"₹{result}"


def generate_ledger_pdf(
    company_name: str,
    gstin: str | None,
    transactions: list[dict],
    date_from: date | None = None,
    date_to: date | None = None,
) -> bytes:
    """Generate a professional Taxodo-branded ledger PDF and return bytes."""
    buf = io.BytesIO()
    page_size = landscape(A4)  # landscape for wider description column
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        topMargin=18 * mm,
        bottomMargin=12 * mm,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ─────────────────────────────────────────────
    brand_style = ParagraphStyle(
        "Brand", parent=styles["Normal"],
        fontSize=11, textColor=TAXODO_PRIMARY_DARK,
        alignment=TA_CENTER, spaceAfter=1,
        fontName="Helvetica-Bold",
    )
    company_style = ParagraphStyle(
        "Company", parent=styles["Heading1"],
        fontSize=18, textColor=TAXODO_INK,
        alignment=TA_CENTER, spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    info_style = ParagraphStyle(
        "Info", parent=styles["Normal"],
        fontSize=10, textColor=TAXODO_MUTED,
        alignment=TA_CENTER, spaceAfter=1,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=7.5, textColor=TAXODO_MUTED,
        alignment=TA_CENTER,
    )
    # Paragraph style for description cells (allows wrapping)
    desc_cell_style = ParagraphStyle(
        "DescCell", parent=styles["Normal"],
        fontSize=7.5, textColor=TAXODO_INK, leading=10,
    )
    acct_cell_style = ParagraphStyle(
        "AcctCell", parent=styles["Normal"],
        fontSize=7.5, textColor=TAXODO_INK, leading=10,
    )

    elements = []

    # ── Header / Branding ─────────────────────────────────────────
    elements.append(Paragraph("taxodo.ai", brand_style))
    elements.append(Spacer(1, 1 * mm))
    elements.append(Paragraph(company_name, company_style))
    if gstin:
        elements.append(Paragraph(f"GSTIN: {gstin}", info_style))
    elements.append(Spacer(1, 2 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=1.5,
        color=TAXODO_PRIMARY, spaceAfter=3 * mm, spaceBefore=1 * mm,
    ))
    elements.append(Paragraph(
        "GENERAL LEDGER — DOUBLE-ENTRY JOURNAL",
        ParagraphStyle("LedgerLabel", parent=info_style,
                       fontSize=11, fontName="Helvetica-Bold",
                       textColor=TAXODO_INK, spaceAfter=2),
    ))

    period_label = "All Transactions"
    if date_from and date_to:
        period_label = f"{date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}"
    elif date_from:
        period_label = f"From {date_from.strftime('%d %b %Y')}"
    elif date_to:
        period_label = f"Up to {date_to.strftime('%d %b %Y')}"
    elements.append(Paragraph(f"Period: {period_label}", info_style))
    elements.append(Spacer(1, 6 * mm))

    if not transactions:
        elements.append(Paragraph(
            "No transactions found for the selected period.", styles["Normal"],
        ))
        doc.build(elements)
        return buf.getvalue()

    # ── Build table data ──────────────────────────────────────────
    header = ["Date", "Description", "Account", "Debit (₹)", "Credit (₹)"]
    table_data = [header]

    grand_debit = 0.0
    grand_credit = 0.0

    for txn in transactions:
        lines = txn.get("journal_lines", [])
        if not lines:
            continue
        txn_date = txn.get("transaction_date", "")
        if isinstance(txn_date, date):
            txn_date = txn_date.strftime("%d-%m-%Y")
        desc_text = txn.get("description", "—") or "—"

        for i, jl in enumerate(lines):
            dr = float(jl.get("debit", 0))
            cr = float(jl.get("credit", 0))
            grand_debit += dr
            grand_credit += cr

            # Use Paragraph for description & account to allow word-wrap
            desc_para = Paragraph(desc_text, desc_cell_style) if i == 0 else ""
            acct_para = Paragraph(
                jl.get("account_name") or jl.get("account_code") or "—",
                acct_cell_style,
            )

            row = [
                txn_date if i == 0 else "",
                desc_para,
                acct_para,
                _fmt_currency(dr),
                _fmt_currency(cr),
            ]
            table_data.append(row)

    # Grand total row
    table_data.append([
        "", "", "GRAND TOTAL",
        _fmt_currency(grand_debit),
        _fmt_currency(grand_credit),
    ])

    # Landscape A4 usable width ≈ 273 mm (297 - 12*2 margins)
    col_widths = [22 * mm, 95 * mm, 55 * mm, 30 * mm, 30 * mm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        # Header row — Taxodo teal
        ("BACKGROUND", (0, 0), (-1, 0), TAXODO_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        # Body
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 8),
        ("TOPPADDING", (0, 1), (-1, -2), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 4),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        # Right-align amount columns
        ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        # Subtle grid
        ("GRID", (0, 0), (-1, -1), 0.4, TAXODO_BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, TAXODO_PRIMARY_DARK),
        # Total row — teal tint
        ("BACKGROUND", (0, -1), (-1, -1), TAXODO_TOTAL_BG),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 9),
        ("TEXTCOLOR", (0, -1), (-1, -1), TAXODO_INK),
        ("TOPPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, TAXODO_PRIMARY),
    ]

    # Zebra striping
    for i in range(1, len(table_data) - 1):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TAXODO_ZEBRA))

    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    # ── Footer ────────────────────────────────────────────────────
    elements.append(Spacer(1, 6 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=TAXODO_BORDER, spaceAfter=3 * mm, spaceBefore=1 * mm,
    ))
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    elements.append(Paragraph(
        f"Generated by <b>taxodo.ai</b> on {now} · This is a computer-generated document · No signature required",
        footer_style,
    ))

    doc.build(elements)
    return buf.getvalue()
