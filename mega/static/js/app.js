/**
 * GAMEDEV JOURNEY 2.0 - Core Application Bootstrap
 * Handles authentication routing, state initialization, and view orchestration.
 */

class AppController {
  constructor() {
    this.currentUser = null;
    this.currentMode = 'dashboard'; // 'dashboard' | 'portfolio'
    this.dashboard = null;

    this.bindGlobalEvents();
  }

  async init() {
    // Check audio mute state
    const muteBtn = document.getElementById('btn-toggle-sfx');
    if (muteBtn && window.cyberAudio) {
      if (window.cyberAudio.muted) {
        muteBtn.classList.remove('active');
        muteBtn.innerHTML = '<span>🔇</span> SFX: OFF';
      } else {
        muteBtn.classList.add('active');
        muteBtn.innerHTML = '<span>🔊</span> SFX: ON';
      }
    }

    try {
      const res = await ApiClient.checkAuth();
      if (res.authenticated) {
        this.currentUser = res.user;
        this.showDashboardView();
      } else {
        this.showAuthView();
      }
    } catch (err) {
      this.showAuthView();
    }
  }

  bindGlobalEvents() {
    // Audio Toggle
    const muteBtn = document.getElementById('btn-toggle-sfx');
    if (muteBtn && window.cyberAudio) {
      muteBtn.addEventListener('click', () => {
        const muted = window.cyberAudio.toggleMute();
        if (muted) {
          muteBtn.classList.remove('active');
          muteBtn.innerHTML = '<span>🔇</span> SFX: OFF';
        } else {
          muteBtn.classList.add('active');
          muteBtn.innerHTML = '<span>🔊</span> SFX: ON';
          window.cyberAudio.playClick();
        }
      });
    }

    // Auth Form Toggle (Login vs Sign Up)
    const btnSwitchToSignup = document.getElementById('btn-switch-to-signup');
    const btnSwitchToLogin = document.getElementById('btn-switch-to-login');
    const boxLogin = document.getElementById('box-login');
    const boxSignup = document.getElementById('box-signup');

    if (btnSwitchToSignup && btnSwitchToLogin) {
      btnSwitchToSignup.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.cyberAudio) window.cyberAudio.playClick();
        boxLogin.style.display = 'none';
        boxSignup.style.display = 'block';
      });

      btnSwitchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.cyberAudio) window.cyberAudio.playClick();
        boxSignup.style.display = 'none';
        boxLogin.style.display = 'block';
      });
    }

    // Login Form
    const formLogin = document.getElementById('form-login');
    if (formLogin) {
      formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        try {
          const res = await ApiClient.login(email, password);
          this.currentUser = res.user;
          ApiClient.showToast('Login successful. Welcome back, Developer!');
          this.showDashboardView();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Sign Up Form
    const formSignup = document.getElementById('form-signup');
    if (formSignup) {
      formSignup.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('signup-email').value.trim();
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;

        if (password !== confirmPassword) {
          ApiClient.showToast('Passwords do not match.', 'error');
          return;
        }

        try {
          const res = await ApiClient.signup(email, password);
          this.currentUser = res.user;
          ApiClient.showToast('Account initialized! Your profile is ready for entry.');
          this.showDashboardView();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Logout Buttons
    document.querySelectorAll('.btn-logout-trigger').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to log out of your session?')) return;
        try {
          await ApiClient.logout();
          this.currentUser = null;
          ApiClient.showToast('Logged out successfully.');
          this.showAuthView();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    });

    // Toggle Dashboard vs Live Portfolio
    const toggleViewBtn = document.getElementById('btn-toggle-view');
    if (toggleViewBtn) {
      toggleViewBtn.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playClick();
        if (this.currentMode === 'dashboard') {
          this.showPortfolioView();
        } else {
          this.showDashboardView();
        }
      });
    }
  }

  showAuthView() {
    document.getElementById('auth-view').style.display = 'flex';
    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('portfolio-view').style.display = 'none';
    document.getElementById('main-hud-bar').style.display = 'none';
  }

  async showDashboardView() {
    this.currentMode = 'dashboard';
    document.getElementById('auth-view').style.display = 'none';
    document.getElementById('dashboard-view').style.display = 'flex';
    document.getElementById('portfolio-view').style.display = 'none';
    document.getElementById('main-hud-bar').style.display = 'flex';

    const toggleViewBtn = document.getElementById('btn-toggle-view');
    if (toggleViewBtn) {
      toggleViewBtn.innerHTML = '<span>👁️</span> LIVE PORTFOLIO';
    }

    if (!this.dashboard) {
      this.dashboard = new DashboardController();
      window.dashboardController = this.dashboard;
    }
    await this.dashboard.init();
  }

  showPortfolioView() {
    this.currentMode = 'portfolio';
    document.getElementById('auth-view').style.display = 'none';
    document.getElementById('dashboard-view').style.display = 'none';
    document.getElementById('portfolio-view').style.display = 'block';
    document.getElementById('main-hud-bar').style.display = 'flex';

    const toggleViewBtn = document.getElementById('btn-toggle-view');
    if (toggleViewBtn) {
      toggleViewBtn.innerHTML = '<span>⚙️</span> DASHBOARD';
    }

    if (this.dashboard) {
      PortfolioViewController.render(
        this.dashboard.profileData,
        this.dashboard.gameJams,
        this.dashboard.achievements,
        this.dashboard.videos,
        this.dashboard.gddData,
        this.dashboard.stats
      );
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.appController = new AppController();
  window.appController.init();
});
