/**
 * Subscription, Trial Countdown & Feature Gating Service
 */

const SubscriptionService = {
  selectedPlan: "PREMIUM",

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const checkoutForm = document.getElementById("checkout-form");
    if (checkoutForm) {
      checkoutForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.processCheckout();
      });
    }
  },

  checkFeatureAccess(featureKey, featureName, featureDescription) {
    if (Store.canAccess(featureKey)) {
      return true;
    }

    this.showUpgradeModal(featureName, featureDescription);
    return false;
  },

  showUpgradeModal(featureName, featureDescription) {
    const nameEl = document.getElementById("upgrade-feature-title");
    const descEl = document.getElementById("upgrade-feature-desc");
    const trialBtn = document.getElementById("upgrade-start-trial-btn");

    if (nameEl) nameEl.textContent = featureName || "Premium Feature";
    if (descEl) descEl.textContent = featureDescription || "This feature is available with StockSathi Premium.";

    // If user already used trial, hide trial button and show view plans
    const user = Store.state.user;
    if (user && user.subscription && user.subscription.trial_started_at) {
      if (trialBtn) trialBtn.classList.add("hidden");
    } else {
      if (trialBtn) trialBtn.classList.remove("hidden");
    }

    App.openModal("modal-upgrade-prompt");
  },

  async startFreeTrial() {
    App.showLoading("Activating your 3-Day Premium Trial...");
    try {
      const res = await API.post("/api/subscription/start-trial", {});
      App.hideLoading();
      App.closeModal("modal-upgrade-prompt");

      // Update state
      if (Store.state.user) {
        Store.state.user.subscription = res;
        Store.notify();
      }

      App.showToast("🎉 3-Day Premium Trial Activated! All AI features are now unlocked.", "success");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  openCheckoutModal(planName = "PREMIUM") {
    this.selectedPlan = planName;
    const planInfo = CONFIG.PLANS[planName] || CONFIG.PLANS["PREMIUM"];

    const titleEl = document.getElementById("checkout-plan-name");
    const priceEl = document.getElementById("checkout-plan-price");
    const gstEl = document.getElementById("checkout-gst-amount");
    const totalEl = document.getElementById("checkout-total-amount");

    const basePrice = planInfo.price;
    const gst = Math.round(basePrice * 0.18);
    const total = basePrice + gst;

    if (titleEl) titleEl.textContent = `StockSathi ${planInfo.name}`;
    if (priceEl) priceEl.textContent = `₹${basePrice}`;
    if (gstEl) gstEl.textContent = `₹${gst}`;
    if (totalEl) totalEl.textContent = `₹${total}`;

    App.openModal("modal-subscription-checkout");
  },

  async processCheckout() {
    const paymentMethod = document.querySelector('input[name="pay_method"]:checked')?.value || "UPI";
    App.showLoading("Securing payment & generating invoice...");

    try {
      const res = await API.post("/api/subscription/checkout", {
        plan_name: this.selectedPlan,
        payment_method: paymentMethod,
        billing_cycle: "monthly"
      });

      App.hideLoading();
      App.closeModal("modal-subscription-checkout");

      if (Store.state.user) {
        Store.state.user.subscription = res.user_status;
        Store.notify();
      }

      App.showToast(`✨ Successfully subscribed to StockSathi ${this.selectedPlan}! Invoice: ${res.subscription.invoice_id}`, "success");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  }
};

window.SubscriptionService = SubscriptionService;
