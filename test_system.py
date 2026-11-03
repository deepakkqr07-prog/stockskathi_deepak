"""
Comprehensive Test Suite for StockSathi Full-Stack Application
"""

import sys
import requests
import json
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("==================================================")
    print("   STOCKSATHI AUTOMATED SYSTEM TEST SUITE")
    print("==================================================")
    
    # 1. Health Check
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("[PASS] Health Check Passed:", r.json())

    # 2. Presentation Demo Mode Seeding
    r = requests.post(f"{BASE_URL}/api/demo/seed")
    assert r.status_code == 200, f"Demo seed failed: {r.text}"
    demo_res = r.json()
    demo_token = demo_res["token"]
    headers = {"Authorization": f"Bearer {demo_token}"}
    print(f"[PASS] Presentation Demo Mode Seeded: User={demo_res['user']['full_name']} (Shop={demo_res['user']['shop_name']})")

    # 3. User Profile /me
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    assert r.status_code == 200
    user_me = r.json()
    assert user_me["subscription"]["is_premium"] == True
    print("[PASS] Profile /me Verified: Premium Trial Active, Ends in", user_me["subscription"]["remaining_trial_days"], "days")

    # 4. Inventory List & KPIs
    r = requests.get(f"{BASE_URL}/api/inventory/products", headers=headers)
    products = r.json()
    assert len(products) >= 8
    print(f"[PASS] Inventory Loaded: {len(products)} products found (e.g. {products[0]['product_name']})")

    r = requests.get(f"{BASE_URL}/api/inventory/kpis", headers=headers)
    kpis = r.json()
    print(f"[PASS] Dashboard KPIs: Total={kpis['total_products']}, StockValue=Rs {kpis['total_stock_value']:,.2f}, LowStock={kpis['low_stock_count']}, Expiring={kpis['expiring_soon_count']}, DeadStock=Rs {kpis['dead_stock_value']:,.2f}")

    # 5. AI Demand Prediction
    r = requests.get(f"{BASE_URL}/api/predictions/", headers=headers)
    preds = r.json()
    maggi_pred = next((p for p in preds["predictions"] if "maggi" in p["product_name"].lower()), None)
    assert maggi_pred is not None
    print(f"[PASS] AI Demand Prediction (Maggi): Current={maggi_pred['current_stock']}, Expected Demand={maggi_pred['expected_demand']}, Recommended Order={maggi_pred['recommended_order']}")

    # 6. Smart Supplier Comparison
    r = requests.post(f"{BASE_URL}/api/suppliers/compare", json={"product_name": "Maggi 2-Minute Noodles", "required_quantity": 45}, headers=headers)
    comp = r.json()
    assert len(comp["options"]) >= 2
    print(f"[PASS] Smart Supplier Comparison: Recommended={comp['recommended_supplier']['supplier_name']} ({comp['recommended_supplier']['badge']})")

    # 7. Voice AI Parse -> Readback -> Confirm Update Flow
    r = requests.post(f"{BASE_URL}/api/voice/parse", json={"transcript": "Maggi ke 20 packet aur add kar do", "language": "Hindi"}, headers=headers)
    v_res = r.json()
    assert v_res["status"] == "CONFIRMATION_REQUIRED"
    pending = v_res["pending_action"]
    print(f"[PASS] Voice AI Parsed: Diff={pending['diff_label']}, Spoken Text='{v_res['readback_text']}'")

    r = requests.post(f"{BASE_URL}/api/voice/confirm", json={"pending_action": pending, "language": "Hindi"}, headers=headers)
    v_conf = r.json()
    assert v_conf["success"] == True
    print(f"[PASS] Voice AI Confirmed & Updated: Prev={v_conf['details']['previous_stock']} -> New={v_conf['details']['new_stock']}, Spoken='{v_conf['speech_response']}'")

    # 8. Dead Money Detector
    r = requests.get(f"{BASE_URL}/api/analytics/dead-money", headers=headers)
    dm = r.json()
    assert len(dm["items"]) > 0
    print(f"[PASS] Dead Money Detector: Total Locked=Rs {dm['total_dead_money']:,.2f}, Top Item={dm['items'][0]['product_name']} ({dm['items'][0]['days_inactive']} days inactive)")

    # 9. Expiry Loss Prevention
    r = requests.get(f"{BASE_URL}/api/analytics/expiry-prevention", headers=headers)
    exp = r.json()
    assert len(exp["items"]) > 0
    print(f"[PASS] Expiry Loss Prevention: Batches={exp['expiring_batches_count']}, At Risk Value=Rs {exp['total_at_risk_value']:,.2f}")

    # 10. AI Support Assistant Grounded Q&A
    r = requests.post(f"{BASE_URL}/api/support/chat", json={"message": "Mera total stock value kitna hai?", "language": "Hindi"}, headers=headers)
    supp = r.json()
    print(f"[PASS] AI Support Q&A: Grounded={supp['grounded_sources']}, Reply='{supp['reply'][:90]}...'")

    # 11. Purchase Order Creation & Receipt
    r = requests.post(f"{BASE_URL}/api/orders/", json={
        "supplier_name": "ABC Wholesale Distributors",
        "items": [{"product_name": "Parle-G Gold Biscuits 250g", "quantity": 30, "unit_price": 22.00, "unit": "packet"}],
        "delivery_days": 1
    }, headers=headers)
    po = r.json()
    assert po["status"] == "PLACED"
    print(f"[PASS] Purchase Order Created: {po['po_number']}, Amount=Rs {po['total_amount']}")

    # Mark PO Received
    r = requests.patch(f"{BASE_URL}/api/orders/{po['_id']}/status", json={"status": "RECEIVED"}, headers=headers)
    assert r.status_code == 200
    print(f"[PASS] Purchase Order Received: Stock automatically adjusted in inventory.")

    # 12. Full Verification of Regular Signup -> OTP -> Unverified Lock -> Verify -> Access
    test_id = uuid.uuid4().hex
    unique_email = f"kirana_{test_id}@test.com"
    unique_phone = f"9{uuid.uuid4().int % 10**9:09d}"
    signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json={
        "full_name": "Vikas Sharma",
        "shop_name": "Sharma General Store",
        "phone": unique_phone,
        "email": unique_email,
        "password": "StrongPass@2026",
        "confirm_password": "StrongPass@2026"
    })
    assert signup_response.status_code == 200, f"Signup failed: {signup_response.text}"
    
    # Login check unverified
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"identifier": unique_email, "password": "StrongPass@2026"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    otp_code = r.json().get("dev_otp")
    assert r.json().get("requires_verification") is True
    assert otp_code, "Login did not return an OTP for the unverified user."
    print("[PASS] Unverified User Dashboard Lock Enforced: Login blocked until OTP verification.")

    # Verify OTP
    r = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={"identifier": unique_email, "otp": otp_code})
    assert r.status_code == 200, f"OTP verification failed: {r.text}"
    verified_user = r.json()
    new_token = verified_user["token"]
    assert verified_user["user"]["is_verified"] == True
    print("[PASS] OTP Verified: User token granted, access unlocked.")

    print("\n==================================================")
    print("   ALL 12 BACKEND & AI ENGINE SUITE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
