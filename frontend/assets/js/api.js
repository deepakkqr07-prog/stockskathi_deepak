/**
 * Centralized API Client with JWT Bearer Interceptors & Error Handlers
 */

const API = {
  getToken() {
    return localStorage.getItem("stocksathi_token");
  },

  setToken(token) {
    if (token) {
      localStorage.setItem("stocksathi_token", token);
    } else {
      localStorage.removeItem("stocksathi_token");
    }
  },

  async request(endpoint, options = {}) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401) {
        // Session expired or unauthenticated
        this.setToken(null);
        if (window.Store) {
          window.Store.clearUser();
        }
        if (window.Router && window.Router.currentView !== "landing" && window.Router.currentView !== "login") {
          window.Router.navigate("login");
          if (window.App) window.App.showToast("Your session has expired. Please log in again.", "warning");
        }
        throw new Error("Authentication required.");
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorDetail = data.detail || (typeof data === "string" ? data : "An error occurred with your request.");
        throw new Error(errorDetail);
      }

      return data;
    } catch (error) {
      console.error(`[API Error] ${endpoint}:`, error.message);
      throw error;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  },

  patch(endpoint, body) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
};

window.API = API;
