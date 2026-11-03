/**
 * Global Reactive Client State Store
 */

const Store = {
  state: {
    user: null,
    isAuthenticated: false,
    isVerified: false,
    kpis: {
      total_products: 0,
      total_stock_value: 0,
      total_retail_value: 0,
      low_stock_count: 0,
      expiring_soon_count: 0,
      dead_stock_value: 0
    },
    products: [],
    suppliers: [],
    orders: [],
    predictions: [],
    topActionItem: null,
    deadMoney: { total_dead_money: 0, items: [] },
    expiryReport: { total_at_risk_value: 0, items: [] },
    dailyActions: [],
    notifications: [],
    unreadNotifsCount: 0,
    isDemoMode: false,
    listeners: []
  },

  setUser(userData) {
    this.state.user = userData;
    this.state.isAuthenticated = !!userData;
    this.state.isVerified = userData ? !!userData.is_verified : false;
    this.state.isDemoMode = userData ? !!userData.is_demo_account : false;
    this.notify();
  },

  clearUser() {
    this.state.user = null;
    this.state.isAuthenticated = false;
    this.state.isVerified = false;
    this.state.isDemoMode = false;
    this.notify();
  },

  isPremium() {
    if (!this.state.user || !this.state.user.subscription) return false;
    return this.state.user.subscription.is_premium;
  },

  isTrialActive() {
    if (!this.state.user || !this.state.user.subscription) return false;
    return this.state.user.subscription.is_trial_active;
  },

  getTrialRemainingDays() {
    if (!this.state.user || !this.state.user.subscription) return 0;
    return this.state.user.subscription.remaining_trial_days || 0;
  },

  canAccess(featureKey) {
    if (featureKey === CONFIG.FEATURES.BASIC_INVENTORY) return true;
    if (!this.state.user || !this.state.user.subscription) return false;
    const unlocked = this.state.user.subscription.unlocked_features || [];
    return unlocked.includes(featureKey);
  },

  subscribe(listener) {
    this.state.listeners.push(listener);
  },

  notify() {
    for (const listener of this.state.listeners) {
      try {
        listener(this.state);
      } catch (err) {
        console.error("[Store Listener Error]:", err);
      }
    }
  }
};

window.Store = Store;
