/**
 * StockSathi Frontend Configuration
 */

const CONFIG = {
  API_BASE_URL: window.location.origin,
  APP_NAME: "StockSathi",
  TAGLINE: "Smart Retail Decision Engine",
  DEFAULT_LANGUAGE: "Hindi",
  TRIAL_DAYS: 3,
  
  FEATURES: {
    BASIC_INVENTORY: "BASIC_INVENTORY",
    DEMAND_PREDICTION: "DEMAND_PREDICTION",
    VOICE_AI: "VOICE_AI",
    SUPPLIER_COMPARISON: "SUPPLIER_COMPARISON",
    DEAD_MONEY: "DEAD_MONEY",
    EXPIRY_PREVENTION: "EXPIRY_PREVENTION",
    DAILY_ASSISTANT: "DAILY_ASSISTANT",
    AI_SUPPORT: "AI_SUPPORT",
    PURCHASE_ACTIONS: "PURCHASE_ACTIONS",
    ADVANCED_ANALYTICS: "ADVANCED_ANALYTICS"
  },
  
  PLANS: {
    FREE: { name: "Free Tier", price: 0 },
    BASIC: { name: "Basic", price: 199 },
    STANDARD: { name: "Standard", price: 499 },
    PREMIUM: { name: "Premium", price: 999 }
  }
};

window.CONFIG = CONFIG;
