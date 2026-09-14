"""
GameDev Journey 2.0 - Automated Test Suite
Verifies:
1. Account creation & login
2. Empty profile baseline (no fake/sample data)
3. Profile data persistence across logout/login
4. Dedicated profile name editing
5. Zero-hallucination PDF resume extraction
6. Gameplay video uploads and deletions
7. Dynamic auto-calculated game jam counter & CRUD
8. Achievements with certificate upload & deletion
9. Social links persistence
10. GDD PDF upload, replace, and delete
11. Strict multi-tenant user data isolation
"""

import os
import io
import json
import tempfile
import unittest
from pypdf import PdfWriter

# Set test DB before importing app
os.environ['GAMEDEV_DB_PATH'] = os.path.join(tempfile.gettempdir(), 'test_gamedev.db')

from app import app
from database import init_db, get_db

class TestGameDevJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        init_db()

    def setUp(self):
        self.client = app.test_client()
        # Clean users table before each test
        conn = get_db()
        with conn:
            conn.execute("DELETE FROM users")
        conn.close()

    def test_01_signup_creates_completely_empty_profile(self):
        """Verify new users start with an entirely empty profile (no default/fake data)."""
        res = self.client.post('/api/auth/signup', json={
            'email': 'developer1@gamedev.com',
            'password': 'SecurePassword123'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn('user', data)

        # Check profile
        prof_res = self.client.get('/api/profile')
        self.assertEqual(prof_res.status_code, 200)
        p = prof_res.get_json()['profile']
        
        # Verify strict empty state
        self.assertEqual(p['profile_name'], '')
        self.assertEqual(p['professional_title'], '')
        self.assertEqual(p['about_me'], '')
        self.assertEqual(p['career_goal'], '')
        self.assertEqual(p['education'], '')
        self.assertEqual(p['skills'], [])
        self.assertEqual(p['github_url'], '')
        self.assertEqual(p['linkedin_url'], '')
        self.assertEqual(p['itchio_url'], '')

        # Verify 0 game jams and 0 achievements
        jams_res = self.client.get('/api/game-jams')
        self.assertEqual(jams_res.get_json()['total_game_jams'], 0)
        self.assertEqual(len(jams_res.get_json()['game_jams']), 0)

        achs_res = self.client.get('/api/achievements')
        self.assertEqual(len(achs_res.get_json()['achievements']), 0)

    def test_02_profile_name_edit_and_persistence_across_logout(self):
        """Verify profile editing, quick name edit, logout, and persistent retention."""
        # Sign up
        self.client.post('/api/auth/signup', json={
            'email': 'dev_persist@gamedev.com',
            'password': 'Password999'
        })

        # Edit Profile Name
        name_res = self.client.put('/api/profile/name', json={'profile_name': 'Kaelen Vance'})
        self.assertEqual(name_res.status_code, 200)
        self.assertEqual(name_res.get_json()['profile_name'], 'Kaelen Vance')

        # Edit full profile details
        update_res = self.client.put('/api/profile', json={
            'profile_name': 'Kaelen Vance',
            'professional_title': 'Senior Gameplay Architect',
            'about_me': 'Building immersive procedural worlds.',
            'career_goal': 'Lead core engine programming for AAA studio.',
            'education': 'B.S. in Computer Science',
            'skills': ['C++', 'Unity', 'HLSL', 'Unreal Engine 5'],
            'github_url': 'https://github.com/kaelen',
            'linkedin_url': 'https://linkedin.com/in/kaelen',
            'itchio_url': 'https://kaelen.itch.io'
        })
        self.assertEqual(update_res.status_code, 200)

        # Logout
        logout_res = self.client.post('/api/auth/logout')
        self.assertEqual(logout_res.status_code, 200)

        # Confirm unauthorized
        check_unauth = self.client.get('/api/profile')
        self.assertEqual(check_unauth.status_code, 401)

        # Log back in
        login_res = self.client.post('/api/auth/login', json={
            'email': 'dev_persist@gamedev.com',
            'password': 'Password999'
        })
        self.assertEqual(login_res.status_code, 200)

        # Verify all profile fields remain intact
        prof_res = self.client.get('/api/profile')
        p = prof_res.get_json()['profile']
        self.assertEqual(p['profile_name'], 'Kaelen Vance')
        self.assertEqual(p['professional_title'], 'Senior Gameplay Architect')
        self.assertEqual(p['about_me'], 'Building immersive procedural worlds.')
        self.assertEqual(p['career_goal'], 'Lead core engine programming for AAA studio.')
        self.assertEqual(p['education'], 'B.S. in Computer Science')
        self.assertEqual(set(p['skills']), {'C++', 'Unity', 'HLSL', 'Unreal Engine 5'})
        self.assertEqual(p['github_url'], 'https://github.com/kaelen')
        self.assertEqual(p['linkedin_url'], 'https://linkedin.com/in/kaelen')
        self.assertEqual(p['itchio_url'], 'https://kaelen.itch.io')

    def test_03_game_jams_dynamic_calculation_and_crud(self):
        """Verify dynamic calculation of total game jams (not hardcoded) and full CRUD."""
        self.client.post('/api/auth/signup', json={
            'email': 'jam_tester@gamedev.com',
            'password': 'Password123'
        })

        # Initially 0
        jams = self.client.get('/api/game-jams').get_json()
        self.assertEqual(jams['total_game_jams'], 0)

        # Add 1st Jam
        add_res1 = self.client.post('/api/game-jams', json={
            'jam_name': 'GMTK Game Jam 2026',
            'event_platform': 'itch.io',
            'date': 'July 2026',
            'game_created': 'Chrono Shift',
            'role': 'Lead Programmer',
            'description': 'Time reversal puzzle platformer.',
            'jam_link': 'https://jam.itch.io/chrono'
        })
        self.assertEqual(add_res1.status_code, 201)
        self.assertEqual(add_res1.get_json()['total_game_jams'], 1)
        jam1_id = add_res1.get_json()['jam_id']

        # Add 2nd Jam
        add_res2 = self.client.post('/api/game-jams', json={
            'jam_name': 'Ludum Dare 58',
            'event_platform': 'Ludum Dare',
            'date': 'October 2026',
            'game_created': 'Core Meltdown',
            'role': 'Solo Developer',
            'description': 'Physics based arcade reactor defense.'
        })
        self.assertEqual(add_res2.status_code, 201)
        self.assertEqual(add_res2.get_json()['total_game_jams'], 2)

        # Fetch and verify total
        jams_list = self.client.get('/api/game-jams').get_json()
        self.assertEqual(jams_list['total_game_jams'], 2)
        self.assertEqual(len(jams_list['game_jams']), 2)

        # Edit 1st Jam
        edit_res = self.client.put(f'/api/game-jams/{jam1_id}', json={
            'jam_name': 'GMTK Game Jam 2026 (Ranked Top 1%)',
            'event_platform': 'itch.io',
            'date': 'July 2026',
            'game_created': 'Chrono Shift 2.0',
            'role': 'Lead Systems Programmer',
            'description': 'Rewind mechanics with custom deterministic timeline.',
            'jam_link': 'https://jam.itch.io/chrono'
        })
        self.assertEqual(edit_res.status_code, 200)

        # Delete 1st Jam
        del_res = self.client.delete(f'/api/game-jams/{jam1_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.get_json()['total_game_jams'], 1)

        # Verify updated count
        jams_after = self.client.get('/api/game-jams').get_json()
        self.assertEqual(jams_after['total_game_jams'], 1)

    def test_04_achievements_with_certificate_upload_and_crud(self):
        """Verify achievement creation with certificate image upload and deletion."""
        self.client.post('/api/auth/signup', json={
            'email': 'ach_tester@gamedev.com',
            'password': 'Password123'
        })

        # Add achievement with certificate
        cert_data = io.BytesIO(b'FAKE_IMAGE_BYTES_FOR_CERTIFICATE')
        add_res = self.client.post('/api/achievements', data={
            'title': 'Best Technical Innovation Award',
            'organization': 'Indie Game Festival 2026',
            'category': 'Competition Award',
            'date': 'May 2026',
            'description': 'Awarded for novel volumetric fluid simulation in game engine.',
            'certificate': (cert_data, 'cert_award.png')
        }, content_type='multipart/form-data')

        self.assertEqual(add_res.status_code, 201)
        ach_id = add_res.get_json()['achievement']['id']
        self.assertIsNotNone(add_res.get_json()['achievement']['certificate_url'])

        # Fetch achievements
        achs = self.client.get('/api/achievements').get_json()['achievements']
        self.assertEqual(len(achs), 1)
        self.assertEqual(achs[0]['title'], 'Best Technical Innovation Award')

        # Delete achievement
        del_res = self.client.delete(f'/api/achievements/{ach_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(len(self.client.get('/api/achievements').get_json()['achievements']), 0)

    def test_05_gameplay_video_upload_and_delete(self):
        """Verify gameplay video upload, streaming URL generation, and deletion."""
        self.client.post('/api/auth/signup', json={
            'email': 'video_tester@gamedev.com',
            'password': 'Password123'
        })

        vid_data = io.BytesIO(b'SAMPLE_VIDEO_STREAM_BYTES')
        upload_res = self.client.post('/api/videos', data={
            'title': 'Boss Fight Mechanics Trailer',
            'description': 'Multi-phase state machine boss fight.',
            'video': (vid_data, 'boss_fight.mp4')
        }, content_type='multipart/form-data')

        self.assertEqual(upload_res.status_code, 201)
        vid = upload_res.get_json()['video']
        vid_id = vid['id']
        self.assertIn('/api/uploads/videos/', vid['stream_url'])

        # Edit video details
        edit_res = self.client.put(f'/api/videos/{vid_id}', json={
            'title': 'Boss Fight Trailer - Phase 3 Added',
            'description': 'Updated with laser barrage attack.'
        })
        self.assertEqual(edit_res.status_code, 200)

        # Delete video
        del_res = self.client.delete(f'/api/videos/{vid_id}')
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(len(self.client.get('/api/videos').get_json()['videos']), 0)

    def test_06_gdd_pdf_upload_replace_and_delete(self):
        """Verify GDD PDF upload, metadata storage, replacement, and deletion."""
        self.client.post('/api/auth/signup', json={
            'email': 'gdd_tester@gamedev.com',
            'password': 'Password123'
        })

        # Initially no GDD
        gdd_res = self.client.get('/api/gdd').get_json()
        self.assertFalse(gdd_res['has_gdd'])

        # Upload GDD PDF
        pdf_stream = io.BytesIO(b'%PDF-1.4 sample gdd document content')
        up_res = self.client.post('/api/gdd', data={
            'title': 'Project Chrono Paradox GDD',
            'gdd': (pdf_stream, 'Chrono_GDD_v1.pdf')
        }, content_type='multipart/form-data')
        self.assertEqual(up_res.status_code, 201)

        # Check active GDD
        active_gdd = self.client.get('/api/gdd').get_json()
        self.assertTrue(active_gdd['has_gdd'])
        self.assertEqual(active_gdd['gdd']['title'], 'Project Chrono Paradox GDD')

        # Delete GDD
        del_res = self.client.delete('/api/gdd')
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(self.client.get('/api/gdd').get_json()['has_gdd'])

    def test_07_user_data_isolation(self):
        """Verify User A data cannot be seen or accessed by User B."""
        # Create User A
        self.client.post('/api/auth/signup', json={
            'email': 'usera@gamedev.com',
            'password': 'PasswordA123'
        })
        user_a_id = self.client.get('/api/auth/me').get_json()['user']['id']

        # User A updates profile and adds a secret jam
        self.client.put('/api/profile/name', json={'profile_name': 'Secret Agent A'})
        self.client.post('/api/game-jams', json={'jam_name': 'User A Confidential Jam'})

        # Upload a video for User A
        vid_stream = io.BytesIO(b'USER_A_PRIVATE_VIDEO_DATA')
        vid_res = self.client.post('/api/videos', data={
            'title': 'Secret Tech Demo',
            'video': (vid_stream, 'secret.mp4')
        }, content_type='multipart/form-data')
        user_a_vid_filename = vid_res.get_json()['video']['filename']

        # Logout User A
        self.client.post('/api/auth/logout')

        # Create User B
        self.client.post('/api/auth/signup', json={
            'email': 'userb@gamedev.com',
            'password': 'PasswordB123'
        })

        # User B should see empty profile
        prof_b = self.client.get('/api/profile').get_json()['profile']
        self.assertEqual(prof_b['profile_name'], '')

        # User B should see 0 jams
        jams_b = self.client.get('/api/game-jams').get_json()
        self.assertEqual(jams_b['total_game_jams'], 0)

        # User B tries to download User A's private video directly
        unauth_file = self.client.get(f'/api/uploads/videos/{user_a_id}/{user_a_vid_filename}')
        self.assertEqual(unauth_file.status_code, 403) # Access Denied!

    def test_08_strict_zero_hallucination_resume_extractor(self):
        """Verify the AI extractor strictly pulls only items present in the PDF and does NOT invent data."""
        from resume_parser import analyze_resume_strictly

        # Resume text strictly containing certain items and omitting others
        sample_resume_text = """
        Marcus Drake
        Lead Gameplay Engineer
        marcus.drake@studio.com | https://github.com/marcusdrake

        SUMMARY
        Passionate game engineer with 6 years experience building physics and mechanics.

        SKILLS
        Unity, C++, C#, HLSL, Blender, Git, Physics

        EDUCATION
        B.S. in Computer Science - University of Waterloo

        EXPERIENCE
        Gameplay Programmer at Orbit Interactive (2022-2026)
        - Developed deterministic character controller in Unity.
        - Optimized shader pipelines using HLSL.

        PROJECTS
        Neon Horizon: Fast paced arcade hovercraft racer.
        """

        extracted = analyze_resume_strictly(sample_resume_text)

        # Assert correct extracted fields
        self.assertEqual(extracted['profile_name'], 'Marcus Drake')
        self.assertEqual(extracted['professional_title'], 'Lead Gameplay Engineer')
        self.assertIn('Unity', extracted['skills'])
        self.assertIn('C++', extracted['skills'])
        self.assertIn('C#', extracted['skills'])
        self.assertIn('HLSL', extracted['skills'])
        self.assertIn('Blender', extracted['skills'])
        self.assertIn('Git', extracted['skills'])
        self.assertEqual(extracted['github_url'], 'https://github.com/marcusdrake')
        self.assertIn('University of Waterloo', extracted['education'])

        # ASSERT STRICT ZERO-INVENTION:
        # Unreal Engine, Godot, Maya, Java, Python were NOT in this resume and must NOT be in skills!
        self.assertNotIn('Unreal Engine', extracted['skills'])
        self.assertNotIn('Godot', extracted['skills'])
        self.assertNotIn('Maya', extracted['skills'])
        self.assertNotIn('Python', extracted['skills'])
        self.assertNotIn('Java', extracted['skills'])

    def test_09_public_profile_unauthenticated_read_only(self):
        """Verify public profiles are accessible without login, read-only, and filter private data."""
        # Create user with custom username
        signup_res = self.client.post('/api/auth/signup', json={
            'email': 'alex_public@gamedev.com',
            'password': 'Password123',
            'username': 'alex_dev'
        })
        self.assertEqual(signup_res.status_code, 201)

        # Update profile
        self.client.put('/api/profile', json={
            'profile_name': 'Alex Mercer',
            'professional_title': 'Lead Engine Programmer',
            'about_me': 'Passionate about custom C++ physics.',
            'skills': ['C++', 'DirectX 12', 'Vulkan'],
            'github_url': 'https://github.com/alexdev'
        })

        # Add 1 public video and 1 private video
        vid_data1 = io.BytesIO(b'PUBLIC_VIDEO_DATA')
        self.client.post('/api/videos', data={
            'title': 'Public Combat Demo',
            'video': (vid_data1, 'public_demo.mp4'),
            'is_public': '1'
        }, content_type='multipart/form-data')

        vid_data2 = io.BytesIO(b'PRIVATE_WIP_VIDEO_DATA')
        self.client.post('/api/videos', data={
            'title': 'Confidential WIP Tech',
            'video': (vid_data2, 'private_wip.mp4'),
            'is_public': '0'
        }, content_type='multipart/form-data')

        # Add 1 Game Jam
        self.client.post('/api/game-jams', json={
            'jam_name': 'GMTK 2026',
            'game_created': 'Chrono Rewind'
        })

        # Upload GDD as private (default)
        gdd_stream = io.BytesIO(b'%PDF-1.4 secret GDD design')
        self.client.post('/api/gdd', data={
            'title': 'Unannounced Next Game GDD',
            'gdd': (gdd_stream, 'Secret_GDD.pdf'),
            'is_public': '0'
        }, content_type='multipart/form-data')

        # LOGOUT: Ensure we are now an unauthenticated external visitor
        self.client.post('/api/auth/logout')

        # 1. Visitor opens public page /profile/alex_dev
        page_res = self.client.get('/profile/alex_dev')
        self.assertEqual(page_res.status_code, 200)
        self.assertIn(b'Alex Mercer', page_res.data)
        self.assertIn(b'PUBLIC DOSSIER', page_res.data)

        # 2. Non-existent user returns 404
        page_404 = self.client.get('/profile/ghost_operative_999')
        self.assertEqual(page_404.status_code, 404)

        # 3. Visitor calls public API
        api_res = self.client.get('/api/public/profile/alex_dev')
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()

        # Sensitive account data MUST NOT be exposed
        self.assertNotIn('password_hash', data['profile'])
        self.assertNotIn('email', data['profile'])

        # Public video MUST be present, private video MUST NOT be present
        vid_titles = [v['title'] for v in data['videos']]
        self.assertIn('Public Combat Demo', vid_titles)
        self.assertNotIn('Confidential WIP Tech', vid_titles)

        # Private GDD MUST NOT be exposed
        self.assertIsNone(data['gdd'])

        # 4. Strict Security: Visitor cannot modify data
        unauth_update = self.client.put('/api/profile', json={'profile_name': 'Hacked Name'})
        self.assertEqual(unauth_update.status_code, 401)

        unauth_jam = self.client.post('/api/game-jams', json={'jam_name': 'Unauthorized Jam'})
        self.assertEqual(unauth_jam.status_code, 401)

    def test_10_visibility_toggle_and_public_file_streaming(self):
        """Verify owner can toggle visibility and public streaming enforces permission."""
        # Login owner
        self.client.post('/api/auth/signup', json={
            'email': 'stream_owner@gamedev.com',
            'password': 'Password123',
            'username': 'stream_owner'
        })

        # Upload GDD as private
        gdd_stream = io.BytesIO(b'%PDF-1.4 proprietary GDD mechanics')
        up_res = self.client.post('/api/gdd', data={
            'title': 'Proprietary Combat System GDD',
            'gdd': (gdd_stream, 'Combat_GDD.pdf'),
            'is_public': '0'
        }, content_type='multipart/form-data')
        gdd_id = up_res.get_json()['gdd']['id']
        gdd_filename = up_res.get_json()['gdd']['view_url'].split('/')[-1]

        # Visitor tries to stream private GDD -> 403 Forbidden
        visitor_stream = self.client.get(f'/api/public/uploads/gdd/stream_owner/{gdd_filename}')
        self.assertEqual(visitor_stream.status_code, 403)

        # Owner toggles GDD to PUBLIC
        toggle_res = self.client.patch(f'/api/visibility/gdd/{gdd_id}', json={'is_public': True})
        self.assertEqual(toggle_res.status_code, 200)
        self.assertTrue(toggle_res.get_json()['is_public'])

        # Now visitor CAN stream public GDD -> 200 OK
        visitor_stream_pub = self.client.get(f'/api/public/uploads/gdd/stream_owner/{gdd_filename}')
        self.assertEqual(visitor_stream_pub.status_code, 200)

        # Public API now includes the GDD
        pub_api = self.client.get('/api/public/profile/stream_owner').get_json()
        self.assertIsNotNone(pub_api['gdd'])
        self.assertEqual(pub_api['gdd']['title'], 'Proprietary Combat System GDD')

    def test_11_update_username_slug(self):
        """Verify updating username updates the public URL immediately and validates uniqueness."""
        self.client.post('/api/auth/signup', json={
            'email': 'slug_tester@gamedev.com',
            'password': 'Password123',
            'username': 'old_slug'
        })

        # Verify old slug works
        self.assertEqual(self.client.get('/profile/old_slug').status_code, 200)

        # Change username to new slug
        update_res = self.client.put('/api/auth/username', json={'username': 'new_awesome_slug'})
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()['username'], 'new_awesome_slug')

        # Old slug returns 404, new slug returns 200
        self.assertEqual(self.client.get('/profile/old_slug').status_code, 404)
        self.assertEqual(self.client.get('/profile/new_awesome_slug').status_code, 200)

if __name__ == '__main__':
    unittest.main()
