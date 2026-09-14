# GameDev Journey 2.0 — Web Application

A full-stack, persistent game-development career portfolio and personal dashboard with email authentication, multi-tenant data isolation, zero-hallucination AI resume parsing, gameplay video streaming, dynamic game jam tracking, certificate verification, and GDD PDF management.

---

## 🎮 Key Features

1. **Email-Based Authentication & Session Management**:
   - Clean sign-up, login, and logout.
   - Salted password hashing via Werkzeug (`scrypt`).
   - **Clean Starting Baseline**: Every new user profile starts 100% empty with no fake or pre-filled data.
   - **Persistent Storage**: All saved user information is stored in SQLite (`instance/gamedev.db`) and remains intact across logout, browser refresh, or closure.

2. **Personal Profile Dashboard & Profile Name Editing**:
   - Dedicated `PROFILE NAME: [ Current Name ] [ EDIT ]` interface with instant persistence and HUD updates.
   - Editable fields: Professional Title, About Me, Career Goal, Skills, Education, and other details.

3. **Resume Upload + Zero-Hallucination AI Extraction**:
   - Upload PDF resumes.
   - Extracts Name, Title, Skills, Education, Experience, Projects, Certifications, and Achievements using `pypdf` and strict entity matching.
   - **Strict Zero-Invention Rule**: AI never synthesizes skills or experience not present in the document.
   - Interactive review modal where users can inspect, edit, or remove extracted items before applying to their profile.

4. **Gameplay Videos Section**:
   - Upload gameplay videos (`.mp4`, `.webm`, `.mov`).
   - Stream videos directly with responsive HTML5 video players.
   - Edit titles/descriptions and delete videos (automatically cleans up disk files).

5. **Game Jams History**:
   - Automatically calculated `Total Game Jams: [Count]` (not hardcoded).
   - Add, edit, and delete game jams (jam name, event/platform, date, game created, role, description, link).

6. **Achievements Vault**:
   - Add unlimited achievements with categories, dates, organizations, and descriptions.
   - Upload proof certificate images with fullscreen lightbox viewer.
   - Edit and delete support with asset cleanup.

7. **Social Links**:
   - Dedicated separate input fields for GitHub, LinkedIn, and itch.io.
   - Displays clean clickable badges in the HUD and live portfolio.

8. **My Next Game Project Idea (GDD PDF)**:
   - Upload, store, view, replace, and delete Game Design Documents (PDF).

9. **Multi-Tenant User Isolation**:
   - Strict database constraints (`user_id = session['user_id']`).
   - Authenticated file router (`/api/uploads/...`) ensures User A cannot access User B's files.

10. **Futuristic Gaming UI & Web Audio Engine**:
    - Cyberpunk dark theme (`#05070b`), neon cyan/purple accents, and responsive layout.
    - Web Audio API procedural sound effects with mute toggle.
    - 1-click toggle between **Dashboard** and **Live Portfolio Preview**.

---

## 🚀 How to Run

### Quick Start (Windows):
Double-click **`run.bat`** or execute:
```powershell
cd d:\mega
python app.py
```
Then open: **`http://127.0.0.1:5000`** in your browser.

### Running Automated Tests:
```powershell
cd d:\mega
python -m unittest tests/test_app.py
```
All 8 automated integration test suites verify empty profile baseline, persistence, dynamic counters, file uploads, and user isolation.
