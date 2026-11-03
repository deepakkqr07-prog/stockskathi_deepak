/**
 * AI Support Assistant Service
 * Grounded Shopkeeper Chat Assistant with Safety Safeguards
 */

const SupportService = {
  isOpen: false,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const chatForm = document.getElementById("support-chat-form");
    if (chatForm) {
      chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("support-chat-input");
        if (input && input.value.trim()) {
          this.sendMessage(input.value.trim());
          input.value = "";
        }
      });
    }

    // Quick prompt pills
    document.querySelectorAll(".quick-pill-btn").forEach((pill) => {
      pill.addEventListener("click", () => {
        const text = pill.getAttribute("data-query") || pill.textContent.trim();
        this.sendMessage(text);
      });
    });
  },

  toggleDrawer() {
    if (!SubscriptionService.checkFeatureAccess(
      CONFIG.FEATURES.AI_SUPPORT,
      "StockSathi Shop Assistant",
      "Ask any question about your inventory, daily sales, stuck capital, and suppliers."
    )) {
      return;
    }

    const drawer = document.getElementById("support-drawer");
    if (drawer) {
      this.isOpen = !this.isOpen;
      if (this.isOpen) drawer.classList.add("open");
      else drawer.classList.remove("open");
    }
  },

  closeDrawer() {
    const drawer = document.getElementById("support-drawer");
    if (drawer) {
      this.isOpen = false;
      drawer.classList.remove("open");
    }
  },

  async sendMessage(query) {
    if (!query) return;

    this.appendMessage(query, "user");
    this.appendTypingIndicator();

    try {
      const res = await API.post("/api/support/chat", {
        message: query,
        language: Store.state.user?.language || "Hindi"
      });

      this.removeTypingIndicator();
      this.appendMessage(res.reply, "assistant", res.grounded_sources, res.pending_action);
    } catch (err) {
      this.removeTypingIndicator();
      this.appendMessage("Sorry, I could not process your query at this moment. Please try again.", "assistant");
      App.showToast(err.message, "error");
    }
  },

  appendMessage(text, sender, sources = [], pendingAction = null) {
    const container = document.getElementById("support-messages-list");
    if (!container) return;

    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;

    let html = text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    if (sources && sources.length > 0) {
      html += `<div style="margin-top: 8px;"><span class="grounded-tag">📊 Grounded: ${sources.join(", ")}</span></div>`;
    }

    if (pendingAction) {
      html += `
        <div style="margin-top: 12px; padding: 10px; background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px;">
          <div style="font-size: 0.8125rem; font-weight: 700; color: #065F46; margin-bottom: 6px;">Action Confirmation Required:</div>
          <div style="font-size: 0.75rem; margin-bottom: 8px;">Update ${pendingAction.product_name} from ${pendingAction.current_stock} to <strong>${pendingAction.new_stock} ${pendingAction.unit}s</strong>?</div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary btn-sm" onclick="VoiceService.currentPendingAction=${JSON.stringify(pendingAction).replace(/"/g, '&quot;')}; VoiceService.executeConfirmedVoiceUpdate();">Confirm Update</button>
            <button class="btn btn-secondary btn-sm" onclick="this.parentElement.parentElement.remove();">Cancel</button>
          </div>
        </div>
      `;
    }

    bubble.innerHTML = html;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  appendTypingIndicator() {
    const container = document.getElementById("support-messages-list");
    if (!container) return;

    const typing = document.createElement("div");
    typing.id = "support-typing-indicator";
    typing.className = "chat-bubble assistant";
    typing.innerHTML = `<span style="color: var(--text-muted); font-size: 0.8125rem;">StockSathi is checking shop records...</span>`;
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
  },

  removeTypingIndicator() {
    const typing = document.getElementById("support-typing-indicator");
    if (typing) typing.remove();
  }
};

window.SupportService = SupportService;
