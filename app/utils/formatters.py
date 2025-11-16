# app/utils/formatters.py

from datetime import datetime
from typing import Any, Optional


# ======== YORDAMCHI FUNKSIYALAR ========

def fmt_date(date_str: Optional[str]) -> str:
    """Sana stringini  dd.MM.YYYY formatiga aylantiradi."""
    if not date_str:
        return "—"

    # Ikki xil formatni qo‘llab-quvvatlaymiz
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            continue

    # Agar tanimasa – o‘zini qaytaramiz
    return date_str


def fmt_num(val: Any) -> int:
    """None, string, float – hammasini xavfsiz int ga o‘giradi."""
    try:
        if val is None:
            return 0
        return int(float(val))
    except (TypeError, ValueError):
        return 0


# ======== CUSTOMER INFO FORMATTER ========

def format_customer_info(data: dict) -> str:
    customer = data.get("customer", {})
    contracts = data.get("contracts", [])
    summary = data.get("summary", {})

    customer_id = customer.get("id") or customer.get("name") or "—"

    text = (
        "👤 <b>Mijoz ma'lumotlari</b>\n"
        f"• ID: <b>{customer_id}</b>\n"
        f"• Ism: <b>{customer.get('name', '—')}</b>\n"
        f"• Telefon: <b>{customer.get('phone', '—')}</b>\n"
        f"• Telegram: <b>{customer.get('telegram', '—') or '—'}</b>\n"
        f"• Toifa: <b>{customer.get('classification', '—')}</b>\n\n"
        "📄 <b>Shartnomalar</b>\n"
        f"• Jami shartnoma: <b>{fmt_num(summary.get('total_contracts'))}</b>\n"
        f"• Umumiy summa: <b>{fmt_num(summary.get('total_amount')):,}</b> so'm\n"
        f"• To'langan: <b>{fmt_num(summary.get('paid_amount')):,}</b> so'm\n"
        f"• Qoldiq: <b>{fmt_num(summary.get('remaining_amount')):,}</b> so'm\n"
    )

    if not contracts:
        text += "\n🔍 Shartnomalar topilmadi."
        return text

    text += "\n📑 <b>Shartnoma ro‘yxati:</b>\n"

    for c in contracts:
        cid = c.get("id") or c.get("name") or "—"
        date = c.get("date")
        total = fmt_num(c.get("total"))
        paid = fmt_num(c.get("paid"))
        remaining = fmt_num(c.get("remaining"))
        next_payment_date = c.get("next_payment_date")
        monthly_payment = fmt_num(c.get("monthly_payment")) if c.get("monthly_payment") else 0
        status = c.get("status", "—")

        text += (
            f"\n<b>#{cid}</b>\n"
            f"• Sana: <b>{fmt_date(date)}</b>\n"
            f"• To‘lov summasi: <b>{total:,}</b> so‘m\n"
            f"• To‘langan: <b>{paid:,}</b> so‘m\n"
            f"• Qoldiq: <b>{remaining:,}</b> so‘m\n"
            f"• Keyingi to‘lov: <b>{fmt_date(next_payment_date)}</b>\n"
            f"• Oylik to‘lov: <b>{monthly_payment:,}</b> so‘m\n"
            f"• Holat: <b>{status}</b>\n"
        )
    return text


# ======== CONTRACT DETAILS FORMATTER ========

def format_contract_details(data: dict) -> str:
    contract = data.get("contract")
    schedule = data.get("schedule", [])

    if not contract:
        return "❌ Shartnoma ma'lumotlari topilmadi."

    text = (
        f"📄 <b>Shartnoma:</b> #{contract.get('id')}</b>\n"
        f"👤 Mijoz: <b>{contract.get('customer')}</b>\n"
        f"📅 Sana: <b>{fmt_date(contract.get('date'))}</b>\n\n"
        f"💰 Umumiy summa: <b>{fmt_num(contract.get('total')):,}</b> so‘m\n"
        f"💳 To‘langan: <b>{fmt_num(contract.get('paid')):,}</b> so‘m\n"
        f"📉 Qoldiq: <b>{fmt_num(contract.get('remaining')):,}</b> so‘m\n"
        f"📌 Holat: <b>{contract.get('status')}</b>\n\n"
        "📅 <b>To‘lov jadvali:</b>\n"
    )

    if not schedule:
        text += "\nJadval topilmadi."
        return text

    for s in schedule:
        text += (
            f"\n<b>{s.get('month')} - oy</b>\n"
            f"• To‘lov kuni: <b>{fmt_date(s.get('due_date'))}</b>\n"
            f"• To‘lov: <b>{fmt_num(s.get('amount')):,}</b> so‘m\n"
            f"• To‘langan: <b>{fmt_num(s.get('paid')):,}</b> so‘m\n"
            f"• Qoldiq: <b>{fmt_num(s.get('outstanding')):,}</b> so‘m\n"
            f"• Holat: <b>{s.get('status')}</b>\n"
        )
    return text


# ======== PAYMENT HISTORY FORMATTER ========

def format_payment_history(data: dict) -> str:
    payments = data.get("payments", [])
    total = fmt_num(data.get("total_payments"))

    text = f"💳 <b>So'nggi {total} ta to‘lov</b>\n"

    if not payments:
        return text + "\nTo‘lovlar topilmadi."

    for p in payments:
        text += (
            f"\n<b>#{p.get('id')}</b>\n"
            f"📅 Sana: <b>{fmt_date(p.get('date'))}</b>\n"
            f"💰 Summa: <b>{fmt_num(p.get('amount')):,}</b> so‘m\n"
            f"📄 Shartnoma: <b>{p.get('contract')}</b>\n"
            f"🏦 To‘lov turi: <b>{p.get('method')}</b>\n"
            f"📝 Izoh: {p.get('notes') or '—'}\n"
        )

    return text
