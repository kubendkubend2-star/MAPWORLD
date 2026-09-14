/**
 * GAMEDEV JOURNEY 2.0 - Live Cyber Portfolio Renderer
 * Populates the interactive cinematic portfolio with authentic user data.
 */

class PortfolioViewController {
  static render(profile, gameJams, achievements, videos, gdd, stats) {
    const container = document.getElementById('portfolio-view-content');
    if (!container) return;

    const p = profile || {};
    const jams = gameJams || [];
    const achs = achievements || [];
    const vids = videos || [];
    const skills = p.skills || [];

    let html = `
      <div class="portfolio-wrapper">
        <!-- Hero Dossier Banner -->
        <div class="portfolio-hero">
          <div class="portfolio-hero-content">
            <div class="portfolio-avatar-frame">
              <img src="/static/assets/default_avatar.svg" alt="Dev Avatar" class="portfolio-avatar-img">
            </div>
            <div class="portfolio-dev-meta">
              <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--neon-cyan); letter-spacing: 2px;">
                DEVELOPER PROFILE // LVL ${stats.level || 1}
              </div>
              <h1 class="portfolio-dev-name">${escapeHtml(p.profile_name || 'ANONYMOUS DEVELOPER')}</h1>
              <div class="portfolio-dev-title">${escapeHtml(p.professional_title || 'GAME DEVELOPER')}</div>
              ${p.career_goal ? `<div class="portfolio-dev-goal"><strong>MISSION OBJECTIVE:</strong> ${escapeHtml(p.career_goal)}</div>` : ''}

              <!-- Social Links -->
              <div class="portfolio-social-bar">
                ${p.github_url ? `<a href="${escapeHtml(p.github_url)}" target="_blank" rel="noopener" class="portfolio-social-link">💻 GITHUB</a>` : ''}
                ${p.linkedin_url ? `<a href="${escapeHtml(p.linkedin_url)}" target="_blank" rel="noopener" class="portfolio-social-link">💼 LINKEDIN</a>` : ''}
                ${p.itchio_url ? `<a href="${escapeHtml(p.itchio_url)}" target="_blank" rel="noopener" class="portfolio-social-link">🕹️ ITCH.IO</a>` : ''}
                ${(!p.github_url && !p.linkedin_url && !p.itchio_url) ? '<span style="font-size:0.8rem; color:var(--text-muted);">No social links configured.</span>' : ''}
              </div>
            </div>
          </div>
        </div>

        <!-- Character Dossier / About Me -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>01</span> ABOUT &amp; BACKGROUND
          </div>
          <div class="portfolio-about-card">
            ${p.about_me ? `<div>${escapeHtml(p.about_me).replace(/\n/g, '<br>')}</div>` : '<div class="cyber-empty-slot">ABOUT ME SECTION NOT YET INITIALIZED</div>'}
            ${p.education ? `
              <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border-subtle);">
                <strong style="color: var(--neon-cyan); font-family: var(--font-mono); font-size: 0.85rem;">EDUCATION CREDENTIALS:</strong>
                <div style="margin-top: 6px; color: var(--text-secondary);">${escapeHtml(p.education).replace(/\n/g, '<br>')}</div>
              </div>
            ` : ''}
          </div>
        </section>

        <!-- Technical Skills Tree -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>02</span> CORE ARSENAL // SKILLS
          </div>
          <div class="cyber-card">
            ${skills.length > 0 ? `
              <div class="skills-wrapper">
                ${skills.map(s => `<div class="skill-pill"><span>${escapeHtml(s)}</span></div>`).join('')}
              </div>
            ` : '<div class="cyber-empty-slot">NO SKILLS RECORDED</div>'}
          </div>
        </section>

        <!-- Gameplay Video Showcase -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>03</span> GAMEPLAY &amp; PROTOTYPE HIGHLIGHTS
          </div>
          ${vids.length > 0 ? `
            <div class="videos-grid">
              ${vids.map(v => `
                <div class="video-card">
                  <div class="video-player-container">
                    <video controls preload="metadata">
                      <source src="${v.stream_url}" type="video/mp4">
                    </video>
                  </div>
                  <div class="video-info">
                    <div class="video-title">${escapeHtml(v.title)}</div>
                    <div class="video-desc">${escapeHtml(v.description || '')}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<div class="cyber-empty-slot">NO GAMEPLAY VIDEOS UPLOADED</div>'}
        </section>

        <!-- Game Jam Records -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>04</span> GAME JAM EXPEDITIONS (${jams.length} TOTAL JAMS)
          </div>
          ${jams.length > 0 ? `
            <div class="jams-list">
              ${jams.map(jam => `
                <div class="jam-card">
                  <div style="flex: 1;">
                    <div class="jam-name">${escapeHtml(jam.jam_name)}</div>
                    <div class="jam-meta">
                      ${jam.event_platform ? `<div class="jam-meta-item">EVENT: <span>${escapeHtml(jam.event_platform)}</span></div>` : ''}
                      ${jam.date ? `<div class="jam-meta-item">DATE: <span>${escapeHtml(jam.date)}</span></div>` : ''}
                      ${jam.game_created ? `<div class="jam-meta-item">GAME: <span>${escapeHtml(jam.game_created)}</span></div>` : ''}
                      ${jam.role ? `<div class="jam-meta-item">ROLE: <span>${escapeHtml(jam.role)}</span></div>` : ''}
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 8px;">
                      ${escapeHtml(jam.description || '')}
                    </div>
                    ${jam.jam_link ? `<a href="${escapeHtml(jam.jam_link)}" target="_blank" rel="noopener" class="portfolio-social-link" style="padding: 3px 10px; font-size: 0.75rem;">🌐 PLAY / INSPECT JAM ENTRY</a>` : ''}
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<div class="cyber-empty-slot">NO GAME JAMS LOGGED</div>'}
        </section>

        <!-- Achievements & Trophy Vault -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>05</span> TROPHY VAULT // HONORS &amp; ACHIEVEMENTS
          </div>
          ${achs.length > 0 ? `
            <div class="achievements-grid">
              ${achs.map(a => `
                <div class="achievement-card">
                  <div class="achievement-badge">🏆</div>
                  <div style="font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: #fff;">${escapeHtml(a.title)}</div>
                  <div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--neon-cyan); margin: 4px 0 8px;">
                    ${escapeHtml(a.category || 'Milestone')} ${a.organization ? `• ${escapeHtml(a.organization)}` : ''} ${a.date ? `• ${escapeHtml(a.date)}` : ''}
                  </div>
                  <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px; flex: 1;">
                    ${escapeHtml(a.description || '')}
                  </div>
                  ${a.certificate_url ? `
                    <div style="margin-top: 10px;">
                      <img src="${a.certificate_url}" class="cert-thumbnail" onclick="window.dashboardController.viewCertificate('${a.certificate_url}', '${escapeJs(a.title)}')" alt="Certificate">
                    </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          ` : '<div class="cyber-empty-slot">NO ACHIEVEMENTS LOGGED</div>'}
        </section>

        <!-- Next Game Project Idea / GDD -->
        <section class="portfolio-section">
          <div class="portfolio-section-title">
            <span>06</span> NEXT GAME PROJECT DESIGN DOCUMENT (GDD)
          </div>
          ${gdd ? `
            <div class="gdd-active-card">
              <div class="gdd-file-info">
                <div class="gdd-file-icon">📋</div>
                <div>
                  <div style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; color: #fff;">${escapeHtml(gdd.title)}</div>
                  <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
                    FILENAME: ${escapeHtml(gdd.filename)} • SIZE: ${(gdd.file_size / (1024 * 1024)).toFixed(2)} MB
                  </div>
                </div>
              </div>
              <div>
                <a href="${gdd.view_url}" target="_blank" class="btn-cyber btn-cyber-primary">READ GAME DESIGN DOCUMENT (PDF)</a>
              </div>
            </div>
          ` : '<div class="cyber-empty-slot">NO GAME DESIGN DOCUMENT CURRENTLY UPLOADED</div>'}
        </section>
      </div>
    `;

    container.innerHTML = html;
  }
}

window.PortfolioViewController = PortfolioViewController;
