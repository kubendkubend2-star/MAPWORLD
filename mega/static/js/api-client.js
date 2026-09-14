/**
 * GAMEDEV JOURNEY 2.0 - Unified API Client & Notification System
 */

class ApiClient {
  static showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-message">${message}</div>
      <button class="modal-close-btn" style="position:static; font-size:1rem;">✕</button>
    `;

    toast.querySelector('button').addEventListener('click', () => toast.remove());
    container.appendChild(toast);

    if (type === 'success' && window.cyberAudio) {
      window.cyberAudio.playSuccess();
    } else if (type === 'error' && window.cyberAudio) {
      window.cyberAudio.playError();
    }

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  static async request(url, options = {}) {
    try {
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401 && !url.includes('/api/auth/me')) {
          ApiClient.showToast(data.error || 'Session expired. Please log in.', 'error');
          if (window.appController) {
            window.appController.showAuthView();
          }
        }
        throw new Error(data.error || 'Server error occurred.');
      }

      return data;
    } catch (error) {
      console.error(`API Error [${url}]:`, error);
      throw error;
    }
  }

  // Auth APIs
  static async signup(email, password) {
    return this.request('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
  }

  static async login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
  }

  static async logout() {
    return this.request('/api/auth/logout', { method: 'POST' });
  }

  static async checkAuth() {
    return this.request('/api/auth/me');
  }

  // Profile APIs
  static async getProfile() {
    return this.request('/api/profile');
  }

  static async updateProfile(profileData) {
    return this.request('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData)
    });
  }

  static async updateProfileName(profileName) {
    return this.request('/api/profile/name', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_name: profileName })
    });
  }

  // Resume APIs
  static async uploadResume(formData) {
    return this.request('/api/resume/upload', {
      method: 'POST',
      body: formData
    });
  }

  static async applyResume(data) {
    return this.request('/api/resume/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  // Videos APIs
  static async getVideos() {
    return this.request('/api/videos');
  }

  static async uploadVideo(formData) {
    return this.request('/api/videos', {
      method: 'POST',
      body: formData
    });
  }

  static async editVideo(videoId, data) {
    return this.request(`/api/videos/${videoId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  static async deleteVideo(videoId) {
    return this.request(`/api/videos/${videoId}`, {
      method: 'DELETE'
    });
  }

  // Game Jams APIs
  static async getGameJams() {
    return this.request('/api/game-jams');
  }

  static async addGameJam(data) {
    return this.request('/api/game-jams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  static async updateGameJam(jamId, data) {
    return this.request(`/api/game-jams/${jamId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }

  static async deleteGameJam(jamId) {
    return this.request(`/api/game-jams/${jamId}`, {
      method: 'DELETE'
    });
  }

  // Achievements APIs
  static async getAchievements() {
    return this.request('/api/achievements');
  }

  static async addAchievement(formData) {
    return this.request('/api/achievements', {
      method: 'POST',
      body: formData
    });
  }

  static async editAchievement(achId, formData) {
    return this.request(`/api/achievements/${achId}`, {
      method: 'PUT',
      body: formData
    });
  }

  static async deleteAchievement(achId) {
    return this.request(`/api/achievements/${achId}`, {
      method: 'DELETE'
    });
  }

  // GDD APIs
  static async getGDD() {
    return this.request('/api/gdd');
  }

  static async uploadGDD(formData) {
    return this.request('/api/gdd', {
      method: 'POST',
      body: formData
    });
  }

  static async deleteGDD() {
    return this.request('/api/gdd', {
      method: 'DELETE'
    });
  }

  // Stats API
  static async getStats() {
    return this.request('/api/dashboard/stats');
  }

  // Username Slug API
  static async updateUsername(newUsername) {
    return this.request('/api/auth/username', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: newUsername })
    });
  }

  // Visibility Toggle API
  static async toggleVisibility(category, itemId, isPublic) {
    return this.request(`/api/visibility/${category}/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_public: isPublic })
    });
  }

  // Public Profile API
  static async getPublicProfile(username) {
    return this.request(`/api/public/profile/${username}`);
  }
}

window.ApiClient = ApiClient;
