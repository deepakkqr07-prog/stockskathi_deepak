# STOCKSATHI — Smart Retail Decision Engine

> **PREDICT → DECIDE → RECOMMEND → ACT**  
> An AI-powered business copilot for every small retailer and Kirana shopkeeper.

---

## 🌟 Overview

StockSathi is a full-stack SaaS application built specifically for small shopkeepers. Unlike traditional passive inventory loggers, StockSathi operates on a proactive **Predict → Decide → Recommend → Act** decision cycle to prevent stock-outs, avoid expiry loss, unlock trapped dead money, and automate smart supplier purchases.

---

## 🚀 Key Features

1. **AI Decision Engine**:
   - **PREDICT**: Forecasts 7-day consumer demand using sales velocity and seasonal buffers.
   - **DECIDE**: Detects stock deficit and days-to-stockout.
   - **RECOMMEND**: Recommends exact reorder quantities and optimal wholesale Mandi suppliers.
   - **ACT**: Generates 1-click purchase orders with automated stock ledger updates upon receipt.

2. **Voice AI Assistant (Hindi / Punjabi / Hinglish / English)**:
   - Hands-free voice operation using the strict protocol:  
     `SPEAK → UNDERSTAND → READ BACK (+DIFF) → CONFIRM/CHANGE → DATABASE UPDATE → VOICE SUCCESS FEEDBACK`
   - Example: *"Maggi ke 20 packet aur add kar do"* → Reads back Previous: 20, Change: +20, New: 40 → Waits for *"Haan"* → Updates stock and speaks *"Ho gaya ji!"*.

3. **Dead Money Detector**:
   - Scans slow-moving inventory to pinpoint trapped working capital (>30/60 days inactive) with actionable liquidation strategies.

4. **Expiry Loss Prevention**:
   - Tracks batches expiring in 7, 15, and 30 days with immediate promotional discount and supplier return suggestions.

5. **Smart Mandi Supplier Comparison**:
   - Compares wholesale vendors across Price per Unit, Delivery Lead Time (1-day vs 3-day), and Reliability Ratings.

6. **Daily Business Assistant**:
   - Morning prioritized checklist of top retail actions.

7. **AI Support Assistant (Chat Drawer)**:
   - Answers shopkeeper questions grounded strictly in live database facts with safety confirmation for write operations.

8. **Presentation Demo Mode**:
   - 1-Click presentation launcher loaded with realistic Kirana store inventory (*Maggi, Parle-G, Amul Milk, Dairy Milk, Sugar, Fortune Oil, Rice, Classmate Notebooks*).
   - Built-in 9-Step Guided Walkthrough runner.
   - 1-Click `[Reset Demo]` button.

---

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML5, Vanilla CSS3 (Custom Design System with CSS tokens, responsive layout, NO robot/sparkle AI gimmicks), Modular ES6 JavaScript.
- **Backend**: Python 3.12, FastAPI, Uvicorn, PyMongo, PyJWT, Passlib/Bcrypt.
- **Database Layer**: MongoDB client with automatic seamless persistent JSON fallback if local MongoDB service is offline.

---

## 🏁 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Application Server
```bash
python run.py
```
Open your browser at **http://127.0.0.1:8000**

### 3. Configure Supabase

Set `SUPABASE_URL` and `SUPABASE_KEY` in `backend/.env`. Replace the key
placeholder with a Supabase API key before using the connection check. Verify
the configuration at **http://127.0.0.1:8000/test-db**.

---

## 👥 Presentation Demo Guide

1. Click **[Try Live Demo]** on the landing page.
2. The system loads *Gupta Ji Daily Needs & Kirana* under an active 3-Day Premium Trial.
3. Follow the floating **9-Step Demo Walkthrough** bar at the bottom:
   - **Step 1**: Review KPI cards & alerts on the Dashboard.
   - **Step 2**: Open Demand Prediction (Maggi expected demand: 56, recommended order: 45).
   - **Step 3**: Compare Mandi suppliers (ABC Wholesale vs Balaji FMCG).
   - **Step 4**: Speak to StockSathi (*"Maggi ke 20 packet aur add kar do"*).
   - **Step 5**: Review Read-back Diff Card & Confirm with *"Haan"*.
   - **Step 6**: Hear spoken confirmation feedback and view updated stock.
   - **Step 7**: Inspect Dead Money Detector (Classmate notebooks ₹2,700 stuck capital).
   - **Step 8**: Inspect Expiry Prevention (Amul Milk expiring in 2 days).
   - **Step 9**: Ask AI Support Assistant *"Aaj mujhe shop mein kya karna chahiye?"*.
