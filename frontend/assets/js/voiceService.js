/**
 * Voice AI Service
 * Real-time Speech Recognition & Synthesis with Read-Back + Confirmation State Machine
 */

const VoiceService = {
  recognition: null,
  isListening: false,
  selectedLanguage: "Hindi",
  currentPendingAction: null,

  init() {
    this.setupSpeechRecognition();
    this.bindEvents();
  },

  setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = "hi-IN";

      this.recognition.onstart = () => {
        this.isListening = true;
        this.updateListeningUI(true);
      };

      this.recognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        this.updateTranscriptUI(transcript);

        if (event.results[0].isFinal) {
          this.processSpokenText(transcript);
        }
      };

      this.recognition.onerror = (event) => {
        console.warn("[SpeechRecognition Error]", event.error);
        this.isListening = false;
        this.updateListeningUI(false);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.updateListeningUI(false);
      };
    }
  },

  bindEvents() {
    // Quick command chips
    document.querySelectorAll(".voice-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const text = chip.getAttribute("data-command") || chip.textContent.trim();
        this.processSpokenText(text);
      });
    });
  },

  openVoiceModal() {
    if (!SubscriptionService.checkFeatureAccess(
      CONFIG.FEATURES.VOICE_AI,
      "Voice AI Inventory Assistant",
      "Speak to StockSathi in Hindi, Punjabi, Hinglish, or English to update stock hands-free."
    )) {
      return;
    }

    this.currentPendingAction = null;
    this.resetVoiceUI();
    App.openModal("modal-voice-assistant");
  },

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  },

  startListening() {
    if (this.recognition) {
      try {
        const langMap = {
          "Hindi": "hi-IN",
          "Punjabi": "pa-IN",
          "English": "en-IN",
          "Hinglish": "hi-IN"
        };
        this.recognition.lang = langMap[this.selectedLanguage] || "hi-IN";
        this.recognition.start();
      } catch (e) {
        console.warn("Recognition start error:", e);
      }
    } else {
      this.updateTranscriptUI("Speech recognition is supported via web browser or demo chips below.");
    }
  },

  stopListening() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
    this.isListening = false;
    this.updateListeningUI(false);
  },

  async processSpokenText(text) {
    if (!text || !text.trim()) return;
    this.stopListening();
    this.updateTranscriptUI(`"${text}"`);

    // Check if user is confirming with 'Haan' / 'Yes' while action is pending
    const lower = text.toLowerCase();
    const isConfirmation = /^(haan|ha|yes|yep|sure|kar do|kardo|update karo|theek hai|proceed|okay|ok)$/i.test(lower.trim());

    if (this.currentPendingAction && isConfirmation) {
      await this.executeConfirmedVoiceUpdate();
      return;
    }

    App.showLoading("StockSathi is understanding your request...");
    try {
      const res = await API.post("/api/voice/parse", {
        transcript: text,
        language: this.selectedLanguage,
        existing_context: this.currentPendingAction
      });

      App.hideLoading();

      if (res.status === "CONFIRMATION_REQUIRED" && res.pending_action) {
        this.currentPendingAction = res.pending_action;
        this.renderReadbackConfirmation(res);
        this.speakUtterance(res.speech_response);
      } else if (res.status === "READY_TO_EXECUTE") {
        await this.executeConfirmedVoiceUpdate();
      } else {
        this.renderClarificationMessage(res.readback_text || "Kripya dobara bolein.");
        this.speakUtterance(res.speech_response || "Kripya dobara bolein.");
      }
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  renderReadbackConfirmation(res) {
    const card = document.getElementById("voice-readback-card");
    const spokenText = document.getElementById("voice-readback-text");
    const pName = document.getElementById("voice-diff-product");
    const prevStock = document.getElementById("voice-diff-prev");
    const changeVal = document.getElementById("voice-diff-change");
    const newStock = document.getElementById("voice-diff-new");
    const actionBtns = document.getElementById("voice-action-buttons");

    if (spokenText) spokenText.textContent = res.readback_text;
    if (pName) pName.textContent = res.display.product_name;
    if (prevStock) prevStock.textContent = `${res.display.current_stock} ${res.display.unit}`;
    if (changeVal) changeVal.textContent = res.display.change;
    if (newStock) newStock.textContent = `${res.display.new_stock} ${res.display.unit}`;

    if (card) card.classList.remove("hidden");
    if (actionBtns) actionBtns.classList.remove("hidden");
  },

  renderClarificationMessage(message) {
    const spokenText = document.getElementById("voice-readback-text");
    const card = document.getElementById("voice-readback-card");
    const actionBtns = document.getElementById("voice-action-buttons");
    
    if (spokenText) spokenText.textContent = message;
    if (card) card.classList.remove("hidden");
    if (actionBtns) actionBtns.classList.add("hidden");
  },

  async executeConfirmedVoiceUpdate() {
    if (!this.currentPendingAction) return;

    App.showLoading("Updating stock in database...");
    try {
      const res = await API.post("/api/voice/confirm", {
        pending_action: this.currentPendingAction,
        language: this.selectedLanguage
      });

      App.hideLoading();
      this.currentPendingAction = null;

      // Show success in modal
      const card = document.getElementById("voice-readback-card");
      const spokenText = document.getElementById("voice-readback-text");
      const actionBtns = document.getElementById("voice-action-buttons");

      if (spokenText) spokenText.innerHTML = `<strong>✓ Stock Updated</strong><br>${res.details.product_name}: Previous ${res.details.previous_stock} → New <strong>${res.details.new_stock} ${res.details.unit}s</strong>.`;
      if (actionBtns) actionBtns.classList.add("hidden");

      // Spoken voice feedback
      this.speakUtterance(res.speech_response);
      App.showToast(res.message, "success");

      // Refresh live inventory & KPIs
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  speakUtterance(text) {
    if ('speechSynthesis' in window && text) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      
      const voices = window.speechSynthesis.getVoices();
      const hindiVoice = voices.find(v => v.lang.includes("hi") || v.name.includes("India") || v.name.includes("Hindi"));
      if (hindiVoice) {
        utterance.voice = hindiVoice;
      }
      
      window.speechSynthesis.speak(utterance);
    }
  },

  updateListeningUI(isListening) {
    const mic = document.getElementById("voice-mic-trigger");
    const statusText = document.getElementById("voice-mic-status");
    if (mic) {
      if (isListening) mic.classList.add("listening");
      else mic.classList.remove("listening");
    }
    if (statusText) {
      statusText.textContent = isListening ? "Listening... Speak now" : "Click microphone to speak";
    }
  },

  updateTranscriptUI(text) {
    const transcriptEl = document.getElementById("voice-live-transcript");
    if (transcriptEl) transcriptEl.textContent = text || "Listening for command...";
  },

  resetVoiceUI() {
    this.updateListeningUI(false);
    this.updateTranscriptUI("Click microphone or select a voice prompt below...");
    const card = document.getElementById("voice-readback-card");
    const actionBtns = document.getElementById("voice-action-buttons");
    if (card) card.classList.add("hidden");
    if (actionBtns) actionBtns.classList.add("hidden");
  }
};

window.VoiceService = VoiceService;
