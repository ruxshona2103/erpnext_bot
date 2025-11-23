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


def format_phone(phone: Any) -> str:
    """
    Telefon raqamini formatlash.

    Args:
        phone: Telefon raqami (har qanday formatda)

    Returns:
        Formatlangan telefon: +998 90 123 45 67
    """
    if not phone:
        return "—"

    # Faqat raqamlarni olish
    digits = ''.join(filter(str.isdigit, str(phone)))

    # ⚠️ MUHIM: Agar raqam juda uzun yoki noto'g'ri bo'lsa - shunchaki qaytarish
    if len(digits) > 15:  # Telefon raqam 15 raqamdan ko'p bo'lmaydi (ITU-T E.164)
        return f"<code>{phone}</code>"  # Asl formatda qaytarish

    # Agar 12 raqam bo'lsa (998901234567)
    if len(digits) == 12 and digits.startswith('998'):
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}"

    # Agar 9 raqam bo'lsa (901234567) - 998 qo'shamiz
    if len(digits) == 9:
        return f"+998 {digits[:2]} {digits[2:5]} {digits[5:7]} {digits[7:]}"

    # Boshqa format bo'lsa - shunchaki qaytaramiz (noto'g'ri format deb hisoblaymiz)
    if digits:
        return f"<code>{phone}</code>"  # Asl formatda ko'rsatish

    return "—"


def clean_customer_name(name: Any) -> str:
    """
    Customer name'dan keraksiz belgilarni olib tashlash.

    Masalan: "(2) Doniyor 93 188 03 00" → "Doniyor"

    Args:
        name: Customer name (har qanday formatda)

    Returns:
        Tozalangan ism
    """
    if not name:
        return "—"

    import re
    name_str = str(name)

    # (2) kabi belgilarni olib tashlash
    name_str = re.sub(r'^\(\d+\)\s*', '', name_str)

    # Oxiridagi raqamlarni olib tashlash (93 188 03 00)
    name_str = re.sub(r'\s+\d+[\s\d]*$', '', name_str)

    # Agar hamma narsa o'chirilgan bo'lsa, asl nomni qaytarish
    cleaned = name_str.strip()
    return cleaned if cleaned else str(name)


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
    try:
        # ✅ Input validation
        if not isinstance(data, dict):
            return "❌ Noto'g'ri ma'lumot formati"

        if not data.get("success"):
            return "❌ Ma'lumot yuklanmadi"

        customer = data.get("customer", {})
        if not customer or not isinstance(customer, dict):
            return "❌ Mijoz ma'lumotlari topilmadi"

        contracts = data.get("contracts", [])
        next_payments = data.get("next_payments", [])

        # ============================================
        # SHAXSIY MA'LUMOTLAR
        # ============================================
        text = "━━━━━━━━━━━━━━━━━━━━\n"
        text += "👤 <b>SHAXSIY MA'LUMOTLAR</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        text += f"👨‍💼 <b>Ism:</b> {clean_customer_name(customer.get('customer_name', '—'))}\n"
        text += f"📱 <b>Telefon:</b> <code>{format_phone(customer.get('phone'))}</code>\n"

        # Passport
        if customer.get('passport'):
            text += f"🆔 <b>Passport:</b> <code>{customer.get('passport')}</code>\n"

        # Classification
        if customer.get('classification'):
            classification_text = {
                'A': 'A (A\'lo)',
                'B': 'B (Yaxshi)',
                'C': 'C (O\'rtacha)',
                'D': 'D (Past)'
            }.get(customer.get('classification'), customer.get('classification'))
            text += f"⭐ <b>Toifa:</b> {classification_text}\n"

        text += f"🔖 <b>ID:</b> <code>{customer.get('customer_id', '—')}</code>\n"

        # ============================================
        # SHARTNOMALAR STATISTIKASI
        # ============================================
        if contracts:
            total_amount = sum(c.get('total_amount', 0) for c in contracts)
            total_paid = sum(c.get('paid', 0) for c in contracts)
            total_remaining = sum(c.get('remaining', 0) for c in contracts)

            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📊 <b>SHARTNOMALAR</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            text += f"📄 <b>Jami shartnomalar:</b> {len(contracts)} ta\n"
            text += f"💰 <b>Umumiy summa:</b> {format_money(total_amount)} so'm\n"
            text += f"✅ <b>To'langan:</b> {format_money(total_paid)} so'm\n"
            text += f"📉 <b>Qolgan qarz:</b> {format_money(total_remaining)} so'm\n"
        else:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📄 <b>SHARTNOMALAR</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            text += "ℹ️ Hozircha shartnomalar mavjud emas\n"

        # ============================================
        # YAQIN TO'LOVLAR
        # ============================================
        if next_payments:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "🔔 <b>YAQIN TO'LOVLAR</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, payment in enumerate(next_payments[:5], 1):  # Eng ko'pi 5 ta
                status_emoji = {
                    "overdue": "❌",
                    "today": "⏰",
                    "soon": "⚠️",
                    "upcoming": "📅"
                }.get(payment.get('status'), "📅")

                text += f"{idx}. {status_emoji} <b>{payment.get('contract_id')}</b>\n"
                text += f"   📅 Sana: <b>{payment.get('due_date')}</b>\n"
                text += f"   💵 Summa: <b>{format_money(payment.get('amount'))}</b> so'm\n"
                text += f"   📊 Holat: <i>{payment.get('status_uz', payment.get('status_text', '—'))}</i>\n"

                if idx < len(next_payments[:5]):
                    text += "\n"

            text += "\n━━━━━━━━━━━━━━━━━━━━"

        return text

    except Exception as e:
        # ❌ Agar formatlashda xato yuz bersa
        from loguru import logger
        logger.error(f"format_customer_profile xatosi: {e}")
        logger.exception("Full traceback:")

        return (
            "❌ <b>Ma'lumotlarni ko'rsatishda xatolik</b>\n\n"
            "Iltimos, qaytadan urinib ko'ring yoki administratorga murojaat qiling."
        )


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
    text = "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📄 <b>SHARTNOMA DETALLARI</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    # Asosiy ma'lumotlar
    text += f"🔖 <b>Shartnoma ID:</b> <code>{contract.get('contract_id')}</code>\n"
    text += f"📅 <b>Sana:</b> {contract.get('contract_date')}\n"
    text += f"📊 <b>Holat:</b> {contract.get('status_uz', contract.get('status'))}\n"

    # Moliyaviy ma'lumotlar
    text += "\n━━━━━━━━━━━━━━━━━━━━\n"
    text += "💰 <b>MOLIYAVIY MA'LUMOTLAR</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    text += f"💵 <b>Umumiy summa:</b> {format_money(contract.get('total_amount'))} so'm\n"

    if contract.get('downpayment'):
        text += f"💳 <b>Boshlang'ich to'lov:</b> {format_money(contract.get('downpayment'))} so'm\n"

    text += f"✅ <b>To'langan:</b> {format_money(contract.get('paid'))} so'm\n"
    text += f"📉 <b>Qolgan qarz:</b> {format_money(contract.get('remaining'))} so'm\n"

    # Mahsulotlar ro'yxati
    products = contract.get('products', [])
    if products:
        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += "🛍 <b>MAHSULOTLAR</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for idx, product in enumerate(products, 1):
            text += f"<b>{idx}. {product.get('name')}</b>\n"
            text += f"   📦 Miqdor: {format_quantity(product.get('qty'))} dona\n"
            text += f"   💵 Narx: {format_money(product.get('price'))} so'm\n"
            text += f"   💰 Jami: {format_money(product.get('total_price'))} so'm\n"

            if product.get('imei'):
                text += f"   🔢 IMEI: <code>{product.get('imei')}</code>\n"

            if product.get('notes'):
                text += f"   📝 Izoh: {product.get('notes')}\n"

            if idx < len(products):
                text += "\n"

    # Keyingi to'lov
    next_payment = contract.get('next_payment')
    if next_payment:
        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += "📅 <b>KEYINGI TO'LOV</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        text += f"📆 <b>Sana:</b> {next_payment.get('due_date')}\n"
        text += f"💵 <b>Summa:</b> {format_money(next_payment.get('amount'))} so'm\n"
        text += f"📊 <b>Holat:</b> <i>{next_payment.get('status_uz', next_payment.get('status_text'))}</i>\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━"

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
                "amount": 1250000,  # Signed (negative for Pay)
                "display_amount": 1250000,  # Unsigned for display
                "method": "Naqd",
                "payment_type": "Receive"  # or "Pay"
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
        # ✅ Payment type ni aniqlash (Receive = kirim, Pay = chiqim/qaytarish)
        payment_type = payment.get('payment_type', 'Receive')
        display_amount = payment.get('display_amount') or abs(payment.get('amount', 0))

        if payment_type == 'Pay':
            type_emoji = "🔴"
            type_text = "Qaytarish"
        else:
            type_emoji = "🟢"
            type_text = "Kirim"

        text += f"📅 <b>{payment.get('date')}</b>\n"
        text += f"   {type_emoji} <b>{format_money(display_amount)}</b> so'm ({type_text})\n"
        text += f"   🏦 Usul: {payment.get('method', 'Naqd')}\n"
        text += f"   🆔 ID: <code>{payment.get('payment_id')}</code>\n\n"

    return text


def format_payment_history_with_products(data: Dict[str, Any]) -> str:
    """
    To'lovlar tarixi + Mahsulotlar (faqat muhim ma'lumotlar).

    Bu formatter Telegram bot uchun maxsus yaratilgan - shaxsiy ma'lumotlar CHIQMAYDI!
    Faqat quyidagilar ko'rsatiladi:
    - Shartnoma asosiy ma'lumotlari (ID, sana, summalar)
    - Mahsulotlar (nomi, miqdori, narxi, IMEI, izohlar)
    - To'lovlar tarixi (sana, summa, usul)

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "contract": {
            "contract_id": "CON-2025-00245",
            "contract_date": "08.07.2025",
            "total_amount": 1116.0,
            "paid": 300.0,
            "remaining": 816.0
        },
        "products": [
            {
                "name": "iPhone 15 Pro Max 256GB",
                "qty": 1,
                "price": 1116.0,
                "total_price": 1116.0,
                "imei": "123456789",
                "notes": ""
            }
        ],
        "payments": [
            {
                "date": "10.07.2025",
                "amount": 300.0,
                "method": "Naqd",
                "payment_id": "PE-00001"
            }
        ],
        "total_paid": 300.0,
        "total_payments": 1
    }

    Returns:
        HTML formatted string (shaxsiy ma'lumotlarsiz!)
    """
    try:
        if not data.get("success"):
            return "❌ Ma'lumotlar yuklanmadi"

        contract = data.get("contract", {})
        products = data.get("products", [])
        payments = data.get("payments", [])
        total_paid = data.get("total_paid", 0)
        total_payments = data.get("total_payments", 0)

        # ============================================
        # SHARTNOMA MA'LUMOTLARI
        # ============================================
        text = "━━━━━━━━━━━━━━━━━━━━\n"
        text += "📄 <b>SHARTNOMA MA'LUMOTLARI</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        text += f"🔖 <b>Shartnoma:</b> <code>{contract.get('contract_id')}</code>\n"
        text += f"📅 <b>Sana:</b> {contract.get('contract_date')}\n\n"

        text += f"💰 <b>Umumiy summa:</b> {format_money(contract.get('total_amount'))} so'm\n"
        text += f"✅ <b>To'langan:</b> {format_money(total_paid)} so'm\n"
        text += f"📉 <b>Qoldiq:</b> {format_money(contract.get('remaining'))} so'm\n"

        # ============================================
        # MAHSULOTLAR
        # ============================================
        if products:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "🛍 <b>MAHSULOTLAR</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, product in enumerate(products, 1):
                text += f"<b>{idx}. {product.get('name')}</b>\n"
                text += f"   📦 Miqdor: {format_quantity(product.get('qty'))} dona\n"
                text += f"   💵 Narx: {format_money(product.get('price'))} so'm\n"
                text += f"   💰 Jami: {format_money(product.get('total_price'))} so'm\n"

                if product.get('imei'):
                    text += f"   🔢 IMEI: <code>{product.get('imei')}</code>\n"

                if product.get('notes'):
                    text += f"   📝 Izoh: {product.get('notes')}\n"

                if idx < len(products):
                    text += "\n"

        # ============================================
        # TO'LOVLAR TARIXI
        # ============================================
        if payments:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += f"💳 <b>TO'LOVLAR TARIXI</b> ({total_payments} ta)\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, payment in enumerate(payments, 1):
                # ✅ Payment type ni aniqlash (Receive = kirim, Pay = chiqim/qaytarish)
                payment_type = payment.get('payment_type', 'Receive')
                display_amount = payment.get('display_amount') or abs(payment.get('amount', 0))

                if payment_type == 'Pay':
                    type_emoji = "🔴"
                    type_text = "Qaytarish"
                else:
                    type_emoji = "🟢"
                    type_text = "Kirim"

                text += f"<b>{idx}. {payment.get('date')}</b>\n"
                text += f"   {type_emoji} <b>{format_money(display_amount)}</b> so'm ({type_text})\n"
                text += f"   🏦 Usul: {payment.get('method', 'Naqd')}\n"

                if payment.get('payment_id'):
                    text += f"   🆔 ID: <code>{payment.get('payment_id')}</code>\n"

                if idx < len(payments):
                    text += "\n"
        else:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "💳 <b>TO'LOVLAR TARIXI</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            text += "ℹ️ Hozircha to'lovlar kiritilmagan\n"

        text += "\n━━━━━━━━━━━━━━━━━━━━"

        return text

    except Exception as e:
        from loguru import logger
        logger.error(f"format_payment_history_with_products xatosi: {e}")
        logger.exception("Full traceback:")

        return (
            "❌ <b>Ma'lumotlarni ko'rsatishda xatolik</b>\n\n"
            "Iltimos, qaytadan urinib ko'ring yoki administratorga murojaat qiling."
        )


# ============================================================================
# PAYMENT SCHEDULE FORMATTER
# ============================================================================

def format_payment_schedule(data: Dict[str, Any]) -> str:
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
    if not data.get("success"):
        return "❌ Ma'lumot yuklanmadi"

    payments = data.get("payments", [])

    if not payments:
        return "✅ <b>Yaqin to'lovlar yo'q</b>\n\nBarcha to'lovlar vaqtida amalga oshirilgan! 🎉"

    text = "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🔔 <b>YAQIN TO'LOVLAR</b> ({len(payments)} ta)\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"

    for idx, payment in enumerate(payments, 1):
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

        text += f"<b>{idx}. {emoji} {payment.get('contract_id')}</b>\n"
        text += f"   📅 <b>Sana:</b> {payment.get('due_date')}\n"
        text += f"   💰 <b>Summa:</b> {format_money(payment.get('amount'))} so'm\n"

        if payment.get('outstanding'):
            text += f"   📉 <b>Qarz:</b> {format_money(payment.get('outstanding'))} so'm\n"

        text += f"   📊 <b>Holat:</b> {status_text}\n"

        if idx < len(payments):
            text += "\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━"

    return text


# ============================================================================
# CONTRACT DETAILS FORMATTER (WRAPPER)
# ============================================================================

def format_contract_details(data: Dict[str, Any]) -> str:
    """
    Shartnoma detallarini formatlash (wrapper function).

    Bu function contract handler uchun - API response ni to'g'ridan-to'g'ri formatlaydi.

    ERPNext API Response:
    ---------------------
    {
        "success": True,
        "contract": {...}
    }

    Args:
        data: ERPNext API response with contract details

    Returns:
        HTML formatted string
    """
    # Agar API xato qaytargan bo'lsa
    if not data.get("success"):
        return format_error_message(data)

    # Contract ma'lumotlarini olamiz
    contract = data.get("contract")
    if not contract:
        return "❌ Shartnoma ma'lumotlari topilmadi"

    # Contract ni formatlash
    return format_contract_with_products(contract)


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


# ============================================================================
# DETAILED PAYMENT HISTORY FORMATTER (BATAFSIL TO'LOVLAR TARIXI)
# ============================================================================

def format_detailed_payment_history(
    contract_data: Dict[str, Any],
    schedule_data: Dict[str, Any],
    payment_history_data: Dict[str, Any]
) -> str:
    """
    Batafsil to'lovlar tarixi formatlash.

    Ko'rsatiladigan ma'lumotlar:
    ---------------------------
    1. Shartnoma asosiy ma'lumotlari
    2. Mahsulotlar (nomi, miqdori, narxi, IMEI)
    3. Necha oylik muddatga kelishilgan
    4. Qaysi oylar to'langan / qolgan
    5. Oxirgi to'lov sanasi va summasi
    6. Umumiy statistika (jami, to'langan, qoldiq)

    Args:
        contract_data: Shartnoma ma'lumotlari (products bilan)
        schedule_data: To'lov jadvali (oylar bo'yicha)
        payment_history_data: To'lovlar tarixi

    Returns:
        HTML formatted string
    """
    try:
        # Xavfsiz dict olish
        if not contract_data:
            contract_data = {}
        if not schedule_data:
            schedule_data = {}
        if not payment_history_data:
            payment_history_data = {}

        text = ""

        # ============================================
        # SHARTNOMA ASOSIY MA'LUMOTLARI
        # ============================================
        # Contract ma'lumotlarini olish - API response strukturasiga qarab
        contract = contract_data.get("contract") or {}
        if not contract:
            # Agar contract alohida field bo'lmasa, contract_data ning o'zidan olish
            contract = {
                "contract_id": contract_data.get("contract_id", "—"),
                "contract_date": contract_data.get("contract_date", "—"),
                "total_amount": contract_data.get("total_amount", 0),
                "paid": contract_data.get("paid", 0),
                "remaining": contract_data.get("remaining", 0),
                "downpayment": contract_data.get("downpayment", 0),
            }

        contract_id = contract.get("contract_id") or "—"
        contract_date = contract.get("contract_date") or "—"
        total_amount = float(contract.get("total_amount") or 0)
        paid_amount = float(contract.get("paid") or 0)
        remaining = float(contract.get("remaining") or 0)
        downpayment = float(contract.get("downpayment") or 0)

        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "📄 <b>SHARTNOMA MA'LUMOTLARI</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        text += f"🔖 <b>Shartnoma:</b> <code>{contract_id}</code>\n"
        text += f"📅 <b>Tuzilgan sana:</b> {contract_date}\n\n"

        text += f"💰 <b>Umumiy summa:</b> {format_money(total_amount)} so'm\n"
        if downpayment:
            text += f"💳 <b>Boshlang'ich to'lov:</b> {format_money(downpayment)} so'm\n"
        text += f"✅ <b>To'langan:</b> {format_money(paid_amount)} so'm\n"
        text += f"📉 <b>Qoldiq:</b> {format_money(remaining)} so'm\n"

        # To'lov foizi
        if total_amount > 0:
            percentage = (paid_amount / total_amount) * 100
            text += f"📊 <b>To'lov foizi:</b> {percentage:.1f}%\n"

        # ============================================
        # MAHSULOTLAR
        # ============================================
        products = contract_data.get("products") or []
        if not products:
            products = contract.get("products") or []

        if products and isinstance(products, list) and len(products) > 0:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += f"🛍 <b>MAHSULOTLAR</b> ({len(products)} ta)\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for idx, product in enumerate(products, 1):
                if not isinstance(product, dict):
                    continue

                name = product.get("name") or "Noma'lum mahsulot"
                qty = float(product.get("qty") or 0)
                imei = product.get("imei") or ""

                # Faqat mahsulot nomi va miqdori ko'rsatiladi (narxsiz)
                text += f"<b>{idx}. {name}</b> — {format_quantity(qty)} dona\n"

                if imei:
                    text += f"   🔢 IMEI: <code>{imei}</code>\n"

                if idx < len(products):
                    text += "\n"

        # ============================================
        # TO'LOV JADVALI (OYLAR BO'YICHA)
        # ============================================
        schedule = schedule_data.get("schedule") or []
        total_months = len(schedule) if schedule else 0

        if schedule and isinstance(schedule, list) and len(schedule) > 0:
            # Xavfsiz filter qilish
            paid_months = [s for s in schedule if isinstance(s, dict) and s.get("status") == "paid"]
            partial_months = [s for s in schedule if isinstance(s, dict) and s.get("status") == "partial"]
            unpaid_months = [s for s in schedule if isinstance(s, dict) and s.get("status") in ("unpaid", "pending", None)]
            overdue_months = [s for s in schedule if isinstance(s, dict) and s.get("is_overdue")]

            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📅 <b>TO'LOV JADVALI</b> ({total_months} oylik)\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            # Umumiy statistika
            text += f"✅ To'langan oylar: <b>{len(paid_months)}</b> ta\n"
            if partial_months:
                text += f"⚠️ Qisman to'langan: <b>{len(partial_months)}</b> ta\n"
            text += f"⏳ Qolgan oylar: <b>{len(unpaid_months)}</b> ta\n"
            if overdue_months:
                text += f"❌ Kechikkan: <b>{len(overdue_months)}</b> ta\n"

            text += "\n<b>Oylar tafsiloti:</b>\n\n"

            # Har bir oy uchun
            for month in schedule:
                if not isinstance(month, dict):
                    continue

                month_num = month.get("month") or 0
                due_date = month.get("due_date") or "—"
                amount = float(month.get("amount") or 0)
                month_paid = float(month.get("paid") or 0)
                outstanding = float(month.get("outstanding") or 0)
                status = month.get("status") or "pending"
                is_overdue = month.get("is_overdue", False)

                # Status emoji
                if status == "paid":
                    emoji = "✅"
                    status_text = "To'langan"
                elif status == "partial":
                    emoji = "⚠️"
                    status_text = f"Qisman ({format_money(month_paid)} so'm)"
                elif is_overdue:
                    emoji = "❌"
                    status_text = "Kechikkan!"
                else:
                    emoji = "⏳"
                    status_text = "Kutilmoqda"

                text += f"{emoji} <b>{month_num}-oy</b> | {due_date}\n"
                text += f"   💵 {format_money(amount)} so'm — {status_text}\n"

                if outstanding > 0 and status != "paid":
                    text += f"   📉 Qoldiq: {format_money(outstanding)} so'm\n"

        # ============================================
        # TO'LOVLAR TARIXI
        # ============================================
        payments = payment_history_data.get("payments") or []
        total_payments = payment_history_data.get("total_payments") or len(payments)

        if payments and isinstance(payments, list) and len(payments) > 0:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += f"💳 <b>TO'LOVLAR TARIXI</b> ({total_payments} ta)\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            # Oxirgi to'lov
            last_payment = payments[0] if payments else None
            if last_payment and isinstance(last_payment, dict):
                text += f"🕐 <b>Oxirgi to'lov:</b>\n"
                text += f"   📅 Sana: <b>{last_payment.get('date') or '—'}</b>\n"
                text += f"   💰 Summa: <b>{format_money(last_payment.get('amount') or 0)}</b> so'm\n"
                text += f"   🏦 Usul: {last_payment.get('method') or 'Naqd'}\n\n"

            # Barcha to'lovlar ro'yxati
            text += "<b>Barcha to'lovlar:</b>\n\n"

            total_paid_sum = 0
            for idx, payment in enumerate(payments, 1):
                if not isinstance(payment, dict):
                    continue

                date = payment.get("date") or "—"
                amount = float(payment.get("amount") or 0)
                method = payment.get("method") or "Naqd"
                payment_id = payment.get("payment_id") or ""

                # ✅ Payment type ni aniqlash (Receive = kirim, Pay = chiqim/qaytarish)
                payment_type = payment.get('payment_type', 'Receive')
                display_amount = payment.get('display_amount') or abs(amount)

                if payment_type == 'Pay':
                    type_emoji = "🔴"
                    type_text = "Qaytarish"
                else:
                    type_emoji = "🟢"
                    type_text = "Kirim"

                # ✅ Jami hisoblashda signed amount ishlatiladi
                total_paid_sum += amount

                text += f"{idx}. <b>{date}</b>\n"
                text += f"   {type_emoji} {format_money(display_amount)} so'm ({type_text}) | {method}\n"

                if payment_id:
                    text += f"   🆔 <code>{payment_id}</code>\n"

            # Jami to'langan (net summa)
            text += f"\n📊 <b>Jami to'langan (sof):</b> {format_money(total_paid_sum)} so'm\n"

        else:
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "💳 <b>TO'LOVLAR TARIXI</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            text += "ℹ️ Hozircha to'lovlar kiritilmagan\n"

        # ============================================
        # YAKUNIY XULOSA
        # ============================================
        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += "📋 <b>XULOSA</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        text += f"💰 Umumiy summa: <b>{format_money(total_amount)}</b> so'm\n"
        text += f"✅ To'langan: <b>{format_money(paid_amount)}</b> so'm\n"
        text += f"📉 Qolgan qarz: <b>{format_money(remaining)}</b> so'm\n"

        # Muddat ma'lumotlari
        final_schedule = schedule_data.get("schedule") or []
        if final_schedule and isinstance(final_schedule, list):
            paid_months_count = len([s for s in final_schedule if isinstance(s, dict) and s.get("status") == "paid"])
            total_months_final = len(final_schedule)
            text += f"📅 Muddat: {total_months_final} oylik ({paid_months_count} oy to'langan)\n"

        text += "\n━━━━━━━━━━━━━━━━━━━━"

        return text

    except Exception as e:
        from loguru import logger
        logger.error(f"format_detailed_payment_history xatosi: {e}")
        logger.exception("Full traceback:")

        return (
            "❌ <b>Ma'lumotlarni ko'rsatishda xatolik</b>\n\n"
            "Iltimos, qaytadan urinib ko'ring yoki administratorga murojaat qiling."
        )
