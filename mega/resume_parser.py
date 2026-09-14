"""
GameDev Journey - Zero-Hallucination AI Resume Extractor
Reads PDF resumes using pypdf and strictly extracts information ONLY present in the document.
Strictly prohibits inventing skills, experiences, projects, or achievements.
"""

import re
from typing import Dict, Any, List
from pypdf import PdfReader

# Comprehensive canonical lexicon of Game Development & Software Engineering terms.
# A skill is ONLY extracted if it literally appears in the user's resume text.
KNOWN_SKILLS = [
    # Engines & Frameworks
    "Unity", "Unity 3D", "Unity 2D", "Unreal Engine", "Unreal Engine 4", "Unreal Engine 5", "UE4", "UE5",
    "Godot", "CryEngine", "Construct", "GameMaker", "RPG Maker", "Phaser", "PixiJS", "Three.js", "Bevy",
    # Programming Languages
    "C++", "C#", "C", "Python", "Lua", "Rust", "HLSL", "GLSL", "ShaderLab", "Java", "JavaScript", 
    "TypeScript", "HTML5", "CSS3", "SQL", "Go", "Kotlin", "Swift", "Assembly",
    # Graphics, Shaders & 3D Math
    "Shaders", "Compute Shaders", "Ray Marching", "DirectX", "DirectX 11", "DirectX 12", "OpenGL", 
    "Vulkan", "Metal", "WebGL", "WebGPU", "Linear Algebra", "3D Math", "Quaternions", "Physics Engines",
    # Tools & DCC Software
    "Blender", "Maya", "3ds Max", "ZBrush", "Substance Painter", "Substance Designer", "Photoshop",
    "Figma", "Houdini", "Aseprite", "Audacity", "FMOD", "Wwise",
    # Version Control & DevOps
    "Git", "GitHub", "GitLab", "Perforce", "Plastic SCM", "SVN", "CI/CD", "Docker", "CMake", "Jenkins",
    # Game Systems & Disciplines
    "Gameplay Programming", "Physics", "AI Programming", "NavMesh", "Pathfinding", "Behavior Trees",
    "Finite State Machines", "Animation Systems", "Inverse Kinematics", "Rigging", "Level Design",
    "Game Design", "Narrative Design", "UI/UX", "System Architecture", "Object-Oriented Programming",
    "Design Patterns", "Data-Oriented Design", "ECS", "DOTS", "Multiplayer", "Netcode", "Mirror",
    "Photon", "WebSocket", "Client-Server Architecture", "Procedural Generation", "Optimization",
    "Profiling", "Memory Management", "Multithreading", "Agile", "Scrum", "Jira"
]

SECTION_PATTERNS = {
    'summary': re.compile(r'^(summary|professional summary|about me|profile|career objective|objective)\b', re.IGNORECASE),
    'skills': re.compile(r'^(technical skills|skills|technologies|core competencies|tools & technologies|proficiencies)\b', re.IGNORECASE),
    'experience': re.compile(r'^(experience|work experience|employment history|professional experience|work history)\b', re.IGNORECASE),
    'education': re.compile(r'^(education|academic background|qualifications|academic history)\b', re.IGNORECASE),
    'projects': re.compile(r'^(projects|game projects|key projects|portfolio projects|personal projects)\b', re.IGNORECASE),
    'certifications': re.compile(r'^(certifications|certificates|licenses|credentials)\b', re.IGNORECASE),
    'achievements': re.compile(r'^(achievements|awards|honors & awards|accomplishments)\b', re.IGNORECASE),
}

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}')
URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+|(?:github|linkedin|itch)\.com/[^\s]+', re.IGNORECASE)

def extract_raw_text(file_path_or_stream) -> str:
    """Extract clean raw text from a PDF file."""
    reader = PdfReader(file_path_or_stream)
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text)
    return "\n".join(text_chunks)

def segment_resume_sections(lines: List[str]) -> Dict[str, List[str]]:
    """Segment resume text lines into recognized sections."""
    sections: Dict[str, List[str]] = {
        'header': [],
        'summary': [],
        'skills': [],
        'experience': [],
        'education': [],
        'projects': [],
        'certifications': [],
        'achievements': [],
        'other': []
    }
    
    current_sec = 'header'
    
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
            
        # Check if line matches any section header
        matched_sec = None
        # Heuristic: headers are usually short (under 40 chars)
        if len(cleaned) < 45:
            for sec_key, pattern in SECTION_PATTERNS.items():
                if pattern.match(cleaned.replace(':', '')):
                    matched_sec = sec_key
                    break
                    
        if matched_sec:
            current_sec = matched_sec
        else:
            sections[current_sec].append(cleaned)
            
    return sections

def extract_strict_name_and_title(header_lines: List[str], all_lines: List[str]) -> Dict[str, str]:
    """
    Extract the user's name and professional title strictly from the resume.
    Does NOT invent names or titles.
    """
    name = ""
    title = ""
    
    # Check top lines of the resume
    candidates = header_lines if header_lines else all_lines[:8]
    
    for line in candidates:
        text = line.strip()
        if not text:
            continue
            
        # Skip contact information lines
        if EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text) or URL_PATTERN.search(text):
            continue
            
        # Clean special chars
        clean_line = re.sub(r'[^a-zA-Z\s\.\-]', '', text).strip()
        words = clean_line.split()
        
        # Name heuristic: 2 to 4 words, reasonable capitalization
        if not name and 1 <= len(words) <= 4 and len(clean_line) < 35:
            if not any(k.lower() in clean_line.lower() for k in ['curriculum', 'resume', 'page', 'portfolio', 'developer', 'engineer']):
                name = clean_line
                continue
                
        # Professional title heuristic
        if not title and len(text) < 60:
            lower_text = text.lower()
            if any(role in lower_text for role in [
                'developer', 'engineer', 'programmer', 'designer', 'artist', 
                'lead', 'intern', 'specialist', 'creator', 'architect'
            ]):
                title = text
                continue

    return {
        'name': name,
        'title': title
    }

def extract_strict_skills(resume_text: str, skill_section_lines: List[str]) -> List[str]:
    """
    Extract skills strictly verified to exist in the resume text.
    Only skills that actually appear in the resume are included.
    """
    found_skills = set()
    
    # 1. Direct match against known tech terms across full resume text
    for skill in KNOWN_SKILLS:
        # Regex boundary match
        # Escape any regex chars like + in C++
        pattern = r'(?<![A-Za-z0-9])' + re.escape(skill) + r'(?![A-Za-z0-9])'
        if re.search(pattern, resume_text, re.IGNORECASE):
            found_skills.add(skill)
            
    # 2. Extract specific comma or bullet separated tokens from the skills section
    for line in skill_section_lines:
        tokens = re.split(r'[,|•·\n;]+', line)
        for tok in tokens:
            t = tok.strip()
            if t and 2 <= len(t) <= 30:
                # Avoid sentence fragments
                if not re.search(r'\b(and|with|over|responsible|created|years|experience)\b', t, re.IGNORECASE):
                    # Check if token exists in full resume text
                    if t.lower() in resume_text.lower():
                        found_skills.add(t)

    return sorted(list(found_skills), key=lambda x: x.lower())

def extract_strict_socials(resume_text: str) -> Dict[str, str]:
    """Extract GitHub, LinkedIn, and itch.io URLs strictly if found in the text."""
    github = ""
    linkedin = ""
    itchio = ""
    
    gh_match = re.search(r'(https?://)?(www\.)?github\.com/[A-Za-z0-9_-]+', resume_text, re.IGNORECASE)
    if gh_match:
        github = gh_match.group(0)
        if not github.startswith('http'):
            github = 'https://' + github
            
    li_match = re.search(r'(https?://)?([a-z]{2,3}\.)?linkedin\.com/(in/)?[A-Za-z0-9_-]+', resume_text, re.IGNORECASE)
    if li_match:
        linkedin = li_match.group(0)
        if not linkedin.startswith('http'):
            linkedin = 'https://' + linkedin
            
    itch_match = re.search(r'(https?://)?([A-Za-z0-9_-]+\.)?itch\.io(/[A-Za-z0-9_-]+)?', resume_text, re.IGNORECASE)
    if itch_match:
        itchio = itch_match.group(0)
        if not itchio.startswith('http'):
            itchio = 'https://' + itchio
            
    return {
        'github': github,
        'linkedin': linkedin,
        'itchio': itchio
    }

def analyze_resume_strictly(raw_text: str) -> Dict[str, Any]:
    """
    Main extraction function. Strictly follows the rule:
    NEVER invent skills, experience, projects, achievements, education, or personal info.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    sections = segment_resume_sections(lines)
    
    name_title = extract_strict_name_and_title(sections['header'], lines)
    skills = extract_strict_skills(raw_text, sections['skills'])
    socials = extract_strict_socials(raw_text)
    
    # Extract clean text blocks for education, experience, etc.
    education = "\n".join(sections['education']).strip()
    experience = "\n".join(sections['experience']).strip()
    projects = "\n".join(sections['projects']).strip()
    certifications = "\n".join(sections['certifications']).strip()
    achievements = "\n".join(sections['achievements']).strip()
    about_me = "\n".join(sections['summary']).strip()
    
    return {
        'profile_name': name_title['name'],
        'professional_title': name_title['title'],
        'about_me': about_me,
        'skills': skills,
        'education': education,
        'experience': experience,
        'projects': projects,
        'certifications': certifications,
        'achievements': achievements,
        'github_url': socials['github'],
        'linkedin_url': socials['linkedin'],
        'itchio_url': socials['itchio'],
        'raw_text_length': len(raw_text)
    }
