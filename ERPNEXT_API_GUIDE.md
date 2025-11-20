# ERPNext Telegram Bot API - To'liq Yo'riqnoma

Bu yo'riqnomada ERPNext app ichida `telegram_bot_api.py` faylini qanday yaratish va sozlash haqida batafsil ma'lumot berilgan.

## 📁 Fayl joylashuvi

```
your_custom_app/
└── your_custom_app/
    └── api/
        └── telegram_bot_api.py
```

Masalan:
```
cash_flow_app/
└── cash_flow_management/
    └── api/
        └── telegram_bot_api.py
```

---

## 📝 `telegram_bot_api.py` - To'liq Kod

```python
# -*- coding: utf-8 -*-
import frappe
from frappe import _


@frappe.whitelist(allow_guest=False)
def get_customer_by_passport(passport_series):
    """
    Passport seriyasi bo'yicha mijoz ma'lumotlarini qaytaradi.

    Args:
        passport_series (str): Passport seriya raqami

    Returns:
        dict: Mijoz, shartnomalar va keyingi to'lovlar haqida ma'lumot
    """
    try:
        # Mijozni topish
        customers = frappe.get_all(
            "Customer",
            filters={"custom_phone_1": passport_series},
            fields=["name", "customer_name", "custom_phone_1",
                    "customer_classification", "custom_telegram_id"]
        )

        if not customers:
            return {
                "success": False,
                "message": "Mijoz topilmadi"
            }

        customer = customers[0]

        # Shartnomalarni topish
        contracts = frappe.get_all(
            "Sales Order",
            filters={
                "customer": customer["name"],
                "docstatus": 1  # Faqat tasdiqlangan
            },
            fields=[
                "name",
                "transaction_date",
                "grand_total as total",
                "advance_paid as paid",
                "rounded_total as remaining"
            ],
            order_by="transaction_date desc"
        )

        # Har bir shartnoma uchun qoldiq hisobini to'g'rilash
        for contract in contracts:
            contract["remaining"] = contract["total"] - contract["paid"]

        # Keyingi to'lovlarni topish
        next_installments = []
        for contract in contracts[:3]:  # Birinchi 3 ta shartnoma
            installments = frappe.get_all(
                "Payment Schedule",
                filters={
                    "parent": contract["name"],
                    "parenttype": "Sales Order",
                    "payment_amount": [">", 0]
                },
                fields=[
                    "payment_amount as amount",
                    "due_date",
                    "outstanding",
                    "idx as month"
                ],
                order_by="due_date asc",
                limit=1
            )

            if installments:
                inst = installments[0]
                # Kunlar farqini hisoblash
                from datetime import datetime
                due_date = inst["due_date"]
                today = datetime.now().date()
                days_left = (due_date - today).days

                inst["contract"] = contract["name"]
                inst["days_left"] = days_left
                inst["status"] = "overdue" if days_left < 0 else "pending"
                inst["due_date"] = due_date.strftime("%d.%m.%Y")

                next_installments.append(inst)

        return {
            "success": True,
            "customer": customer,
            "contracts": {
                "success": True,
                "contracts": contracts
            },
            "next_payment": {
                "success": True,
                "next_installments": next_installments
            }
        }

    except Exception as e:
        frappe.log_error(f"Telegram Bot API Error: {str(e)}", "get_customer_by_passport")
        return {
            "success": False,
            "message": f"Xatolik yuz berdi: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def link_telegram(customer_id, telegram_id, username=None):
    """
    Mijozga Telegram ID ni bog'lash.

    Args:
        customer_id (str): Customer document name
        telegram_id (str/int): Telegram chat ID
        username (str, optional): Telegram username

    Returns:
        dict: Success status
    """
    try:
        customer = frappe.get_doc("Customer", customer_id)
        customer.custom_telegram_id = str(telegram_id)

        if username:
            customer.custom_telegram_username = username

        customer.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "message": "Telegram ID muvaffaqiyatli bog'landi"
        }

    except Exception as e:
        frappe.log_error(f"Telegram Link Error: {str(e)}", "link_telegram")
        return {
            "success": False,
            "message": f"Bog'lanishda xatolik: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def get_contracts_by_telegram_id(telegram_id):
    """
    Telegram ID bo'yicha mijoz shartnomalarini qaytaradi.

    Args:
        telegram_id (str/int): Telegram chat ID

    Returns:
        dict: Mijoz va shartnomalar ma'lumoti
    """
    try:
        # Telegram ID bo'yicha mijoz topish
        customers = frappe.get_all(
            "Customer",
            filters={"custom_telegram_id": str(telegram_id)},
            fields=["name", "customer_name", "custom_phone_1",
                    "customer_classification", "custom_telegram_id"]
        )

        if not customers:
            return {
                "success": False,
                "message": "Telegram ID ga bog'langan mijoz topilmadi"
            }

        customer = customers[0]

        # Shartnomalarni olish - get_customer_by_passport dan foydalanish
        result = get_customer_by_passport(customer["custom_phone_1"])

        return result

    except Exception as e:
        frappe.log_error(f"Telegram Contracts Error: {str(e)}", "get_contracts_by_telegram_id")
        return {
            "success": False,
            "message": f"Xatolik: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def get_contract_details(contract_id):
    """
    Bitta shartnoma bo'yicha to'liq ma'lumot va to'lov jadvali.

    Args:
        contract_id (str): Sales Order name

    Returns:
        dict: Shartnoma detallari va to'lov jadvali
    """
    try:
        contract = frappe.get_doc("Sales Order", contract_id)

        # Asosiy ma'lumotlar
        contract_data = {
            "id": contract.name,
            "customer": contract.customer_name,
            "date": contract.transaction_date.strftime("%Y-%m-%d"),
            "total": contract.grand_total,
            "paid": contract.advance_paid,
            "remaining": contract.grand_total - contract.advance_paid,
            "status": contract.status
        }

        # To'lov jadvali
        schedule = []
        for idx, payment in enumerate(contract.payment_schedule, 1):
            schedule.append({
                "month": idx,
                "due_date": payment.due_date.strftime("%Y-%m-%d") if payment.due_date else None,
                "amount": payment.payment_amount,
                "paid": payment.payment_amount - payment.outstanding,
                "outstanding": payment.outstanding,
                "status": "paid" if payment.outstanding == 0 else "pending"
            })

        return {
            "success": True,
            "contract": contract_data,
            "schedule": schedule
        }

    except Exception as e:
        frappe.log_error(f"Contract Details Error: {str(e)}", "get_contract_details")
        return {
            "success": False,
            "message": f"Shartnoma topilmadi: {str(e)}"
        }


@frappe.whitelist(allow_guest=False)
def get_payment_history(customer_id, limit=10):
    """
    Mijozning to'lovlar tarixini qaytaradi.

    Args:
        customer_id (str): Customer name
        limit (int): Qaytariladigan to'lovlar soni

    Returns:
        dict: To'lovlar tarixi
    """
    try:
        payments = frappe.get_all(
            "Payment Entry",
            filters={
                "party": customer_id,
                "party_type": "Customer",
                "docstatus": 1
            },
            fields=[
                "name as id",
                "posting_date as date",
                "paid_amount as amount",
                "mode_of_payment as method",
                "remarks as notes",
                "custom_contract_reference as contract"
            ],
            order_by="posting_date desc",
            limit=limit
        )

        for payment in payments:
            if payment["date"]:
                payment["date"] = payment["date"].strftime("%Y-%m-%d")

        return {
            "success": True,
            "total_payments": len(payments),
            "payments": payments
        }

    except Exception as e:
        frappe.log_error(f"Payment History Error: {str(e)}", "get_payment_history")
        return {
            "success": False,
            "message": f"Xatolik: {str(e)}"
        }
```

---

## 🔧 ERPNext da Custom Field yaratish

### 1. Customer DocType uchun custom fieldlar:

```python
# Custom fieldlarni qo'shish uchun fixtures yoki bench console:

bench --site your-site console

# Keyin:
```

```python
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

custom_fields = {
    "Customer": [
        {
            "fieldname": "custom_telegram_id",
            "label": "Telegram ID",
            "fieldtype": "Data",
            "insert_after": "mobile_no",
            "unique": 1
        },
        {
            "fieldname": "custom_telegram_username",
            "label": "Telegram Username",
            "fieldtype": "Data",
            "insert_after": "custom_telegram_id"
        },
        {
            "fieldname": "custom_phone_1",
            "label": "Passport / Phone",
            "fieldtype": "Data",
            "insert_after": "custom_telegram_username",
            "unique": 1
        }
    ],
    "Payment Entry": [
        {
            "fieldname": "custom_contract_reference",
            "label": "Contract Reference",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "party"
        }
    ]
}

create_custom_fields(custom_fields, update=True)
```

---

## 🔑 API Permission sozlash

API ga kirish uchun token yaratish:

1. ERPNext ga admin sifatida kiring
2. **User** ga o'ting
3. **API Access** -> **Generate Keys**
4. `api_key` va `api_secret` ni saqlang
5. Botning `.env` fayliga qo'shing:

```env
ERP_BASE_URL=https://your-erpnext-site.com
ERP_API_KEY=your_api_key_here
ERP_API_SECRET=your_api_secret_here
```

---

## 🧪 API ni test qilish

cURL orqali:

```bash
curl -X GET "https://your-site.com/api/method/cash_flow_management.api.telegram_bot_api.get_customer_by_passport" \
  -H "Authorization: token api_key:api_secret" \
  -d "passport_series=AA1234567"
```

---

## 📊 Notification sistemasi

Avtomatik xabarlar yuborish uchun ERPNext da Server Script yarating:

**Script Type:** DocType Event
**DocType:** Payment Entry
**Event:** On Submit

```python
import requests
import json

def send_telegram_notification(doc, method):
    """To'lov kiritilganda Telegram orqali xabar yuborish"""

    if not doc.custom_telegram_id:
        return

    # Bot webhook URL
    webhook_url = "https://your-bot-webhook.com/webhook/payment-entry"

    payload = {
        "name": doc.name,
        "party": doc.party,
        "contract": doc.custom_contract_reference,
        "amount": doc.paid_amount,
        "telegram_id": doc.custom_telegram_id
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        frappe.logger().info(f"Telegram notification sent: {response.status_code}")
    except Exception as e:
        frappe.log_error(f"Telegram notification failed: {str(e)}")
```

---

## ✅ Barcha o'zgarishlar:

### Bot tomonida:
1. ✅ Telegram ID avtomatik bog'lanadi
2. ✅ "Mening shartnomalarim" - to'liq ma'lumot ko'rsatadi
3. ✅ PDF yuklab olish funksiyasi
4. ✅ Chiroyli formatlanish
5. ✅ Inline buttonlar to'g'ri ishlaydi

### ERPNext tomonida:
1. ✅ `telegram_bot_api.py` - barcha API methodlar
2. ✅ Custom fieldlar (telegram_id, telegram_username, phone_1)
3. ✅ Notification Server Script
4. ✅ API Permission sozlanishi

---

## 🚀 Ishga tushirish:

```bash
# Bot tomonida
cd /home/user/Documents/erpnext_bot
python app/main.py

# ERPNext tomonida
bench restart
```

Bot endi to'liq ishlashi kerak!
