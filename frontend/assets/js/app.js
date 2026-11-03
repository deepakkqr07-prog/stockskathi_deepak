/**
 * Main Application Orchestrator & View Renderers
 */

const App = {
  activeEditProductId: null,

  async init() {
    console.log("[StockSathi] Initializing Application...");
    
    // Check if auth token exists and fetch user profile
    const token = API.getToken();
    if (token) {
      try {
        const profile = await API.get("/api/auth/me");
        Store.setUser(profile);
      } catch (e) {
        console.warn("[App Init] Token invalid or expired, resetting.");
        API.setToken(null);
      }
    }

    // Initialize modules
    Auth.init();
    SubscriptionService.init();
    VoiceService.init();
    SupportService.init();
    Router.init();

    this.bindGlobalEvents();

    // Subscribe store to trigger re-renders
    Store.subscribe((state) => {
      this.updateUserInterface(state);
    });

    if (Store.state.isAuthenticated) {
      this.refreshDashboardData();
    }
  },

  bindGlobalEvents() {
    // Add product form
    const addProductForm = document.getElementById("add-product-form");
    if (addProductForm) {
      addProductForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleAddProduct();
      });
    }

    // Edit product form
    const editProductForm = document.getElementById("edit-product-form");
    if (editProductForm) {
      editProductForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleEditProduct();
      });
    }

    // Create supplier form
    const addSupplierForm = document.getElementById("add-supplier-form");
    if (addSupplierForm) {
      addSupplierForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleAddSupplier();
      });
    }

    // Inventory search & category filters
    const searchInput = document.getElementById("inventory-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.loadInventoryData(e.target.value, document.getElementById("inventory-category-filter")?.value);
      });
    }

    const categoryFilter = document.getElementById("inventory-category-filter");
    if (categoryFilter) {
      categoryFilter.addEventListener("change", (e) => {
        this.loadInventoryData(document.getElementById("inventory-search-input")?.value, e.target.value);
      });
    }
  },

  async refreshDashboardData() {
    if (!Store.state.isAuthenticated) return;

    try {
      // Parallel fetch for speed
      const [kpis, products, notifs, dailyActions] = await Promise.all([
        API.get("/api/inventory/kpis"),
        API.get("/api/inventory/products"),
        API.get("/api/notifications/"),
        API.get("/api/analytics/daily-assistant").catch(() => ({ actions: [] }))
      ]);

      Store.state.kpis = kpis;
      Store.state.products = products;
      Store.state.notifications = notifs.notifications || [];
      Store.state.unreadNotifsCount = notifs.unread_count || 0;
      Store.state.dailyActions = dailyActions.actions || [];
      Store.notify();

      this.renderKPICards(kpis);
      this.renderInventoryTable(products);
      this.renderDailyChecklist(dailyActions.actions || []);
      this.renderNotificationsList(notifs.notifications || []);

      // If Premium/Trial, fetch advanced engines
      if (Store.isPremium()) {
        this.loadAdvancedAnalytics();
      } else {
        this.renderLockedPreviews();
      }
    } catch (err) {
      console.error("[Refresh Dashboard Error]:", err);
    }
  },

  async loadAdvancedAnalytics() {
    try {
      const [predictions, deadMoney, expiryReport, suppliers, orders] = await Promise.all([
        API.get("/api/predictions/").catch(() => ({ predictions: [] })),
        API.get("/api/analytics/dead-money").catch(() => ({ items: [] })),
        API.get("/api/analytics/expiry-prevention").catch(() => ({ items: [] })),
        API.get("/api/suppliers/").catch(() => []),
        API.get("/api/orders/").catch(() => [])
      ]);

      Store.state.predictions = predictions.predictions || [];
      Store.state.topActionItem = predictions.top_action_item;
      Store.state.deadMoney = deadMoney;
      Store.state.expiryReport = expiryReport;
      Store.state.suppliers = suppliers;
      Store.state.orders = orders;

      this.renderDecisionEngineHero(predictions.top_action_item);
      this.renderPredictionsView(predictions.predictions || []);
      this.renderDeadMoneyView(deadMoney);
      this.renderExpiryView(expiryReport);
      this.renderSuppliersView(suppliers);
      this.renderOrdersView(orders);
    } catch (e) {
      console.error("[Advanced Analytics Load Error]:", e);
    }
  },

  updateUserInterface(state) {
    const user = state.user;
    if (!user) return;

    // Update Topbar Greeting & Shop Name
    const greetingEl = document.getElementById("topbar-greeting-name");
    const shopNameEl = document.getElementById("topbar-shop-name");
    const planBadge = document.getElementById("topbar-plan-badge");
    const trialBanner = document.getElementById("trial-countdown-banner");
    const trialRemainingText = document.getElementById("trial-remaining-text");
    const sidebarAvatar = document.getElementById("sidebar-user-avatar");
    const sidebarName = document.getElementById("sidebar-user-name");
    const sidebarShop = document.getElementById("sidebar-shop-name");

    const hour = new Date().getHours();
    const timeGreeting = hour < 12 ? "Good Morning" : (hour < 17 ? "Good Afternoon" : "Good Evening");

    if (greetingEl) greetingEl.textContent = `${timeGreeting}, ${user.full_name}`;
    if (shopNameEl) shopNameEl.textContent = user.shop_name;
    if (sidebarAvatar) sidebarAvatar.textContent = user.full_name.charAt(0).toUpperCase();
    if (sidebarName) sidebarName.textContent = user.full_name;
    if (sidebarShop) sidebarShop.textContent = user.shop_name;

    const sub = user.subscription || {};
    if (planBadge) {
      planBadge.textContent = sub.effective_plan || "FREE";
      planBadge.className = `badge ${sub.is_premium ? 'badge-primary' : 'badge-neutral'}`;
    }

    if (trialBanner) {
      if (sub.is_trial_active) {
        trialBanner.classList.remove("hidden");
        if (trialRemainingText) {
          trialRemainingText.textContent = `Your 3-Day Premium Trial ends in ${sub.remaining_trial_days || 2} days. All AI Decision Engines are unlocked.`;
        }
      } else {
        trialBanner.classList.add("hidden");
      }
    }

    // Update Demo banner if demo account
    if (user.is_demo_account) {
      DemoService.renderDemoRunnerUI(true);
    }
  },

  renderKPICards(kpis) {
    const totalProds = document.getElementById("kpi-total-products");
    const stockVal = document.getElementById("kpi-stock-value");
    const lowStock = document.getElementById("kpi-low-stock");
    const expiring = document.getElementById("kpi-expiring");
    const deadStock = document.getElementById("kpi-dead-stock");

    if (totalProds) totalProds.textContent = kpis.total_products;
    if (stockVal) stockVal.textContent = `₹${(kpis.total_stock_value || 0).toLocaleString('en-IN')}`;
    if (lowStock) lowStock.textContent = kpis.low_stock_count;
    if (expiring) expiring.textContent = kpis.expiring_soon_count;
    if (deadStock) deadStock.textContent = `₹${(kpis.dead_stock_value || 0).toLocaleString('en-IN')}`;
  },

  renderDecisionEngineHero(topItem) {
    const container = document.getElementById("decision-engine-hero-card");
    if (!container) return;

    if (!Store.isPremium()) {
      container.innerHTML = `
        <div class="decision-engine-header">
          <div>
            <h3 style="font-size: 1.25rem; font-weight: 800;">Smart Retail Decision Engine</h3>
            <p style="font-size: 0.875rem; color: #A7F3D0;">PREDICT → DECIDE → RECOMMEND → ACT</p>
          </div>
          <span class="locked-badge-pill">🔒 Premium Feature</span>
        </div>
        <div style="background: rgba(0,0,0,0.2); border-radius: 12px; padding: 24px; text-align: center;">
          <p style="font-size: 0.9375rem; margin-bottom: 16px;">AI Demand Forecasting and automated Purchase Recommendations are unlocked on Premium.</p>
          <button class="btn btn-amber" onclick="SubscriptionService.startFreeTrial()">Start 3-Day Free Trial</button>
        </div>
      `;
      return;
    }

    if (!topItem) {
      container.innerHTML = `
        <div class="decision-engine-header">
          <div>
            <h3 style="font-size: 1.25rem; font-weight: 800;">Decision Engine Status: Optimal</h3>
            <p style="font-size: 0.875rem; color: #A7F3D0;">All key inventory lines are balanced.</p>
          </div>
        </div>
      `;
      return;
    }

    const p = topItem.pipeline;
    container.innerHTML = `
      <div class="decision-engine-header">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 800;">AI Decision Engine: ${topItem.product_name}</h3>
          <p style="font-size: 0.8125rem; color: #A7F3D0;">Core Workflow: PREDICT → DECIDE → RECOMMEND → ACT</p>
        </div>
        <span class="engine-tag">92% PREDICTION CONFIDENCE</span>
      </div>
      <div class="decision-steps-container">
        <div class="decision-step-box">
          <span class="step-label-title">1. PREDICT</span>
          <p class="step-content-text">${p.predict}</p>
        </div>
        <div class="decision-step-box">
          <span class="step-label-title">2. DECIDE</span>
          <p class="step-content-text">${p.decide}</p>
        </div>
        <div class="decision-step-box">
          <span class="step-label-title">3. RECOMMEND</span>
          <p class="step-content-text">${p.recommend}</p>
        </div>
        <div class="decision-step-box" style="display: flex; flex-direction: column; justify-content: space-between;">
          <span class="step-label-title">4. ACT</span>
          <button class="btn decision-act-btn" onclick="App.triggerGeneratePO('${topItem.product_name}', ${topItem.recommended_order}, '${topItem.supplier_name}', 12.00)">
            Create Purchase Order
          </button>
        </div>
      </div>
    `;
  },

  renderDailyChecklist(actions) {
    const list = document.getElementById("daily-actions-checklist");
    if (!list) return;

    if (!actions || actions.length === 0) {
      list.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-muted);">No urgent actions pending today.</div>`;
      return;
    }

    list.innerHTML = actions.map(act => `
      <div class="checklist-item">
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge badge-${act.badge_color}">${act.badge}</span>
            <strong style="font-size: 0.9375rem; color: var(--text-main);">${act.title}</strong>
          </div>
          <p style="font-size: 0.8125rem; color: var(--text-muted);">${act.description}</p>
        </div>
        <button class="btn btn-outline btn-sm" onclick="App.handleActionClick('${act.action_type}', ${JSON.stringify(act.action_payload).replace(/"/g, '&quot;')})">
          ${act.button_label}
        </button>
      </div>
    `).join("");
  },

  handleActionClick(actionType, payload) {
    if (actionType === "CREATE_PO") {
      this.triggerGeneratePO(payload.product_name, payload.recommended_qty || 30, "ABC Wholesale Distributors", 12.00);
    } else if (actionType === "NAVIGATE_EXPIRY") {
      Router.navigate("expiry");
    } else if (actionType === "NAVIGATE_DEAD_MONEY") {
      Router.navigate("dead-stock");
    } else if (actionType === "OPEN_VOICE") {
      VoiceService.openVoiceModal();
    }
  },

  async loadInventoryData(search = "", category = "ALL") {
    try {
      const products = await API.get(`/api/inventory/products?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}`);
      this.renderInventoryTable(products);
    } catch (e) {
      console.error("Failed to filter inventory", e);
    }
  },

  renderInventoryTable(products) {
    const tbody = document.getElementById("inventory-table-body");
    if (!tbody) return;

    if (!products || products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">No products found matching your search.</td></tr>`;
      return;
    }

    tbody.innerHTML = products.map(p => {
      let statusBadge = `<span class="badge badge-success">In Stock</span>`;
      if (p.is_out_of_stock) {
        statusBadge = `<span class="badge badge-danger">Out of Stock</span>`;
      } else if (p.is_low_stock) {
        statusBadge = `<span class="badge badge-warning">Low Stock (${p.quantity})</span>`;
      }

      return `
        <tr>
          <td>
            <div style="font-weight: 700; color: var(--text-main);">${p.product_name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${p.category} • Batch: ${p.batch_number || 'B-01'}</div>
          </td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <button class="btn btn-secondary btn-sm" style="padding: 2px 8px;" onclick="App.adjustStockDirect('${p._id}', -1)">-</button>
              <strong style="font-size: 1rem;">${p.quantity}</strong>
              <span style="font-size: 0.8125rem; color: var(--text-muted);">${p.unit}s</span>
              <button class="btn btn-secondary btn-sm" style="padding: 2px 8px;" onclick="App.adjustStockDirect('${p._id}', 1)">+</button>
            </div>
          </td>
          <td>₹${p.purchase_price.toFixed(2)}</td>
          <td>₹${p.selling_price.toFixed(2)}</td>
          <td>
            <div>${p.supplier_name || 'Direct'}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Min Level: ${p.min_stock_level}</div>
          </td>
          <td>${statusBadge}</td>
          <td>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-secondary btn-sm" onclick="App.openEditProductModal('${p._id}')">Edit</button>
              <button class="btn btn-outline btn-sm" style="color: var(--crimson-danger); border-color: #FECACA;" onclick="App.deleteProductItem('${p._id}')">Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  async adjustStockDirect(productId, delta) {
    try {
      const res = await API.patch("/api/inventory/adjust-stock", {
        product_name_or_id: productId,
        delta,
        reason: "Quick +/- adjustment"
      });
      this.showToast(res.message, "success");
      this.refreshDashboardData();
    } catch (e) {
      this.showToast(e.message, "error");
    }
  },

  async handleAddProduct() {
    const name = document.getElementById("add-prod-name").value.trim();
    const category = document.getElementById("add-prod-category").value;
    const quantity = parseInt(document.getElementById("add-prod-qty").value) || 0;
    const unit = document.getElementById("add-prod-unit").value;
    const purchasePrice = parseFloat(document.getElementById("add-prod-cost").value) || 0;
    const sellingPrice = parseFloat(document.getElementById("add-prod-price").value) || 0;
    const supplier = document.getElementById("add-prod-supplier").value.trim();
    const minLevel = parseInt(document.getElementById("add-prod-min").value) || 10;
    const expiry = document.getElementById("add-prod-expiry").value || null;

    if (!name) {
      this.showToast("Product name is required", "error");
      return;
    }

    this.showLoading("Adding product to inventory...");
    try {
      await API.post("/api/inventory/products", {
        product_name: name,
        category,
        quantity,
        unit,
        purchase_price: purchasePrice,
        selling_price: sellingPrice,
        supplier_name: supplier,
        min_stock_level: minLevel,
        expiry_date: expiry
      });

      this.hideLoading();
      this.closeModal("modal-add-product");
      document.getElementById("add-product-form").reset();
      this.showToast(`✓ Product '${name}' added to inventory.`, "success");
      this.refreshDashboardData();
    } catch (e) {
      this.hideLoading();
      this.showToast(e.message, "error");
    }
  },

  async openEditProductModal(productId) {
    this.activeEditProductId = productId;
    try {
      const prod = await API.get(`/api/inventory/products/${productId}`);
      document.getElementById("edit-prod-name").value = prod.product_name;
      document.getElementById("edit-prod-category").value = prod.category;
      document.getElementById("edit-prod-qty").value = prod.quantity;
      document.getElementById("edit-prod-unit").value = prod.unit;
      document.getElementById("edit-prod-cost").value = prod.purchase_price;
      document.getElementById("edit-prod-price").value = prod.selling_price;
      document.getElementById("edit-prod-supplier").value = prod.supplier_name || "";
      document.getElementById("edit-prod-min").value = prod.min_stock_level;
      document.getElementById("edit-prod-expiry").value = prod.expiry_date || "";

      this.openModal("modal-edit-product");
    } catch (e) {
      this.showToast("Could not load product details.", "error");
    }
  },

  async handleEditProduct() {
    if (!this.activeEditProductId) return;

    this.showLoading("Saving changes...");
    try {
      await API.put(`/api/inventory/products/${this.activeEditProductId}`, {
        product_name: document.getElementById("edit-prod-name").value.trim(),
        category: document.getElementById("edit-prod-category").value,
        quantity: parseInt(document.getElementById("edit-prod-qty").value),
        unit: document.getElementById("edit-prod-unit").value,
        purchase_price: parseFloat(document.getElementById("edit-prod-cost").value),
        selling_price: parseFloat(document.getElementById("edit-prod-price").value),
        supplier_name: document.getElementById("edit-prod-supplier").value.trim(),
        min_stock_level: parseInt(document.getElementById("edit-prod-min").value),
        expiry_date: document.getElementById("edit-prod-expiry").value || null
      });

      this.hideLoading();
      this.closeModal("modal-edit-product");
      this.showToast("✓ Product information updated successfully.", "success");
      this.refreshDashboardData();
    } catch (e) {
      this.hideLoading();
      this.showToast(e.message, "error");
    }
  },

  async deleteProductItem(productId) {
    if (!confirm("Are you sure you want to remove this product from inventory?")) return;

    try {
      await API.delete(`/api/inventory/products/${productId}`);
      this.showToast("Product deleted.", "info");
      this.refreshDashboardData();
    } catch (e) {
      this.showToast(e.message, "error");
    }
  },

  renderPredictionsView(predictions) {
    const list = document.getElementById("predictions-grid-container");
    if (!list) return;

    list.innerHTML = predictions.map(p => `
      <div class="card">
        <div class="card-header">
          <div>
            <h4 class="card-title">${p.product_name}</h4>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${p.category}</span>
          </div>
          <span class="badge ${p.urgency === 'HIGH' ? 'badge-danger' : (p.urgency === 'MEDIUM' ? 'badge-warning' : 'badge-neutral')}">${p.urgency} URGENCY</span>
        </div>
        <div class="card-body" style="display: flex; flex-direction: column; gap: 14px;">
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; background: #F8FAFC; padding: 12px; border-radius: 8px;">
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">Current Stock</div>
              <strong style="font-size: 1.25rem;">${p.current_stock}</strong>
            </div>
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">Exp. Demand</div>
              <strong style="font-size: 1.25rem; color: var(--info-blue);">${p.expected_demand}</strong>
            </div>
            <div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">Rec. Order</div>
              <strong style="font-size: 1.25rem; color: var(--emerald-success);">${p.recommended_order}</strong>
            </div>
          </div>
          
          <div style="font-size: 0.8125rem; background: #ECFDF5; border-left: 3px solid #059669; padding: 10px; border-radius: 4px;">
            <strong>AI Rationale:</strong> ${p.pipeline.recommend}
          </div>

          ${p.recommended_order > 0 ? `
            <button class="btn btn-primary btn-sm" style="margin-top: 8px;" onclick="App.triggerGeneratePO('${p.product_name}', ${p.recommended_order}, '${p.supplier_name}', 12.00)">
              Generate Purchase Order (${p.recommended_order} units)
            </button>
          ` : ''}
        </div>
      </div>
    `).join("");
  },

  renderDeadMoneyView(deadMoney) {
    const summaryVal = document.getElementById("dead-money-total-val");
    const summaryTip = document.getElementById("dead-money-summary-tip");
    const tbody = document.getElementById("dead-money-table-body");

    if (summaryVal) summaryVal.textContent = `₹${(deadMoney.total_dead_money || 0).toLocaleString('en-IN')}`;
    if (summaryTip) summaryTip.textContent = deadMoney.summary_tip || "";
    if (!tbody) return;

    if (!deadMoney.items || deadMoney.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 24px; color: var(--text-muted);">No slow-moving dead capital detected.</td></tr>`;
      return;
    }

    tbody.innerHTML = deadMoney.items.map(it => `
      <tr>
        <td>
          <div style="font-weight: 700;">${it.product_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${it.category}</div>
        </td>
        <td>${it.quantity} ${it.unit}s</td>
        <td><strong style="color: var(--crimson-danger);">₹${it.money_stuck.toLocaleString('en-IN')}</strong></td>
        <td>${it.days_inactive} days ago</td>
        <td><span class="badge ${it.risk_level === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}">${it.risk_level}</span></td>
        <td style="font-size: 0.8125rem;">
          <div>${it.recommendation}</div>
          <button class="btn btn-secondary btn-sm" style="margin-top: 6px;" onclick="App.showToast('Clearance offer activated for ${it.product_name}', 'success')">Apply Discount</button>
        </td>
      </tr>
    `).join("");
  },

  renderExpiryView(expiryReport) {
    const totalRisk = document.getElementById("expiry-total-risk-val");
    const tbody = document.getElementById("expiry-table-body");

    if (totalRisk) totalRisk.textContent = `₹${(expiryReport.total_at_risk_value || 0).toLocaleString('en-IN')}`;
    if (!tbody) return;

    if (!expiryReport.items || expiryReport.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 24px; color: var(--text-muted);">No products expiring in the next 60 days.</td></tr>`;
      return;
    }

    tbody.innerHTML = expiryReport.items.map(it => `
      <tr>
        <td>
          <div style="font-weight: 700;">${it.product_name}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">Batch: ${it.batch_number}</div>
        </td>
        <td>${it.expiry_date}</td>
        <td><strong style="color: ${it.days_remaining <= 7 ? 'var(--crimson-danger)' : 'var(--accent-amber)'};">${it.days_remaining} Days Left</strong></td>
        <td>${it.quantity} ${it.unit}s</td>
        <td>₹${it.at_risk_value.toFixed(2)}</td>
        <td>
          <div style="font-size: 0.8125rem; margin-bottom: 6px;">${it.recommendation}</div>
          <button class="btn btn-amber btn-sm" onclick="App.showToast('Priority clearance deal pushed to front shelf', 'info')">Prioritize Sale</button>
        </td>
      </tr>
    `).join("");
  },

  renderSuppliersView(suppliers) {
    const grid = document.getElementById("suppliers-grid-container");
    if (!grid) return;

    if (!suppliers || suppliers.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 32px; color: var(--text-muted);">No suppliers registered yet.</div>`;
      return;
    }

    grid.innerHTML = suppliers.map(s => `
      <div class="card">
        <div class="card-header">
          <h4 class="card-title">${s.name}</h4>
          <span class="badge badge-success">${s.reliability_score}% Reliability</span>
        </div>
        <div class="card-body" style="display: flex; flex-direction: column; gap: 10px; font-size: 0.875rem;">
          <div><strong>Contact:</strong> ${s.contact_person} (${s.phone})</div>
          <div><strong>Delivery Time:</strong> ${s.delivery_time_days} Day(s)</div>
          <div><strong>Payment Terms:</strong> ${s.payment_terms}</div>
          <div><strong>Categories:</strong> ${(s.categories || []).join(', ')}</div>
          <button class="btn btn-outline btn-sm" style="margin-top: 10px;" onclick="App.triggerSupplierCompare('Maggi 2-Minute Noodles', 50)">
            Compare Against Other Mandi Vendors
          </button>
        </div>
      </div>
    `).join("");
  },

  renderOrdersView(orders) {
    const tbody = document.getElementById("orders-table-body");
    if (!tbody) return;

    if (!orders || orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">No purchase orders created yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => `
      <tr>
        <td><strong>${o.po_number}</strong></td>
        <td>${o.supplier_name}</td>
        <td>${(o.items || []).map(i => `${i.product_name} (${i.quantity})`).join(', ')}</td>
        <td><strong>₹${o.total_amount.toLocaleString('en-IN')}</strong></td>
        <td><span class="badge ${o.status === 'RECEIVED' ? 'badge-success' : 'badge-warning'}">${o.status}</span></td>
        <td>
          ${o.status !== 'RECEIVED' ? `
            <button class="btn btn-primary btn-sm" onclick="App.markOrderReceived('${o._id}')">Mark Received</button>
          ` : '<span style="color: var(--emerald-success); font-weight: 700; font-size: 0.8125rem;">✓ Stock Updated</span>'}
        </td>
      </tr>
    `).join("");
  },

  async triggerSupplierCompare(productName, qty) {
    if (!SubscriptionService.checkFeatureAccess(
      CONFIG.FEATURES.SUPPLIER_COMPARISON,
      "Smart Supplier Comparison",
      "Compare prices, delivery lead times, and reliability ratings across Mandi vendors."
    )) return;

    this.showLoading("Comparing wholesale mandi vendors...");
    try {
      const res = await API.post("/api/suppliers/compare", {
        product_name: productName,
        required_quantity: qty
      });

      this.hideLoading();

      const modalBody = document.getElementById("supplier-compare-modal-content");
      if (modalBody) {
        modalBody.innerHTML = `
          <div style="margin-bottom: 16px;">
            <h4>Comparison for ${res.requested_quantity} units of <strong>${res.product_name}</strong></h4>
            <p style="font-size: 0.875rem; color: var(--text-muted);">${res.decision_summary}</p>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${res.options.map(opt => `
              <div style="border: 1.5px solid ${opt.is_recommended ? 'var(--primary)' : 'var(--border-light)'}; border-radius: 12px; padding: 16px; background: ${opt.is_recommended ? '#F0FDF4' : '#FFFFFF'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <strong>${opt.supplier_name}</strong>
                  <span class="badge ${opt.is_recommended ? 'badge-primary' : 'badge-neutral'}">${opt.badge}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 0.875rem; margin-bottom: 8px;">
                  <div>Price/Unit: <strong>₹${opt.price_per_unit}</strong></div>
                  <div>Delivery: <strong>${opt.delivery_time}</strong></div>
                  <div>Reliability: <strong>${opt.reliability_score}%</strong></div>
                </div>
                <p style="font-size: 0.8125rem; color: var(--text-muted);">${opt.rationale}</p>
                <button class="btn btn-primary btn-sm" style="margin-top: 10px;" onclick="App.triggerGeneratePO('${res.product_name}', ${res.requested_quantity}, '${opt.supplier_name}', ${opt.price_per_unit})">
                  Order from ${opt.supplier_name}
                </button>
              </div>
            `).join("")}
          </div>
        `;
        this.openModal("modal-supplier-compare");
      }
    } catch (e) {
      this.hideLoading();
      this.showToast(e.message, "error");
    }
  },

  async triggerGeneratePO(productName, qty, supplierName, unitPrice) {
    if (!SubscriptionService.checkFeatureAccess(
      CONFIG.FEATURES.PURCHASE_ACTIONS,
      "Automated Purchase Orders",
      "Create, confirm, and automatically receive PO inventory into your store records."
    )) return;

    if (!confirm(`Generate purchase order for ${qty} units of ${productName} with ${supplierName} (Total: ₹${(qty * unitPrice).toFixed(2)})?`)) {
      return;
    }

    this.showLoading("Creating purchase order...");
    try {
      const res = await API.post("/api/orders/", {
        supplier_name: supplierName,
        items: [{
          product_name: productName,
          quantity: qty,
          unit_price: unitPrice,
          unit: "packet"
        }],
        delivery_days: 1,
        source: "DECISION_ENGINE"
      });

      this.hideLoading();
      this.closeModal("modal-supplier-compare");
      this.showToast(`✓ Purchase order ${res.po_number} generated!`, "success");
      Router.navigate("orders");
      this.refreshDashboardData();
    } catch (e) {
      this.hideLoading();
      this.showToast(e.message, "error");
    }
  },

  async markOrderReceived(orderId) {
    this.showLoading("Receiving shipment & updating stock...");
    try {
      await API.patch(`/api/orders/${orderId}/status`, { status: "RECEIVED" });
      this.hideLoading();
      this.showToast("✓ Stock ledger updated from PO receipt!", "success");
      this.refreshDashboardData();
    } catch (e) {
      this.hideLoading();
      this.showToast(e.message, "error");
    }
  },

  renderLockedPreviews() {
    // Renders lock banners if Free account
    const decHero = document.getElementById("decision-engine-hero-card");
    if (decHero) this.renderDecisionEngineHero(null);
  },

  renderNotificationsList(notifs) {
    const list = document.getElementById("notifications-dropdown-list");
    const badge = document.getElementById("topbar-notif-badge");

    if (badge) {
      const count = Store.state.unreadNotifsCount;
      badge.textContent = count;
      if (count > 0) badge.classList.remove("hidden");
      else badge.classList.add("hidden");
    }

    if (!list) return;

    if (!notifs || notifs.length === 0) {
      list.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 0.8125rem;">No new notifications.</div>`;
      return;
    }

    list.innerHTML = notifs.map(n => `
      <div style="padding: 12px 16px; border-bottom: 1px solid var(--border-light); background: ${n.is_read ? '#FFFFFF' : '#F0FDF4'};">
        <div style="font-size: 0.875rem; font-weight: 700; color: var(--text-main);">${n.title}</div>
        <p style="font-size: 0.8125rem; color: var(--text-muted); margin-top: 2px;">${n.message}</p>
      </div>
    `).join("");
  },

  toggleNotificationsPanel() {
    const panel = document.getElementById("notifications-dropdown-panel");
    if (panel) panel.classList.toggle("hidden");
  },

  async markAllNotificationsRead() {
    try {
      await API.post("/api/notifications/mark-all-read", {});
      Store.state.unreadNotifsCount = 0;
      Store.notify();
      this.refreshDashboardData();
    } catch (e) {}
  },

  // Modal Manager
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("open");
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("open");
  },

  // Toast System
  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div style="font-weight: 600; font-size: 0.875rem; color: var(--text-main);">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // Loading Overlay
  showLoading(text = "Loading...") {
    const overlay = document.getElementById("global-loading-overlay");
    const label = document.getElementById("global-loading-text");
    if (label) label.textContent = text;
    if (overlay) overlay.classList.remove("hidden");
  },

  hideLoading() {
    const overlay = document.getElementById("global-loading-overlay");
    if (overlay) overlay.classList.add("hidden");
  }
};

window.App = App;

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
