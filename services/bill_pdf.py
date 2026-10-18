from datetime import datetime
from html import escape
from pathlib import Path

from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

from gui.branding import LOGO_PATH


def create_bill_pdf(
    order_id,
    customer,
    employee_name,
    order_type,
    table_number,
    payment_method,
    cart,
    output_directory=None,
):
    if not cart:
        raise ValueError("Cannot generate a bill for an empty order.")
    order_id = int(order_id)

    output_directory = (
        Path(output_directory)
        if output_directory is not None
        else Path(__file__).resolve().parents[1] / "bills"
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    pdf_path = output_directory / f"MAYURICAFE_bill_{order_id}.pdf"

    customer_name = escape(str(customer.get("customer_name") or "Guest"))
    customer_phone = escape(str(customer.get("phone") or "Not provided"))
    service = escape(str(order_type).replace("_", " ").title())
    if table_number is not None:
        service += f" · Table {escape(str(table_number))}"

    item_rows = []
    total = 0
    for item in cart:
        quantity = int(item["quantity"])
        unit_price = float(item["price"])
        line_total = quantity * unit_price
        total += line_total
        item_rows.append(
            "<tr>"
            f"<td>{escape(str(item['item_name']))}</td>"
            f"<td class='center'>{quantity}</td>"
            f"<td class='number'>₹{unit_price:,.2f}</td>"
            f"<td class='number'>₹{line_total:,.2f}</td>"
            "</tr>"
        )

    issued_at = datetime.now().strftime("%d %b %Y · %I:%M %p").lstrip("0")
    html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: sans-serif; color: #2b1810; font-size: 12pt; }}
            .header {{ width: 100%; border-bottom: 2px solid #e5cba8;
                       padding-bottom: 12px; }}
            .brand-logo {{ width: 68px; height: 68px; }}
            h1 {{ color: #9f4616; font-size: 30pt; margin: 0; }}
            .tagline {{ color: #806b57; font-size: 11pt; }}
            .bill-label {{ color: #806b57; font-size: 10pt; text-align: right; }}
            .bill-id {{ color: #9f4616; font-size: 18pt; font-weight: bold;
                        text-align: right; }}
            .meta {{ width: 100%; margin-top: 22px; margin-bottom: 24px;
                     background-color: #faf6f1; }}
            .meta td {{ padding: 10px 12px; }}
            .meta-label {{ color: #806b57; font-size: 9pt; }}
            .meta-value {{ font-size: 11pt; font-weight: bold; }}
            table.items {{ width: 100%; border-collapse: collapse; }}
            .items th {{ background-color: #f4e9dc; color: #5b3929;
                         text-align: left; padding: 12px 9px; font-size: 10pt; }}
            .items td {{ padding: 14px 9px; border-bottom: 1px solid #eee5db; }}
            .center {{ text-align: center; }}
            .number {{ text-align: right; }}
            .total-box {{ margin-top: 20px; padding: 14px;
                          background-color: #fbf3e9; text-align: right; }}
            .total-label {{ font-size: 11pt; font-weight: bold; }}
            .total-value {{ font-size: 20pt; font-weight: bold; color: #9f4616; }}
            .footer {{ margin-top: 34px; padding-top: 14px;
                       border-top: 1px solid #e5cba8; text-align: center;
                       color: #806b57; font-size: 10pt; }}
        </style>
        </head>
        <body>
            <table class="header" width="100%">
                <tr>
                    <td><h1>MAYURICAFE</h1>
                        <div class="tagline">Fresh moments, thoughtfully served</div></td>
                    <td><div class="bill-label">PAYMENT RECEIPT</div>
                        <div class="bill-id">#{int(order_id)}</div></td>
                    <td width="76">
                        <img class="brand-logo" src="{LOGO_PATH.as_uri()}"
                             width="68" height="68"/>
                    </td>
                </tr>
            </table>
            <table class="meta" width="100%">
                <tr>
                    <td><div class="meta-label">GUEST</div>
                        <div class="meta-value">{customer_name}</div></td>
                    <td><div class="meta-label">DATE &amp; TIME</div>
                        <div class="meta-value">{escape(issued_at)}</div></td>
                </tr>
                <tr>
                    <td><div class="meta-label">PHONE</div>
                        <div class="meta-value">{customer_phone}</div></td>
                    <td><div class="meta-label">SERVICE</div>
                        <div class="meta-value">{service}</div></td>
                </tr>
                <tr>
                    <td><div class="meta-label">SERVED BY</div>
                        <div class="meta-value">{escape(str(employee_name))}</div></td>
                    <td><div class="meta-label">PAYMENT METHOD</div>
                        <div class="meta-value">
                            {escape(str(payment_method).upper())} · PAID
                        </div></td>
                </tr>
            </table>
            <table class="items" width="100%">
                <thead><tr><th>Item</th><th class="center">Qty</th>
                    <th class="number">Unit price</th>
                    <th class="number">Line total</th></tr></thead>
                <tbody>{''.join(item_rows)}</tbody>
            </table>
            <div class="total-box">
                <span class="total-label">TOTAL PAID&nbsp;&nbsp;</span>
                <span class="total-value">₹{total:,.2f}</span>
            </div>
            <div class="footer">
                Thank you for choosing MAYURICAFE.<br/>
                We look forward to serving you again.
            </div>
        </body>
        </html>
    """

    writer = QPdfWriter(str(pdf_path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(
        QMarginsF(16, 16, 16, 16),
        QPageLayout.Unit.Millimeter,
    )
    document = QTextDocument()
    document.setHtml(html)
    printable_size = writer.pageLayout().paintRect(QPageLayout.Unit.Point).size()
    document.setPageSize(QSizeF(printable_size))
    document.print_(writer)
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise OSError(f"PDF bill was not written to {pdf_path}.")
    return pdf_path
