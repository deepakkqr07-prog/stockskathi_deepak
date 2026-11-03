/**
 * Presentation Demo Mode & Guided 9-Step Walkthrough Controller
 */

const DemoService = {
  currentStepIndex: 0,

  DEMO_STEPS: [
    {
      step: 1,
      title: "Step 1: Smart Dashboard",
      desc: "Open Dashboard. Note KPI cards and the alert: '3 products need your attention today'.",
      action: () => {
        Router.navigate("dashboard");
      }
    },
    {
      step: 2,
      title: "Step 2: AI Demand Prediction",
      desc: "View Maggi demand forecast: Expected Demand: 56, Current Stock: 20, Recommended Order: 45.",
      action: () => {
        Router.navigate("prediction");
      }
    },
    {
      step: 3,
      title: "Step 3: Smart Supplier Comparison",
      desc: "Compare ABC Wholesale (1 day delivery) vs Balaji FMCG (3 days lead time).",
      action: () => {
        Router.navigate("suppliers");
        setTimeout(() => App.triggerSupplierCompare("Maggi 2-Minute Noodles", 45), 300);
      }
    },
    {
      step: 4,
      title: "Step 4: Voice AI Command",
      desc: "Open Voice AI and say: 'Maggi ke 20 packet aur add kar do'.",
      action: () => {
        VoiceService.openVoiceModal();
        setTimeout(() => VoiceService.processSpokenText("Maggi ke 20 packet aur add kar do"), 400);
      }
    },
    {
      step: 5,
      title: "Step 5: Voice Read-Back & Confirm",
      desc: "Review Read-Back diff (Previous: 20 → Added: +20 → New: 40). Confirm with 'Haan'.",
      action: () => {
        VoiceService.processSpokenText("Haan");
      }
    },
    {
      step: 6,
      title: "Step 6: Voice Success & Verified Update",
      desc: "Listen to spoken success feedback: 'Ho gaya ji! Maggi ka stock update kar diya gaya hai'.",
      action: () => {
        App.closeModal("modal-voice-assistant");
        Router.navigate("inventory");
      }
    },
    {
      step: 7,
      title: "Step 7: Dead Money Detector",
      desc: "Inspect locked working capital (e.g. ₹2,700 stuck in Classmate Notebooks for 48 days).",
      action: () => {
        Router.navigate("dead-stock");
      }
    },
    {
      step: 8,
      title: "Step 8: Expiry Loss Prevention",
      desc: "View batches nearing shelf-life (Amul Milk expiring in 2 days, Dairy Milk in 14 days).",
      action: () => {
        Router.navigate("expiry");
      }
    },
    {
      step: 9,
      title: "Step 9: AI Shopkeeper Assistant",
      desc: "Open chat and ask: 'Aaj mujhe shop mein kya karna chahiye?'",
      action: () => {
        SupportService.toggleDrawer();
        setTimeout(() => SupportService.sendMessage("Aaj mujhe shop mein kya karna chahiye?"), 400);
      }
    }
  ],

  async startDemoMode() {
    App.showLoading("Seeding presentation demo environment...");
    try {
      const res = await API.post("/api/demo/seed", {});
      App.hideLoading();

      API.setToken(res.token);
      Store.setUser(res.user);

      this.currentStepIndex = 0;
      this.renderDemoRunnerUI(true);

      App.showToast("🚀 Demo Mode active! Gupta Ji Kirana Store loaded.", "success");
      Router.navigate("dashboard");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  async resetDemo() {
    App.showLoading("Resetting demo data to original pristine state...");
    try {
      const res = await API.post("/api/demo/reset", {});
      App.hideLoading();

      API.setToken(res.token);
      Store.setUser(res.user);

      this.currentStepIndex = 0;
      this.updateStepDisplay();

      App.showToast("✓ Demo dataset reset successfully.", "info");
      Router.navigate("dashboard");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  nextStep() {
    if (this.currentStepIndex < this.DEMO_STEPS.length - 1) {
      this.currentStepIndex++;
      this.runCurrentStep();
    }
  },

  prevStep() {
    if (this.currentStepIndex > 0) {
      this.currentStepIndex--;
      this.runCurrentStep();
    }
  },

  runCurrentStep() {
    const cur = this.DEMO_STEPS[this.currentStepIndex];
    if (cur && cur.action) {
      this.updateStepDisplay();
      cur.action();
    }
  },

  updateStepDisplay() {
    const cur = this.DEMO_STEPS[this.currentStepIndex];
    const badge = document.getElementById("demo-guide-step-badge");
    const title = document.getElementById("demo-guide-title");
    const desc = document.getElementById("demo-guide-desc");

    if (badge) badge.textContent = `Step ${cur.step} of 9`;
    if (title) title.textContent = cur.title;
    if (desc) desc.textContent = cur.desc;
  },

  renderDemoRunnerUI(show) {
    const topBanner = document.getElementById("demo-top-banner");
    const runnerPill = document.getElementById("demo-guide-pill");

    if (topBanner) {
      if (show) topBanner.classList.remove("hidden");
      else topBanner.classList.add("hidden");
    }

    if (runnerPill) {
      if (show) {
        runnerPill.classList.remove("hidden");
        this.updateStepDisplay();
      } else {
        runnerPill.classList.add("hidden");
      }
    }
  }
};

window.DemoService = DemoService;
