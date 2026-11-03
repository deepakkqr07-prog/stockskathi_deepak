"""
Presentation Demo Mode Service
Provides one-click setup, realistic Kirana store seed data, and clean reset functionality.
"""

import datetime
from typing import Dict, Any
from backend.database import get_db_collection
from backend.security import hash_password, create_access_token
from backend.services.subscription_service import subscription_service

DEMO_USER_ID = "demo-gupta-kirana-store"

class DemoService:

    @staticmethod
    def seed_demo_data() -> Dict[str, Any]:
        users_coll = get_db_collection("users")
        products_coll = get_db_collection("products")
        suppliers_coll = get_db_collection("suppliers")
        orders_coll = get_db_collection("purchase_orders")
        notifs_coll = get_db_collection("notifications")
        ledger_coll = get_db_collection("stock_ledger")

        # 1. Clean previous demo state
        products_coll.delete_many({"user_id": DEMO_USER_ID})
        suppliers_coll.delete_many({"user_id": DEMO_USER_ID})
        orders_coll.delete_many({"user_id": DEMO_USER_ID})
        notifs_coll.delete_many({"user_id": DEMO_USER_ID})
        ledger_coll.delete_many({"user_id": DEMO_USER_ID})
        users_coll.delete_many({"_id": DEMO_USER_ID})

        now = datetime.datetime.now(datetime.timezone.utc)
        trial_ends = now + datetime.timedelta(days=2)  # "Ends in 2 days"

        # 2. Create Demo User
        demo_user = {
            "_id": DEMO_USER_ID,
            "full_name": "Ramesh Gupta",
            "shop_name": "Gupta Ji Daily Needs & Kirana",
            "phone": "+91 98765 43210",
            "email": "demo@stocksathi.in",
            "password_hash": hash_password("DemoPass@2026"),
            "plan": "FREE",
            "trial_started_at": (now - datetime.timedelta(days=1)).isoformat(),
            "trial_ends_at": trial_ends.isoformat(),
            "has_used_trial": True,
            "is_verified": True,
            "language": "Hindi",
            "is_demo_account": True,
            "created_at": now.isoformat(),
            "settings": {
                "low_stock_threshold": 15,
                "expiry_alert_days": 30,
                "language": "Hindi",
                "voice_speed": "normal"
            }
        }
        users_coll.insert_one(demo_user)

        # 3. Create Demo Suppliers
        suppliers = [
            {
                "user_id": DEMO_USER_ID,
                "name": "ABC Wholesale Distributors",
                "contact_person": "Vipin Aggarwal",
                "phone": "+91 98101 23456",
                "email": "vipin@abcwholesale.in",
                "address": "Shop 14, Main Mandi, Sector 18",
                "categories": ["Groceries", "Snacks", "Noodles"],
                "delivery_time_days": 1,
                "reliability_score": 98,
                "min_order_amount": 1500,
                "payment_terms": "Net 7 Days Credit",
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "name": "Balaji FMCG Mandi Agency",
                "contact_person": "Suresh Singhal",
                "phone": "+91 98202 34567",
                "email": "balajifmcg@gmail.com",
                "address": "Grain Market, Godown 4B",
                "categories": ["Staples", "Oils", "Sugar", "Spices"],
                "delivery_time_days": 3,
                "reliability_score": 88,
                "min_order_amount": 3000,
                "payment_terms": "Cash / UPI on Delivery",
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "name": "Metro Cash & Carry Hub",
                "contact_person": "Customer Desk",
                "phone": "+91 98303 45678",
                "email": "orders@metro-hub.in",
                "address": "Commercial Complex, GT Road",
                "categories": ["Dairy", "Chocolates", "Beverages"],
                "delivery_time_days": 0,
                "reliability_score": 99,
                "min_order_amount": 500,
                "payment_terms": "Instant Digital Billing",
                "created_at": now.isoformat()
            }
        ]
        suppliers_coll.insert_many(suppliers)

        # 4. Create Demo Products
        products = [
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Maggi 2-Minute Noodles",
                "category": "Snacks",
                "quantity": 20,
                "unit": "packet",
                "purchase_price": 12.00,
                "selling_price": 14.00,
                "supplier_name": "ABC Wholesale Distributors",
                "min_stock_level": 25,
                "expiry_date": (now + datetime.timedelta(days=180)).date().isoformat(),
                "batch_number": "MG-2026A",
                "last_sold_date": now.date().isoformat(),
                "monthly_sales_avg": 240,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Parle-G Gold Biscuits 250g",
                "category": "Snacks",
                "quantity": 15,
                "unit": "packet",
                "purchase_price": 22.00,
                "selling_price": 25.00,
                "supplier_name": "ABC Wholesale Distributors",
                "min_stock_level": 20,
                "expiry_date": (now + datetime.timedelta(days=120)).date().isoformat(),
                "batch_number": "PG-88",
                "last_sold_date": now.date().isoformat(),
                "monthly_sales_avg": 120,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Amul Taaza Milk 500ml",
                "category": "Dairy",
                "quantity": 8,
                "unit": "packet",
                "purchase_price": 26.00,
                "selling_price": 28.00,
                "supplier_name": "Metro Cash & Carry Hub",
                "min_stock_level": 15,
                "expiry_date": (now + datetime.timedelta(days=2)).date().isoformat(),  # 2 days left
                "batch_number": "AM-02",
                "last_sold_date": now.date().isoformat(),
                "monthly_sales_avg": 180,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Cadbury Dairy Milk Silk 60g",
                "category": "Snacks",
                "quantity": 35,
                "unit": "piece",
                "purchase_price": 70.00,
                "selling_price": 80.00,
                "supplier_name": "Metro Cash & Carry Hub",
                "min_stock_level": 10,
                "expiry_date": (now + datetime.timedelta(days=14)).date().isoformat(), # 14 days left
                "batch_number": "CDM-41",
                "last_sold_date": (now - datetime.timedelta(days=2)).date().isoformat(),
                "monthly_sales_avg": 45,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Madhur Pure Crystal Sugar",
                "category": "Groceries",
                "quantity": 45,
                "unit": "kg",
                "purchase_price": 42.00,
                "selling_price": 48.00,
                "supplier_name": "Balaji FMCG Mandi Agency",
                "min_stock_level": 20,
                "expiry_date": (now + datetime.timedelta(days=300)).date().isoformat(),
                "batch_number": "SUG-99",
                "last_sold_date": now.date().isoformat(),
                "monthly_sales_avg": 160,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Fortune Sunlite Refined Oil 1L",
                "category": "Groceries",
                "quantity": 12,
                "unit": "pouch",
                "purchase_price": 135.00,
                "selling_price": 155.00,
                "supplier_name": "Balaji FMCG Mandi Agency",
                "min_stock_level": 15,
                "expiry_date": (now + datetime.timedelta(days=180)).date().isoformat(),
                "batch_number": "FO-103",
                "last_sold_date": now.date().isoformat(),
                "monthly_sales_avg": 65,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "India Gate Basmati Rice Feast 5kg",
                "category": "Groceries",
                "quantity": 18,
                "unit": "bag",
                "purchase_price": 380.00,
                "selling_price": 450.00,
                "supplier_name": "Balaji FMCG Mandi Agency",
                "min_stock_level": 8,
                "expiry_date": (now + datetime.timedelta(days=365)).date().isoformat(),
                "batch_number": "IGR-05",
                "last_sold_date": (now - datetime.timedelta(days=1)).date().isoformat(),
                "monthly_sales_avg": 30,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "product_name": "Classmate Long Notebook 120p",
                "category": "Stationery",
                "quantity": 60,
                "unit": "piece",
                "purchase_price": 45.00,
                "selling_price": 60.00,
                "supplier_name": "ABC Wholesale Distributors",
                "min_stock_level": 10,
                "expiry_date": None,
                "batch_number": "ST-01",
                "last_sold_date": (now - datetime.timedelta(days=48)).date().isoformat(), # Dead money!
                "monthly_sales_avg": 5,
                "created_at": now.isoformat()
            }
        ]
        products_coll.insert_many(products)

        # 5. Pre-seeded Notifications
        notifs = [
            {
                "user_id": DEMO_USER_ID,
                "type": "DECISION_ALERT",
                "title": "⚠️ 3 Products Need Your Attention Today",
                "message": "Maggi is below safety buffer (20 remaining). Amul Milk expires in 2 days. Classmate notebooks have ₹2,700 stuck capital.",
                "is_read": False,
                "created_at": now.isoformat()
            },
            {
                "user_id": DEMO_USER_ID,
                "type": "TRIAL_BANNER",
                "title": "✨ Premium Trial Active",
                "message": "Your 3-day full access pass expires in 2 days. All AI Decision Engines unlocked.",
                "is_read": False,
                "created_at": now.isoformat()
            }
        ]
        notifs_coll.insert_many(notifs)

        token = create_access_token({"sub": DEMO_USER_ID})
        sub_status = subscription_service.get_user_subscription_status(demo_user)

        return {
            "token": token,
            "user": {
                "id": DEMO_USER_ID,
                "full_name": demo_user["full_name"],
                "shop_name": demo_user["shop_name"],
                "email": demo_user["email"],
                "phone": demo_user["phone"],
                "is_verified": True,
                "language": "Hindi",
                "is_demo_account": True,
                "subscription": sub_status
            },
            "message": "Demo mode activated! Loaded Gupta Ji Kirana Store with live sample data."
        }

demo_service = DemoService()
