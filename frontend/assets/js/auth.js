/**
 * Authentication & Verification Controller
 */

const Auth = {
  pendingIdentifier: "",
  
  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Signup password strength live meter
    const signupPwd = document.getElementById("signup-password");
    if (signupPwd) {
      signupPwd.addEventListener("input", (e) => {
        this.evaluatePasswordStrength(e.target.value);
      });
    }

    // Signup form submit
    const signupForm = document.getElementById("signup-form");
    if (signupForm) {
      signupForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleSignup();
      });
    }

    // Login form submit
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }

    // OTP Verification submit
    const otpForm = document.getElementById("otp-form");
    if (otpForm) {
      otpForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleVerifyOtp();
      });
    }

    // Forgot Password submit
    const forgotForm = document.getElementById("forgot-password-form");
    if (forgotForm) {
      forgotForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleForgotPassword();
      });
    }

    // Reset Password submit
    const resetForm = document.getElementById("reset-password-form");
    if (resetForm) {
      resetForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleResetPassword();
      });
    }
  },

  evaluatePasswordStrength(password) {
    const meter = document.getElementById("signup-strength-meter");
    const label = document.getElementById("signup-strength-label");
    if (!meter || !label) return;

    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

    meter.className = "strength-meter";
    if (password.length === 0) {
      label.textContent = "";
    } else if (score < 3 || password.length < 8) {
      meter.classList.add("weak");
      label.textContent = "Weak (Minimum 8 chars, uppercase, lowercase, number, symbol)";
      label.style.color = "var(--crimson-danger)";
    } else if (score < 4) {
      meter.classList.add("medium");
      label.textContent = "Medium Strength";
      label.style.color = "var(--accent-amber)";
    } else {
      meter.classList.add("strong");
      label.textContent = "Strong Password ✓";
      label.style.color = "var(--emerald-success)";
    }
  },

  async handleSignup() {
    const fullName = document.getElementById("signup-name").value.trim();
    const shopName = document.getElementById("signup-shop").value.trim();
    const phone = document.getElementById("signup-phone").value.trim();
    const email = document.getElementById("signup-email").value.trim();
    const password = document.getElementById("signup-password").value;
    const confirmPassword = document.getElementById("signup-confirm-password").value;

    if (!fullName || !shopName || !phone || !email || !password) {
      App.showToast("Please fill in all required fields.", "error");
      return;
    }

    if (password !== confirmPassword) {
      App.showToast("Passwords do not match.", "error");
      return;
    }

    App.showLoading("Creating your shop account...");
    try {
      const res = await API.post("/api/auth/signup", {
        full_name: fullName,
        shop_name: shopName,
        phone,
        email,
        password,
        confirm_password: confirmPassword
      });

      App.hideLoading();
      this.pendingIdentifier = email || phone;
      
      // Open OTP Modal with clear feedback
      this.openOtpModal(this.pendingIdentifier, res.dev_otp);
      App.showToast("Account created! Please verify the OTP code.", "success");
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  async handleLogin() {
    const identifier = document.getElementById("login-identifier").value.trim();
    const password = document.getElementById("login-password").value;

    if (!identifier || !password) {
      App.showToast("Please enter your Phone/Email and password.", "error");
      return;
    }

    App.showLoading("Signing into StockSathi...");
    try {
      const res = await API.post("/api/auth/login", {
        identifier,
        password
      });

      App.hideLoading();

      if (res.requires_verification) {
        this.pendingIdentifier = res.identifier;
        this.openOtpModal(res.identifier, res.dev_otp);
        App.showToast("Please verify your account before accessing the dashboard.", "warning");
        return;
      }

      API.setToken(res.token);
      Store.setUser(res.user);
      App.showToast(`Welcome back, ${res.user.full_name}!`, "success");
      Router.navigate("dashboard");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  openOtpModal(identifier, devOtp) {
    this.pendingIdentifier = identifier;
    const targetSpan = document.getElementById("otp-modal-target");
    const devBanner = document.getElementById("otp-dev-code-banner");
    const devCode = document.getElementById("otp-dev-code");
    const otpInput = document.getElementById("otp-input-code");

    if (targetSpan) targetSpan.textContent = identifier;
    if (devBanner && devOtp) {
      devBanner.classList.remove("hidden");
      if (devCode) devCode.textContent = devOtp;
      if (otpInput) otpInput.value = devOtp; // prefill for instant smooth demo experience
    }
    
    App.openModal("modal-otp-verification");
  },

  async handleVerifyOtp() {
    const otp = document.getElementById("otp-input-code").value.trim();
    if (!otp) {
      App.showToast("Please enter the 6-digit OTP code.", "error");
      return;
    }

    App.showLoading("Verifying code...");
    try {
      const res = await API.post("/api/auth/verify-otp", {
        identifier: this.pendingIdentifier,
        otp
      });

      App.hideLoading();
      App.closeModal("modal-otp-verification");
      
      API.setToken(res.token);
      Store.setUser(res.user);
      App.showToast("Account verified successfully! Welcome to StockSathi.", "success");
      Router.navigate("dashboard");
      App.refreshDashboardData();
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  async resendOtp() {
    if (!this.pendingIdentifier) return;
    try {
      const res = await API.post("/api/auth/resend-otp", { identifier: this.pendingIdentifier });
      const devCode = document.getElementById("otp-dev-code");
      const otpInput = document.getElementById("otp-input-code");
      if (devCode && res.dev_otp) devCode.textContent = res.dev_otp;
      if (otpInput && res.dev_otp) otpInput.value = res.dev_otp;
      App.showToast("New OTP code generated.", "info");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async handleForgotPassword() {
    const idInput = document.getElementById("forgot-identifier").value.trim();
    if (!idInput) {
      App.showToast("Please enter your registered email or phone.", "error");
      return;
    }

    App.showLoading("Sending reset code...");
    try {
      const res = await API.post("/api/auth/forgot-password", { identifier: idInput });
      App.hideLoading();
      App.closeModal("modal-forgot-password");
      
      this.pendingIdentifier = idInput;
      
      const resetIdSpan = document.getElementById("reset-target-id");
      const resetDevCode = document.getElementById("reset-dev-code");
      const resetOtpInput = document.getElementById("reset-otp-input");
      
      if (resetIdSpan) resetIdSpan.textContent = idInput;
      if (resetDevCode && res.dev_otp) resetDevCode.textContent = res.dev_otp;
      if (resetOtpInput && res.dev_otp) resetOtpInput.value = res.dev_otp;
      
      App.openModal("modal-reset-password");
      App.showToast("Reset OTP sent.", "info");
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  async handleResetPassword() {
    const otp = document.getElementById("reset-otp-input").value.trim();
    const newPwd = document.getElementById("reset-new-password").value;
    const confirmPwd = document.getElementById("reset-confirm-password").value;

    if (!otp || !newPwd) {
      App.showToast("Please enter the OTP and new password.", "error");
      return;
    }

    if (newPwd !== confirmPwd) {
      App.showToast("Passwords do not match.", "error");
      return;
    }

    App.showLoading("Updating password...");
    try {
      await API.post("/api/auth/reset-password", {
        identifier: this.pendingIdentifier,
        otp,
        new_password: newPwd,
        confirm_password: confirmPwd
      });

      App.hideLoading();
      App.closeModal("modal-reset-password");
      App.showToast("Password updated successfully! You can now log in.", "success");
      Router.navigate("login");
    } catch (err) {
      App.hideLoading();
      App.showToast(err.message, "error");
    }
  },

  logout() {
    API.setToken(null);
    Store.clearUser();
    App.showToast("Logged out successfully.", "info");
    Router.navigate("landing");
  }
};

window.Auth = Auth;
