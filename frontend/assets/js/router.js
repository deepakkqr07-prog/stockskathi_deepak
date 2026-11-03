/**
 * Client-Side View Router & Protection Guards
 */

const Router = {
  currentView: "landing",
  
  PROTECTED_VIEWS: [
    "dashboard", "inventory", "products", "suppliers", "orders",
    "prediction", "dead-stock", "expiry", "daily-assistant",
    "settings", "notifications"
  ],

  init() {
    window.addEventListener("hashchange", () => {
      this.handleHashChange();
    });
    this.handleHashChange();
  },

  handleHashChange() {
    const hash = window.location.hash.replace("#", "").trim();
    const target = hash || (API.getToken() ? "dashboard" : "landing");
    this.navigate(target, false);
  },

  navigate(viewName, updateHash = true) {
    const cleanView = viewName || "landing";

    // Authentication Guard
    const token = API.getToken();
    const isProtected = this.PROTECTED_VIEWS.includes(cleanView);

    if (isProtected && !token) {
      this.renderView("login");
      if (updateHash) window.location.hash = "login";
      return;
    }

    // If authenticated and tries to open login/signup, go to dashboard
    if ((cleanView === "login" || cleanView === "signup") && token && Store.state.user) {
      this.renderView("dashboard");
      if (updateHash) window.location.hash = "dashboard";
      return;
    }

    this.renderView(cleanView);
    if (updateHash) {
      window.location.hash = cleanView;
    }
  },

  renderView(viewName) {
    this.currentView = viewName;

    // Toggle Landing vs App Layout
    const landingContainer = document.getElementById("landing-view-container");
    const authContainer = document.getElementById("auth-view-container");
    const appLayout = document.getElementById("app-layout-container");

    if (viewName === "landing") {
      if (landingContainer) landingContainer.classList.remove("hidden");
      if (authContainer) authContainer.classList.add("hidden");
      if (appLayout) appLayout.classList.add("hidden");
      window.scrollTo(0, 0);
      return;
    }

    if (viewName === "login" || viewName === "signup") {
      if (landingContainer) landingContainer.classList.add("hidden");
      if (authContainer) authContainer.classList.remove("hidden");
      if (appLayout) appLayout.classList.add("hidden");

      const loginCard = document.getElementById("auth-login-card");
      const signupCard = document.getElementById("auth-signup-card");

      if (viewName === "login") {
        if (loginCard) loginCard.classList.remove("hidden");
        if (signupCard) signupCard.classList.add("hidden");
      } else {
        if (loginCard) loginCard.classList.add("hidden");
        if (signupCard) signupCard.classList.remove("hidden");
      }
      window.scrollTo(0, 0);
      return;
    }

    // Workspace Views (Dashboard, Inventory, etc.)
    if (landingContainer) landingContainer.classList.add("hidden");
    if (authContainer) authContainer.classList.add("hidden");
    if (appLayout) appLayout.classList.remove("hidden");

    // Hide all internal workspace views
    document.querySelectorAll(".workspace-view").forEach((el) => {
      el.classList.add("hidden");
    });

    // Show active workspace view
    const targetEl = document.getElementById(`view-${viewName}`);
    if (targetEl) {
      targetEl.classList.remove("hidden");
    } else {
      const defaultEl = document.getElementById("view-dashboard");
      if (defaultEl) defaultEl.classList.remove("hidden");
    }

    // Update active state in sidebar
    document.querySelectorAll(".sidebar-item").forEach((item) => {
      if (item.getAttribute("data-view") === viewName) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    window.scrollTo(0, 0);
  }
};

window.Router = Router;
