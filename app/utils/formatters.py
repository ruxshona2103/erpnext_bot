"""
Message Formatters for Telegram Bot

Bu modul ERPNext API dan kelgan ma'lumotlarni Telegram uchun
chiroyli formatda ko'rsatadi.

ERPNext API Structure bilan to'liq mos:
---------------------------------------
- Customer info
- Contract details with products
- Payment history
- Payment schedule
- Upcoming payments

Best Practices:
---------------
- HTML formatlash ishlatilgan (<b>, <i>, <code>)
- Raqamlar 1,000,000 formatda
- Sanalar dd.MM.yyyy formatda
- Emoji ishlatilgan (😊 user-friendly)
"""

from typing import Dict, List, Any, Optional


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_money(amount: Any) -> str:
    """
    Pul summalarini formatlash: 1234567 → 1,234,567

    Args:
        amount: Pul summasi (int, float, str, None)

    Returns:
        Formatlangan string
    """
    try:
        if amount is None or amount == "":
            return "0"
        return f"{int(float(amount)):,}"
    except (ValueError, TypeError):
        return "0"


def format_quantity(qty: Any) -> str:
    """
    Miqdorni formatlash (dona, kg, etc.)

    Args:
        qty: Miqdor

    Returns:
        Formatlangan string
    """
    try:
        if qty is None or qty == "":
            return "0"
        # Float bo'lsa .5 ko'rsatamiz, integer bo'lsa 2 → 2
        num = float(qty)
        if num == int(num):
            return str(int(num))
        return f"{num:.1f}"
    except (ValueError, TypeError):
        return "0"


# ============================================================================
# CUSTOMER PROFILE FORMATTER
# ============================================================================

def format_customer_profile(data: Dict[str, Any]) -> str:
    """
    Customer profil ma'lumotlarini formatlash.

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "customer": {
            "customer_id": "CUST-00001",
            "customer_name": "Ali Aliyev",
            "phone": "+998901234567",
            "passport": "AB1234567",
            "telegram_id": "123456789"
        },
        "contracts": [...],
        "next_payments": [...]
    }

    Returns:
        HTML formatted string
    """
    if not data.get("success"):
        return "❌ Ma'lumot yuklanmadi"

    customer = data.get("customer", {})
    contracts = data.get("contracts", [])
    next_payments = data.get("next_payments", [])

    # Customer asosiy ma'lumotlari
    text = "👤 <b>Shaxsiy ma'lumotlar</b>\n\n"
    text += f"👨‍💼 Ism: <b>{customer.get('customer_name', '—')}</b>\n"
    text += f"📱 Telefon: <b>{customer.get('phone', '—')}</b>\n"
    text += f"🆔 ID: <code>{customer.get('customer_id', '—')}</code>\n"

    # Shartnomalar umumiy statistika
    if contracts:
        total_amount = sum(c.get('total_amount', 0) for c in contracts)
        total_paid = sum(c.get('paid', 0) for c in contracts)
        total_remaining = sum(c.get('remaining', 0) for c in contracts)

        text += "\n📊 <b>Umumiy statistika</b>\n\n"
        text += f"📄 Shartnomalar: <b>{len(contracts)} ta</b>\n"
        text += f"💰 Umumiy summa: <b>{format_money(total_amount)}</b> so'm\n"
        text += f"✅ To'langan: <b>{format_money(total_paid)}</b> so'm\n"
        text += f"📉 Qarz: <b>{format_money(total_remaining)}</b> so'm\n"
    else:
        text += "\n📄 Shartnomalar mavjud emas\n"

    # Yaqin to'lovlar
    if next_payments:
        text += "\n🔔 <b>Yaqin to'lovlar:</b>\n\n"
        for payment in next_payments[:3]:  # Faqat 3 ta yaqin to'lov
            status_emoji = {
                "overdue": "❌",
                "today": "⏰",
                "soon": "⚠️",
                "upcoming": "📅"
            }.get(payment.get('status'), "📅")

            text += f"{status_emoji} <b>{payment.get('contract_id')}</b>\n"
            text += f"   💵 Summa: <b>{format_money(payment.get('amount'))}</b> so'm\n"
            text += f"   📅 Sana: <b>{payment.get('due_date')}</b>\n"
            text += f"   ⏳ {payment.get('status_uz', payment.get('status_text'))}\n\n"

    return text


# ============================================================================
# CONTRACT DETAILS FORMATTER (WITH PRODUCTS)
# ============================================================================

def format_contract_with_products(contract: Dict[str, Any]) -> str:
    """
    Shartnoma batafsil ma'lumotlari - mahsulotlar bilan.

    ERPNext API Response Structure:
    -------------------------------
    {
        "contract_id": "SAL-ORD-00001",
        "contract_date": "15.01.2025",
        "total_amount": 15000000,
        "downpayment": 3000000,
        "paid": 5000000,
        "remaining": 10000000,
        "status": "To Deliver and Bill",
        "status_uz": "Yetkazish va hisob",
        "products": [
            {
                "name": "Samsung Galaxy S24",
                "qty": 2,
                "price": 7000000,  # Narx foiz bilan
                "total_price": 14000000,
                "imei": "123456789",
                "notes": "Qora rang"
            }
        ],
        "payments_history": [...],
        "next_payment": {...}
    }

    Returns:
        HTML formatted string
    """
    text = f"📄 <b>Shartnoma #{contract.get('contract_id')}</b>\n\n"

    # Asosiy ma'lumotlar
    text += f"📅 Sana: <b>{contract.get('contract_date')}</b>\n"
    text += f"📊 Holat: <b>{contract.get('status_uz', contract.get('status'))}</b>\n\n"

    # Moliyaviy ma'lumotlar
    text += "💰 <b>Moliyaviy ma'lumotlar:</b>\n\n"
    text += f"   Umumiy summa: <b>{format_money(contract.get('total_amount'))}</b> so'm\n"

    if contract.get('downpayment'):
        text += f"   Boshlang'ich to'lov: <b>{format_money(contract.get('downpayment'))}</b> so'm\n"

    text += f"   ✅ To'langan: <b>{format_money(contract.get('paid'))}</b> so'm\n"
    text += f"   📉 Qarz: <b>{format_money(contract.get('remaining'))}</b> so'm\n"

    # Mahsulotlar ro'yxati
    products = contract.get('products', [])
    if products:
        text += "\n🛍 <b>Mahsulotlar:</b>\n\n"
        for idx, product in enumerate(products, 1):
            text += f"{idx}. <b>{product.get('name')}</b>\n"
            text += f"   📦 Miqdor: <b>{format_quantity(product.get('qty'))}</b> dona\n"
            text += f"   💵 Narx: <b>{format_money(product.get('price'))}</b> so'm\n"
            text += f"   💰 Jami: <b>{format_money(product.get('total_price'))}</b> so'm\n"

            if product.get('imei'):
                text += f"   🔢 IMEI: <code>{product.get('imei')}</code>\n"

            if product.get('notes'):
                text += f"   📝 {product.get('notes')}\n"

            text += "\n"

    # Keyingi to'lov
    next_payment = contract.get('next_payment')
    if next_payment:
        text += "📅 <b>Keyingi to'lov:</b>\n\n"
        text += f"   Sana: <b>{next_payment.get('due_date')}</b>\n"
        text += f"   Summa: <b>{format_money(next_payment.get('amount'))}</b> so'm\n"
        text += f"   Holat: <b>{next_payment.get('status_uz', next_payment.get('status_text'))}</b>\n"

    return text


# ============================================================================
# CONTRACTS LIST FORMATTER
# ============================================================================

def format_contracts_list(contracts: List[Dict[str, Any]]) -> str:
    """
    Shartnomalar ro'yxatini formatlash (qisqa format).

    Inline keyboard uchun ishlatiladi.

    Returns:
        HTML formatted string
    """
    if not contracts:
        return "📄 Shartnomalar topilmadi"

    text = f"📄 <b>Sizning shartnomalaringiz</b> ({len(contracts)} ta)\n\n"
    text += "Batafsil ko'rish uchun shartnomani tanlang:\n"

    return text


# ============================================================================
# PAYMENT HISTORY FORMATTER
# ============================================================================

def format_payment_history(data: Dict[str, Any]) -> str:
    """
    To'lovlar tarixini formatlash.

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "payments": [
            {
                "payment_id": "PE-00001",
                "date": "15.02.2025",
                "amount": 1250000,
                "method": "Naqd"
            }
        ],
        "total_payments": 5
    }

    Returns:
        HTML formatted string
    """
    if not data.get("success"):
        return "❌ To'lovlar yuklanmadi"

    payments = data.get("payments", [])
    total = data.get("total_payments", 0)

    if not payments:
        return "💳 To'lovlar tarixi mavjud emas"

    text = f"💳 <b>To'lovlar tarixi</b> ({total} ta)\n\n"

    for payment in payments:
        text += f"📅 <b>{payment.get('date')}</b>\n"
        text += f"   💰 Summa: <b>{format_money(payment.get('amount'))}</b> so'm\n"
        text += f"   🏦 Usul: {payment.get('method', 'Naqd')}\n"
        text += f"   🆔 ID: <code>{payment.get('payment_id')}</code>\n\n"

    return text


# ============================================================================
# PAYMENT SCHEDULE FORMATTER
# ============================================================================

def format_payment_schedule(data: Dict[str, Any]) -> str:
    """
    To'lov jadvalini formatlash.

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "contract_id": "SAL-ORD-00001",
        "schedule": [
            {
                "month": 1,
                "due_date": "15.02.2025",
                "amount": 1250000,
                "paid": 1250000,
                "outstanding": 0,
                "status": "paid",
                "status_uz": "To'langan",
                "days_left": -30,
                "is_overdue": False
            }
        ],
        "total_months": 12
    }

    Returns:
        HTML formatted string
    """
    if not data.get("success"):
        return "❌ To'lov jadvali yuklanmadi"

    contract_id = data.get("contract_id")
    schedule = data.get("schedule", [])
    total_months = data.get("total_months", 0)

    if not schedule:
        return "📅 To'lov jadvali mavjud emas"

    text = f"📅 <b>To'lov jadvali</b>\n"
    text += f"📄 Shartnoma: <code>{contract_id}</code>\n"
    text += f"📊 Jami: {total_months} oylik\n\n"

    for month in schedule:
        # Status emoji
        status = month.get('status')
        if status == 'paid':
            emoji = "✅"
        elif status == 'partial':
            emoji = "⚠️"
        elif month.get('is_overdue'):
            emoji = "❌"
        else:
            emoji = "⏳"

        text += f"{emoji} <b>{month.get('month')}-oy</b> — {month.get('due_date')}\n"
        text += f"   💵 To'lov: <b>{format_money(month.get('amount'))}</b> so'm\n"

        if month.get('paid', 0) > 0:
            text += f"   ✅ To'langan: <b>{format_money(month.get('paid'))}</b> so'm\n"

        if month.get('outstanding', 0) > 0:
            text += f"   📉 Qoldiq: <b>{format_money(month.get('outstanding'))}</b> so'm\n"

        text += f"   📊 {month.get('status_uz', status)}\n\n"

    return text


# ============================================================================
# UPCOMING PAYMENTS FORMATTER (REMINDERS)
# ============================================================================

def format_upcoming_payments(data: Dict[str, Any]) -> str:
    """
    Yaqin to'lovlar (eslatmalar) formatini yaratish.

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "payments": [
            {
                "contract_id": "SAL-ORD-00001",
                "due_date": "15.03.2025",
                "amount": 1250000,
                "outstanding": 1250000,
                "days_left": 5,
                "status": "soon",
                "status_uz": "Yaqinda",
                "month_number": 3
            }
        ],
        "total_upcoming": 3
    }

    Returns:
        HTML formatted string
    """
    if not data.get("success"):
        return "❌ Ma'lumot yuklanmadi"

    payments = data.get("payments", [])

    if not payments:
        return "✅ Yaqin to'lovlar yo'q"

    text = f"🔔 <b>Yaqin to'lovlar</b> ({len(payments)} ta)\n\n"

    for payment in payments:
        status = payment.get('status')
        days_left = payment.get('days_left', 0)

        # Status emoji
        if status == 'overdue':
            emoji = "❌"
            status_text = f"<b>{abs(days_left)} kun kechikkan!</b>"
        elif status == 'today':
            emoji = "⏰"
            status_text = "<b>BUGUN to'lash kerak!</b>"
        elif status == 'soon':
            emoji = "⚠️"
            status_text = f"<b>{days_left} kundan keyin</b>"
        else:
            emoji = "📅"
            status_text = f"{days_left} kun qoldi"

        text += f"{emoji} <b>{payment.get('contract_id')}</b>\n"
        text += f"   📅 Sana: <b>{payment.get('due_date')}</b>\n"
        text += f"   💰 Summa: <b>{format_money(payment.get('amount'))}</b> so'm\n"
        text += f"   ⏳ {status_text}\n\n"

    return text


# ============================================================================
# ERROR MESSAGES
# ============================================================================

def format_error_message(error_data: Dict[str, Any]) -> str:
    """
    Xato xabarlarini formatlash.

    Args:
        error_data: ERPNext API error response

    Returns:
        User-friendly error message
    """
    message = error_data.get('message', 'Noma\'lum xatolik')
    message_uz = error_data.get('message_uz')

    if message_uz:
        return f"❌ {message_uz}"

    return f"❌ {message}"
