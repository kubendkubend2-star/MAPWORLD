/**
 * GAMEDEV JOURNEY 2.0 - Dashboard Controller
 * Manages all 10 tabs, interactive forms, modals, uploads, and dynamic counters.
 */

class DashboardController {
  constructor() {
    this.currentTab = 'profile';
    this.profileData = {};
    this.gameJams = [];
    this.achievements = [];
    this.videos = [];
    this.gddData = null;
    this.stats = {};
    this.username = '';

    this.bindEvents();
  }

  async init() {
    await this.refreshAllData();
    this.switchTab('profile');
  }

  async refreshAllData() {
    try {
      const [profileRes, jamsRes, achRes, vidRes, gddRes, statsRes] = await Promise.all([
        ApiClient.getProfile(),
        ApiClient.getGameJams(),
        ApiClient.getAchievements(),
        ApiClient.getVideos(),
        ApiClient.getGDD(),
        ApiClient.getStats()
      ]);

      this.profileData = profileRes.profile || {};
      this.gameJams = jamsRes.game_jams || [];
      this.achievements = achRes.achievements || [];
      this.videos = vidRes.videos || [];
      this.gddData = gddRes.gdd || null;
      this.stats = statsRes || {};
      this.username = this.profileData.username || (window.appController && window.appController.currentUser ? window.appController.currentUser.username : '');

      this.renderAll();
      this.updateHUDStats();
      this.updatePublicLinkDisplays();
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    }
  }

  updatePublicLinkDisplays() {
    const fullUrl = `${window.location.origin}/profile/${this.username}`;
    const pubPreview = document.getElementById('pub-profile-link-preview');
    if (pubPreview) pubPreview.textContent = fullUrl;

    const viewBtn = document.getElementById('btn-view-public-link');
    if (viewBtn) viewBtn.href = `/profile/${this.username}`;

    const shareDisplay = document.getElementById('share-profile-url-display');
    if (shareDisplay) shareDisplay.value = fullUrl;

    const shareTabBtn = document.getElementById('btn-open-share-tab');
    if (shareTabBtn) shareTabBtn.href = `/profile/${this.username}`;

    const inputAccountUser = document.getElementById('input-account-username');
    if (inputAccountUser) inputAccountUser.value = this.username;

    const inputModalUser = document.getElementById('input-modal-username');
    if (inputModalUser) inputModalUser.value = this.username;
  }

  updateHUDStats() {
    if (!this.stats) return;
    document.querySelectorAll('.hud-level-value').forEach(el => el.textContent = `LVL ${this.stats.level || 1}`);
    document.querySelectorAll('.hud-xp-current').forEach(el => el.textContent = (this.stats.xp || 0).toLocaleString());
    document.querySelectorAll('.hud-xp-next').forEach(el => el.textContent = (this.stats.next_level_xp || 1000).toLocaleString());

    const pct = Math.min(100, Math.round(((this.stats.current_level_xp || 0) / (this.stats.next_level_xp || 1000)) * 100));
    document.querySelectorAll('.hud-xp-fill').forEach(el => el.style.width = `${pct}%`);

    // Tab badges
    const jamBadge = document.getElementById('badge-jams');
    if (jamBadge) jamBadge.textContent = this.gameJams.length;

    const achBadge = document.getElementById('badge-achievements');
    if (achBadge) achBadge.textContent = this.achievements.length;

    const vidBadge = document.getElementById('badge-videos');
    if (vidBadge) vidBadge.textContent = this.videos.length;
  }

  bindEvents() {
    // Tab switching
    document.querySelectorAll('.nav-tab-btn[data-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playClick();
        this.switchTab(btn.dataset.tab);
      });
    });

    // Share My Profile Trigger
    const btnShare = document.getElementById('btn-share-profile');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playModal();
        this.updatePublicLinkDisplays();
        this.openModal('modal-share-profile');
      });
    }

    // Copy Public Profile Link
    const copyButtons = [
      document.getElementById('btn-copy-share-url'),
      document.getElementById('btn-copy-public-link')
    ];
    copyButtons.forEach(btn => {
      if (btn) {
        btn.addEventListener('click', async () => {
          const fullUrl = `${window.location.origin}/profile/${this.username}`;
          try {
            await navigator.clipboard.writeText(fullUrl);
            ApiClient.showToast('Public profile link copied to clipboard!');
          } catch (e) {
            ApiClient.showToast(fullUrl, 'info');
          }
        });
      }
    });

    // Username Handle Update Handler
    const handleUsernameUpdate = async (newUsername) => {
      try {
        const res = await ApiClient.updateUsername(newUsername);
        this.username = res.username;
        if (window.appController && window.appController.currentUser) {
          window.appController.currentUser.username = res.username;
        }
        this.updatePublicLinkDisplays();
        ApiClient.showToast('Username handle updated successfully.');
        this.closeModal('modal-share-profile');
      } catch (err) {
        ApiClient.showToast(err.message, 'error');
      }
    };

    const formAccUser = document.getElementById('form-account-update-username');
    if (formAccUser) {
      formAccUser.addEventListener('submit', async (e) => {
        e.preventDefault();
        const val = document.getElementById('input-account-username').value.trim();
        await handleUsernameUpdate(val);
      });
    }

    const formModalUser = document.getElementById('form-modal-update-username');
    if (formModalUser) {
      formModalUser.addEventListener('submit', async (e) => {
        e.preventDefault();
        const val = document.getElementById('input-modal-username').value.trim();
        await handleUsernameUpdate(val);
      });
    }

    // Profile Name Edit Modal triggers
    const editNameBtn = document.getElementById('btn-edit-profile-name');
    if (editNameBtn) {
      editNameBtn.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playModal();
        const input = document.getElementById('input-modal-profile-name');
        if (input) input.value = this.profileData.profile_name || '';
        this.openModal('modal-edit-profile-name');
      });
    }

    const formEditName = document.getElementById('form-edit-profile-name');
    if (formEditName) {
      formEditName.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nameVal = document.getElementById('input-modal-profile-name').value.trim();
        try {
          await ApiClient.updateProfileName(nameVal);
          this.profileData.profile_name = nameVal;
          ApiClient.showToast('Profile name updated successfully.');
          this.closeModal('modal-edit-profile-name');
          this.renderProfile();
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Profile General Details Form
    const formProfile = document.getElementById('form-profile-details');
    if (formProfile) {
      formProfile.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
          profile_name: this.profileData.profile_name || '',
          professional_title: document.getElementById('input-prof-title').value.trim(),
          about_me: document.getElementById('input-about-me').value.trim(),
          career_goal: document.getElementById('input-career-goal').value.trim(),
          education: document.getElementById('input-education').value.trim(),
          other_details: document.getElementById('input-other-details').value.trim(),
          skills: this.profileData.skills || [],
          github_url: this.profileData.github_url || '',
          linkedin_url: this.profileData.linkedin_url || '',
          itchio_url: this.profileData.itchio_url || ''
        };

        try {
          const res = await ApiClient.updateProfile(payload);
          this.profileData = { ...this.profileData, ...res.profile };
          ApiClient.showToast('Profile updated successfully.');
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Social Links Form
    const formSocials = document.getElementById('form-social-links');
    if (formSocials) {
      formSocials.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
          ...this.profileData,
          github_url: document.getElementById('input-social-github').value.trim(),
          linkedin_url: document.getElementById('input-social-linkedin').value.trim(),
          itchio_url: document.getElementById('input-social-itchio').value.trim()
        };

        try {
          const res = await ApiClient.updateProfile(payload);
          this.profileData = { ...this.profileData, ...res.profile };
          ApiClient.showToast('Profile updated successfully.');
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Skills Add Form
    const formAddSkill = document.getElementById('form-add-skill');
    if (formAddSkill) {
      formAddSkill.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('input-new-skill');
        const skill = input.value.trim();
        if (!skill) return;

        const skills = [...(this.profileData.skills || [])];
        if (!skills.map(s => s.toLowerCase()).includes(skill.toLowerCase())) {
          skills.push(skill);
          try {
            await ApiClient.updateProfile({ ...this.profileData, skills });
            this.profileData.skills = skills;
            input.value = '';
            ApiClient.showToast('Profile updated successfully.');
            this.renderSkills();
            const statsRes = await ApiClient.getStats();
            this.stats = statsRes;
            this.updateHUDStats();
          } catch (err) {
            ApiClient.showToast(err.message, 'error');
          }
        } else {
          ApiClient.showToast('Skill already in your profile.', 'error');
        }
      });
    }

    // Resume Upload Dropzone & File Input
    const resumeFileInput = document.getElementById('input-resume-file');
    const resumeDropzone = document.getElementById('dropzone-resume');
    if (resumeDropzone && resumeFileInput) {
      resumeDropzone.addEventListener('click', () => resumeFileInput.click());

      resumeDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        resumeDropzone.style.borderColor = 'var(--neon-cyan)';
      });

      resumeDropzone.addEventListener('dragleave', () => {
        resumeDropzone.style.borderColor = '';
      });

      resumeDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        resumeDropzone.style.borderColor = '';
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleResumeUpload(e.dataTransfer.files[0]);
        }
      });

      resumeFileInput.addEventListener('change', () => {
        if (resumeFileInput.files && resumeFileInput.files.length > 0) {
          this.handleResumeUpload(resumeFileInput.files[0]);
        }
      });
    }

    // Apply Resume Extracted Data Form
    const formApplyResume = document.getElementById('form-apply-resume');
    if (formApplyResume) {
      formApplyResume.addEventListener('submit', async (e) => {
        e.preventDefault();
        const skillsText = document.getElementById('extracted-skills').value;
        const skillsArray = skillsText.split(',').map(s => s.trim()).filter(Boolean);

        const payload = {
          profile_name: document.getElementById('extracted-name').value.trim(),
          professional_title: document.getElementById('extracted-title').value.trim(),
          about_me: document.getElementById('extracted-about').value.trim(),
          education: document.getElementById('extracted-education').value.trim(),
          skills: skillsArray,
          github_url: document.getElementById('extracted-github').value.trim(),
          linkedin_url: document.getElementById('extracted-linkedin').value.trim(),
          itchio_url: document.getElementById('extracted-itchio').value.trim()
        };

        try {
          await ApiClient.applyResume(payload);
          ApiClient.showToast('Profile updated successfully.');
          this.closeModal('modal-review-resume');
          await this.refreshAllData();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Game Jam Add Button & Form
    const btnAddJam = document.getElementById('btn-add-jam');
    if (btnAddJam) {
      btnAddJam.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playModal();
        document.getElementById('form-jam').reset();
        document.getElementById('jam-modal-title').textContent = 'ADD GAME JAM';
        document.getElementById('input-jam-id').value = '';
        this.openModal('modal-jam');
      });
    }

    const formJam = document.getElementById('form-jam');
    if (formJam) {
      formJam.addEventListener('submit', async (e) => {
        e.preventDefault();
        const jamId = document.getElementById('input-jam-id').value;
        const payload = {
          jam_name: document.getElementById('input-jam-name').value.trim(),
          event_platform: document.getElementById('input-jam-event').value.trim(),
          date: document.getElementById('input-jam-date').value.trim(),
          game_created: document.getElementById('input-jam-game').value.trim(),
          role: document.getElementById('input-jam-role').value.trim(),
          description: document.getElementById('input-jam-desc').value.trim(),
          jam_link: document.getElementById('input-jam-link').value.trim()
        };

        try {
          if (jamId) {
            await ApiClient.updateGameJam(jamId, payload);
            ApiClient.showToast('Game Jam updated successfully.');
          } else {
            await ApiClient.addGameJam(payload);
            ApiClient.showToast('Game Jam added successfully.');
          }
          this.closeModal('modal-jam');
          const jamsRes = await ApiClient.getGameJams();
          this.gameJams = jamsRes.game_jams || [];
          this.renderGameJams();
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Achievements Add Button & Form
    const btnAddAch = document.getElementById('btn-add-achievement');
    if (btnAddAch) {
      btnAddAch.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playModal();
        document.getElementById('form-achievement').reset();
        document.getElementById('ach-modal-title').textContent = 'ADD ACHIEVEMENT';
        document.getElementById('input-ach-id').value = '';
        this.openModal('modal-achievement');
      });
    }

    const formAch = document.getElementById('form-achievement');
    if (formAch) {
      formAch.addEventListener('submit', async (e) => {
        e.preventDefault();
        const achId = document.getElementById('input-ach-id').value;
        const formData = new FormData(formAch);

        try {
          if (achId) {
            await ApiClient.editAchievement(achId, formData);
            ApiClient.showToast('Achievement updated successfully.');
          } else {
            await ApiClient.addAchievement(formData);
            ApiClient.showToast('Achievement saved successfully.');
          }
          this.closeModal('modal-achievement');
          const achRes = await ApiClient.getAchievements();
          this.achievements = achRes.achievements || [];
          this.renderAchievements();
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // Gameplay Video Upload Button & Form
    const btnUploadVideo = document.getElementById('btn-upload-video');
    if (btnUploadVideo) {
      btnUploadVideo.addEventListener('click', () => {
        if (window.cyberAudio) window.cyberAudio.playModal();
        document.getElementById('form-video').reset();
        this.openModal('modal-video-upload');
      });
    }

    const formVideo = document.getElementById('form-video');
    if (formVideo) {
      formVideo.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(formVideo);
        const submitBtn = formVideo.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'UPLOADING VIDEO...';

        try {
          await ApiClient.uploadVideo(formData);
          ApiClient.showToast('Gameplay video uploaded successfully.');
          this.closeModal('modal-video-upload');
          const vidRes = await ApiClient.getVideos();
          this.videos = vidRes.videos || [];
          this.renderVideos();
          const statsRes = await ApiClient.getStats();
          this.stats = statsRes;
          this.updateHUDStats();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = 'UPLOAD VIDEO';
        }
      });
    }

    // Video Edit Form
    const formEditVideo = document.getElementById('form-video-edit');
    if (formEditVideo) {
      formEditVideo.addEventListener('submit', async (e) => {
        e.preventDefault();
        const videoId = document.getElementById('input-edit-video-id').value;
        const title = document.getElementById('input-edit-video-title').value.trim();
        const description = document.getElementById('input-edit-video-desc').value.trim();

        try {
          await ApiClient.editVideo(videoId, { title, description });
          ApiClient.showToast('Video details updated successfully.');
          this.closeModal('modal-video-edit');
          const vidRes = await ApiClient.getVideos();
          this.videos = vidRes.videos || [];
          this.renderVideos();
        } catch (err) {
          ApiClient.showToast(err.message, 'error');
        }
      });
    }

    // GDD Upload Dropzone & Button
    const gddFileInput = document.getElementById('input-gdd-file');
    const gddDropzone = document.getElementById('dropzone-gdd');
    if (gddDropzone && gddFileInput) {
      gddDropzone.addEventListener('click', () => gddFileInput.click());

      gddDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        gddDropzone.style.borderColor = 'var(--neon-green)';
      });

      gddDropzone.addEventListener('dragleave', () => {
        gddDropzone.style.borderColor = '';
      });

      gddDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        gddDropzone.style.borderColor = '';
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleGddUpload(e.dataTransfer.files[0]);
        }
      });

      gddFileInput.addEventListener('change', () => {
        if (gddFileInput.files && gddFileInput.files.length > 0) {
          this.handleGddUpload(gddFileInput.files[0]);
        }
      });
    }

    // Modal Close Buttons
    document.querySelectorAll('.modal-close-btn, .btn-modal-cancel').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const modal = e.target.closest('.modal-overlay');
        if (modal) modal.classList.remove('open');
      });
    });

    // Close modal on click outside
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          overlay.classList.remove('open');
        }
      });
    });
  }

  async handleResumeUpload(file) {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      ApiClient.showToast('Please select a valid PDF resume file.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('resume', file);

    const statusEl = document.getElementById('resume-upload-status');
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.textContent = 'ANALYZING RESUME WITH ZERO-HALLUCINATION AI ENGINE...';
    }

    try {
      const res = await ApiClient.uploadResume(formData);
      ApiClient.showToast('Resume uploaded successfully.');
      if (statusEl) statusEl.style.display = 'none';

      // Open review modal
      this.populateResumeReviewModal(res.extracted);
      this.openModal('modal-review-resume');
    } catch (err) {
      if (statusEl) statusEl.style.display = 'none';
      ApiClient.showToast(err.message, 'error');
    }
  }

  populateResumeReviewModal(data) {
    if (!data) return;
    document.getElementById('extracted-name').value = data.profile_name || '';
    document.getElementById('extracted-title').value = data.professional_title || '';
    document.getElementById('extracted-about').value = data.about_me || '';
    document.getElementById('extracted-education').value = data.education || '';
    document.getElementById('extracted-skills').value = (data.skills || []).join(', ');
    document.getElementById('extracted-experience').value = data.experience || '';
    document.getElementById('extracted-achievements').value = data.achievements || '';
    document.getElementById('extracted-github').value = data.github_url || '';
    document.getElementById('extracted-linkedin').value = data.linkedin_url || '';
    document.getElementById('extracted-itchio').value = data.itchio_url || '';
  }

  async handleGddUpload(file) {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      ApiClient.showToast('Only PDF format is supported for Game Design Documents.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('gdd', file);
    formData.append('title', file.name.replace('.pdf', ''));

    try {
      const res = await ApiClient.uploadGDD(formData);
      this.gddData = res.gdd;
      ApiClient.showToast('Game Design Document saved successfully.');
      this.renderGDD();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('open');
      if (window.cyberAudio) window.cyberAudio.playModal();
    }
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('open');
  }

  switchTab(tabId) {
    this.currentTab = tabId;

    // Update active nav button
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    // Update active pane
    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `pane-${tabId}`);
    });

    // Render active tab data
    if (tabId === 'profile') this.renderProfile();
    else if (tabId === 'skills') this.renderSkills();
    else if (tabId === 'videos') this.renderVideos();
    else if (tabId === 'jams') this.renderGameJams();
    else if (tabId === 'achievements') this.renderAchievements();
    else if (tabId === 'socials') this.renderSocials();
    else if (tabId === 'gdd') this.renderGDD();
    else if (tabId === 'account') this.renderAccount();
  }

  renderAll() {
    this.renderProfile();
    this.renderSkills();
    this.renderVideos();
    this.renderGameJams();
    this.renderAchievements();
    this.renderSocials();
    this.renderGDD();
    this.renderAccount();
  }

  renderProfile() {
    const p = this.profileData;
    const nameDisplay = document.getElementById('profile-name-val-display');
    if (nameDisplay) {
      nameDisplay.textContent = p.profile_name || '[ NO PROFILE NAME SET ]';
      if (!p.profile_name) {
        nameDisplay.style.color = 'var(--text-muted)';
      } else {
        nameDisplay.style.color = '#fff';
      }
    }

    // Top HUD name display
    document.querySelectorAll('.player-name-hud').forEach(el => {
      el.textContent = p.profile_name || 'ANONYMOUS DEV';
    });

    // Form inputs
    const inputTitle = document.getElementById('input-prof-title');
    if (inputTitle) inputTitle.value = p.professional_title || '';

    const inputAbout = document.getElementById('input-about-me');
    if (inputAbout) inputAbout.value = p.about_me || '';

    const inputGoal = document.getElementById('input-career-goal');
    if (inputGoal) inputGoal.value = p.career_goal || '';

    const inputEdu = document.getElementById('input-education');
    if (inputEdu) inputEdu.value = p.education || '';

    const inputOther = document.getElementById('input-other-details');
    if (inputOther) inputOther.value = p.other_details || '';
  }

  renderSkills() {
    const wrapper = document.getElementById('skills-list-container');
    if (!wrapper) return;

    const skills = this.profileData.skills || [];
    if (skills.length === 0) {
      wrapper.innerHTML = `
        <div class="empty-state-box" style="padding: 24px; width: 100%;">
          <div class="empty-state-title">NO SKILLS RECORDED</div>
          <div class="empty-state-sub">Add your game engines, programming languages, or 3D DCC tools above.</div>
        </div>
      `;
      return;
    }

    wrapper.innerHTML = skills.map(skill => `
      <div class="skill-pill">
        <span>${escapeHtml(skill)}</span>
        <button class="skill-remove-btn" onclick="window.dashboardController.removeSkill('${escapeHtml(skill)}')">✕</button>
      </div>
    `).join('');
  }

  async removeSkill(skillToRemove) {
    const skills = (this.profileData.skills || []).filter(s => s !== skillToRemove);
    try {
      await ApiClient.updateProfile({ ...this.profileData, skills });
      this.profileData.skills = skills;
      ApiClient.showToast('Profile updated successfully.');
      this.renderSkills();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  renderVideos() {
    const container = document.getElementById('videos-grid-container');
    if (!container) return;

    if (this.videos.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">🎬</div>
          <div class="empty-state-title">NO GAMEPLAY VIDEOS UPLOADED</div>
          <div class="empty-state-sub">Upload trailers, mechanics prototypes, or gameplay walkthroughs to showcase your game dev work.</div>
          <button class="btn-cyber btn-cyber-primary" onclick="window.dashboardController.openModal('modal-video-upload')">+ UPLOAD GAMEPLAY VIDEO</button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.videos.map(v => `
      <div class="video-card">
        <div class="video-player-container">
          <video controls preload="metadata">
            <source src="${v.stream_url}" type="video/mp4">
            Your browser does not support the video tag.
          </video>
        </div>
        <div class="video-info">
          <div class="video-title">${escapeHtml(v.title)}</div>
          <div class="video-desc">${escapeHtml(v.description || 'No description provided.')}</div>
          <div class="video-actions">
            <button class="btn-cyber btn-cyber-sm ${v.is_public ? 'btn-cyber-primary' : ''}" 
                    title="Click to toggle Public / Private" 
                    onclick="window.dashboardController.toggleVideoVisibility(${v.id}, ${v.is_public ? 1 : 0})">
              ${v.is_public ? '👁️ PUBLIC' : '🔒 PRIVATE'}
            </button>
            <button class="btn-cyber btn-cyber-sm" onclick="window.dashboardController.openEditVideoModal(${v.id}, '${escapeJs(v.title)}', '${escapeJs(v.description || '')}')">EDIT</button>
            <button class="btn-cyber btn-cyber-sm btn-cyber-danger" onclick="window.dashboardController.deleteVideo(${v.id})">DELETE</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  async toggleVideoVisibility(id, currentStatus) {
    const newStatus = currentStatus === 1 ? false : true;
    try {
      await ApiClient.toggleVisibility('videos', id, newStatus);
      const v = this.videos.find(item => item.id === id);
      if (v) v.is_public = newStatus ? 1 : 0;
      ApiClient.showToast(`Gameplay video set to ${newStatus ? 'Public' : 'Private'}.`);
      this.renderVideos();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  openEditVideoModal(id, title, desc) {
    document.getElementById('input-edit-video-id').value = id;
    document.getElementById('input-edit-video-title').value = title;
    document.getElementById('input-edit-video-desc').value = desc;
    this.openModal('modal-video-edit');
  }

  async deleteVideo(id) {
    if (!confirm('Are you sure you want to delete this gameplay video?')) return;
    try {
      await ApiClient.deleteVideo(id);
      ApiClient.showToast('Gameplay video deleted successfully.');
      const vidRes = await ApiClient.getVideos();
      this.videos = vidRes.videos || [];
      this.renderVideos();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  renderGameJams() {
    const counterEl = document.getElementById('total-jams-counter');
    if (counterEl) {
      counterEl.textContent = this.gameJams.length;
    }

    const listEl = document.getElementById('jams-list-container');
    if (!listEl) return;

    if (this.gameJams.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state-box">
          <div class="empty-state-icon">🕹️</div>
          <div class="empty-state-title">NO GAME JAM RECORDS FOUND</div>
          <div class="empty-state-sub">Document your rapid game development journey by logging game jams you participated in.</div>
          <button class="btn-cyber btn-cyber-purple" onclick="document.getElementById('btn-add-jam').click()">+ ADD GAME JAM</button>
        </div>
      `;
      return;
    }

    listEl.innerHTML = this.gameJams.map(jam => `
      <div class="jam-card">
        <div style="flex: 1;">
          <div class="jam-name">${escapeHtml(jam.jam_name)}</div>
          <div class="jam-meta">
            ${jam.event_platform ? `<div class="jam-meta-item">PLATFORM: <span>${escapeHtml(jam.event_platform)}</span></div>` : ''}
            ${jam.date ? `<div class="jam-meta-item">DATE: <span>${escapeHtml(jam.date)}</span></div>` : ''}
            ${jam.game_created ? `<div class="jam-meta-item">PROJECT: <span>${escapeHtml(jam.game_created)}</span></div>` : ''}
            ${jam.role ? `<div class="jam-meta-item">ROLE: <span>${escapeHtml(jam.role)}</span></div>` : ''}
          </div>
          <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 8px;">
            ${escapeHtml(jam.description || 'No description provided.')}
          </div>
          ${jam.jam_link ? `<a href="${escapeHtml(jam.jam_link)}" target="_blank" rel="noopener" class="portfolio-social-link" style="padding: 3px 10px; font-size: 0.75rem;">🌐 VISIT SUBMISSION</a>` : ''}
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn-cyber btn-cyber-sm" onclick="window.dashboardController.openEditJamModal(${jam.id})">EDIT</button>
          <button class="btn-cyber btn-cyber-sm btn-cyber-danger" onclick="window.dashboardController.deleteJam(${jam.id})">DELETE</button>
        </div>
      </div>
    `).join('');
  }

  openEditJamModal(jamId) {
    const jam = this.gameJams.find(j => j.id === jamId);
    if (!jam) return;

    document.getElementById('jam-modal-title').textContent = 'EDIT GAME JAM';
    document.getElementById('input-jam-id').value = jam.id;
    document.getElementById('input-jam-name').value = jam.jam_name || '';
    document.getElementById('input-jam-event').value = jam.event_platform || '';
    document.getElementById('input-jam-date').value = jam.date || '';
    document.getElementById('input-jam-game').value = jam.game_created || '';
    document.getElementById('input-jam-role').value = jam.role || '';
    document.getElementById('input-jam-desc').value = jam.description || '';
    document.getElementById('input-jam-link').value = jam.jam_link || '';

    this.openModal('modal-jam');
  }

  async deleteJam(jamId) {
    if (!confirm('Are you sure you want to remove this Game Jam entry?')) return;
    try {
      await ApiClient.deleteGameJam(jamId);
      ApiClient.showToast('Game Jam deleted successfully.');
      const jamsRes = await ApiClient.getGameJams();
      this.gameJams = jamsRes.game_jams || [];
      this.renderGameJams();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  renderAchievements() {
    const container = document.getElementById('achievements-grid-container');
    if (!container) return;

    if (this.achievements.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">🏆</div>
          <div class="empty-state-title">NO ACHIEVEMENTS RECORDED</div>
          <div class="empty-state-sub">Add honors, awards, hackathon wins, and upload your certificate images.</div>
          <button class="btn-cyber btn-cyber-primary" onclick="document.getElementById('btn-add-achievement').click()">+ ADD ACHIEVEMENT</button>
        </div>
      `;
      return;
    }

    container.innerHTML = this.achievements.map(a => `
      <div class="achievement-card">
        <div class="achievement-badge">🏆</div>
        <div style="font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: #fff;">${escapeHtml(a.title)}</div>
        <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--neon-cyan); margin: 4px 0 8px;">
          ${escapeHtml(a.category || 'Milestone')} ${a.organization ? `• ${escapeHtml(a.organization)}` : ''} ${a.date ? `• ${escapeHtml(a.date)}` : ''}
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px; flex: 1;">
          ${escapeHtml(a.description || 'No description.')}
        </div>
        ${a.certificate_url ? `
          <div style="margin-bottom: 12px;">
            <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted); margin-bottom: 4px;">CERTIFICATE IMAGE:</div>
            <img src="${a.certificate_url}" class="cert-thumbnail" onclick="window.dashboardController.viewCertificate('${a.certificate_url}', '${escapeJs(a.title)}')" alt="Certificate">
          </div>
        ` : ''}
        <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid var(--border-subtle); padding-top: 10px;">
          <button class="btn-cyber btn-cyber-sm ${a.is_public ? 'btn-cyber-primary' : ''}" 
                  title="Click to toggle Public / Private" 
                  onclick="window.dashboardController.toggleAchievementVisibility(${a.id}, ${a.is_public ? 1 : 0})">
            ${a.is_public ? '👁️ PUBLIC' : '🔒 PRIVATE'}
          </button>
          <button class="btn-cyber btn-cyber-sm" onclick="window.dashboardController.openEditAchModal(${a.id})">EDIT</button>
          <button class="btn-cyber btn-cyber-sm btn-cyber-danger" onclick="window.dashboardController.deleteAch(${a.id})">DELETE</button>
        </div>
      </div>
    `).join('');
  }

  async toggleAchievementVisibility(id, currentStatus) {
    const newStatus = currentStatus === 1 ? false : true;
    try {
      await ApiClient.toggleVisibility('achievements', id, newStatus);
      const a = this.achievements.find(item => item.id === id);
      if (a) a.is_public = newStatus ? 1 : 0;
      ApiClient.showToast(`Achievement set to ${newStatus ? 'Public' : 'Private'}.`);
      this.renderAchievements();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  viewCertificate(imgUrl, title) {
    const modal = document.getElementById('modal-lightbox');
    if (!modal) return;
    document.getElementById('lightbox-title').textContent = title || 'CERTIFICATE';
    document.getElementById('lightbox-img').src = imgUrl;
    this.openModal('modal-lightbox');
  }

  openEditAchModal(achId) {
    const ach = this.achievements.find(a => a.id === achId);
    if (!ach) return;

    document.getElementById('ach-modal-title').textContent = 'EDIT ACHIEVEMENT';
    document.getElementById('input-ach-id').value = ach.id;
    document.getElementById('input-ach-title').value = ach.title || '';
    document.getElementById('input-ach-desc').value = ach.description || '';
    document.getElementById('input-ach-date').value = ach.date || '';
    document.getElementById('input-ach-org').value = ach.organization || '';
    document.getElementById('input-ach-cat').value = ach.category || 'Milestone';

    this.openModal('modal-achievement');
  }

  async deleteAch(achId) {
    if (!confirm('Are you sure you want to remove this achievement?')) return;
    try {
      await ApiClient.deleteAchievement(achId);
      ApiClient.showToast('Achievement deleted successfully.');
      const achRes = await ApiClient.getAchievements();
      this.achievements = achRes.achievements || [];
      this.renderAchievements();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  renderSocials() {
    const p = this.profileData;
    const gh = document.getElementById('input-social-github');
    if (gh) gh.value = p.github_url || '';

    const li = document.getElementById('input-social-linkedin');
    if (li) li.value = p.linkedin_url || '';

    const it = document.getElementById('input-social-itchio');
    if (it) it.value = p.itchio_url || '';
  }

  renderGDD() {
    const container = document.getElementById('gdd-container');
    if (!container) return;

    if (!this.gddData) {
      container.innerHTML = `
        <div class="dropzone-box" id="dropzone-gdd">
          <div class="dropzone-icon">📄</div>
          <div class="empty-state-title">UPLOAD GAME DESIGN DOCUMENT (GDD PDF)</div>
          <div class="empty-state-sub">Drag & drop your GDD PDF file here, or click to browse.</div>
          <button class="btn-cyber btn-cyber-primary" type="button">SELECT GDD PDF</button>
        </div>
      `;
      // Re-bind click
      const drop = document.getElementById('dropzone-gdd');
      const input = document.getElementById('input-gdd-file');
      if (drop && input) drop.addEventListener('click', () => input.click());
    } else {
      const mb = (this.gddData.file_size / (1024 * 1024)).toFixed(2);
      container.innerHTML = `
        <div class="gdd-active-card">
          <div class="gdd-file-info">
            <div class="gdd-file-icon">📋</div>
            <div>
              <div style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; color: #fff;">${escapeHtml(this.gddData.title)}</div>
              <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
                FILENAME: ${escapeHtml(this.gddData.filename)} • SIZE: ${mb} MB
              </div>
            </div>
          </div>
          <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
            <button class="btn-cyber btn-cyber-sm ${this.gddData.is_public ? 'btn-cyber-primary' : ''}" 
                    title="Click to toggle Public / Private" 
                    onclick="window.dashboardController.toggleGddVisibility(${this.gddData.id}, ${this.gddData.is_public ? 1 : 0})">
              ${this.gddData.is_public ? '👁️ PUBLIC GDD' : '🔒 PRIVATE GDD'}
            </button>
            <a href="${this.gddData.view_url}" target="_blank" class="btn-cyber btn-cyber-primary">VIEW / DOWNLOAD PDF</a>
            <button class="btn-cyber" onclick="document.getElementById('input-gdd-file').click()">REPLACE GDD</button>
            <button class="btn-cyber btn-cyber-danger" onclick="window.dashboardController.deleteGDD()">DELETE GDD</button>
          </div>
        </div>
      `;
    }
  }

  async toggleGddVisibility(id, currentStatus) {
    const newStatus = currentStatus === 1 ? false : true;
    try {
      await ApiClient.toggleVisibility('gdd', id, newStatus);
      if (this.gddData) this.gddData.is_public = newStatus ? 1 : 0;
      ApiClient.showToast(`Game Design Document set to ${newStatus ? 'Public' : 'Private'}.`);
      this.renderGDD();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  async deleteGDD() {
    if (!confirm('Are you sure you want to delete this Game Design Document?')) return;
    try {
      await ApiClient.deleteGDD();
      this.gddData = null;
      ApiClient.showToast('Game Design Document deleted successfully.');
      this.renderGDD();
      const statsRes = await ApiClient.getStats();
      this.stats = statsRes;
      this.updateHUDStats();
    } catch (err) {
      ApiClient.showToast(err.message, 'error');
    }
  }

  renderAccount() {
    const emailEl = document.getElementById('account-email-val');
    if (emailEl && window.appController && window.appController.currentUser) {
      emailEl.textContent = window.appController.currentUser.email || '';
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeJs(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

window.DashboardController = DashboardController;
