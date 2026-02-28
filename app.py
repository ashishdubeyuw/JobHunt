"""
Job Matching & Resume Analysis Application
Main Streamlit Dashboard

A comprehensive job matching platform using LlamaIndex, LangChain, and Google Gemini.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from modules.scrapers import JobScraper, load_mock_jobs
from modules.parsers import ResumeParser
from modules.matching_engine import MatchingEngine, MatchResult
from modules.agents import RecruiterAssistant, CoverLetterGenerator
from modules.scheduler import JobSearchScheduler, UserProfile
from modules.notifications import send_email_notification, send_whatsapp_notification
from modules.web_search import WebJobSearch, search_web_jobs

# Page configuration
st.set_page_config(
    page_title="Job Genie AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Clean, accessible design with good color contrast
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* ===== BASE STYLES ===== */

    /* Simple solid dark background - no distracting animation */
    .stApp {
        background: #1a1a2e;
    }

    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #e8eaf0;
    }

    /* Main container */
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
    }

    /* ===== HEADER ===== */
    .header-gradient {
        background: #16213e;
        border: 1px solid #2d3561;
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }

    .header-gradient h1 {
        color: #ffffff !important;
        margin: 0;
        font-weight: 800;
        font-size: 2.5rem;
    }

    .header-gradient p {
        color: #c5cae9;
        margin: 0.75rem 0 0 0;
        font-size: 1.1rem;
    }

    /* ===== CARDS ===== */
    .glass-card, .job-card {
        background: #16213e;
        border: 1px solid #2d3561;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    .glass-card:hover, .job-card:hover {
        background: #1e2a4a;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        border-color: #4a5568;
    }

    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: #16213e;
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        background: #1e2a4a;
        transform: scale(1.02);
    }

    .metric-value {
        font-size: 2.25rem;
        font-weight: 800;
        color: #7c9ef8;
    }

    .metric-value-success {
        font-size: 2.25rem;
        font-weight: 800;
        color: #4ade80;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #a0aec0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ===== SCORE BADGES ===== */
    .score-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 700;
        border: 1px solid transparent;
    }

    .score-excellent {
        background: #14532d;
        color: #86efac;
        border-color: #16a34a;
    }
    .score-good {
        background: #1e3a5f;
        color: #93c5fd;
        border-color: #2563eb;
    }
    .score-partial {
        background: #451a03;
        color: #fcd34d;
        border-color: #d97706;
    }

    /* ===== SIDEBAR BASE ===== */
    [data-testid="stSidebar"] {
        background: #0f172a !important;
        border-right: 2px solid #2d3561 !important;
    }

    /* ===== SIDEBAR - desktop: always visible and fixed ===== */
    @media (min-width: 769px) {
        [data-testid="stSidebar"] {
            min-width: 21rem !important;
            transform: none !important;
            position: sticky !important;
            top: 0 !important;
            height: 100vh !important;
        }

        /* Hide the collapse/expand toggle on desktop only */
        [data-testid="collapsedControl"],
        button[data-testid="baseButton-headerNoPadding"] {
            display: none !important;
        }
    }

    /* ===== SIDEBAR - mobile: collapsible via native Streamlit toggle ===== */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            min-width: unset !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            z-index: 999 !important;
            width: 78vw !important;
            max-width: 18rem !important;
            overflow-y: auto !important;
        }

        /* Show the collapse/expand toggle on mobile */
        [data-testid="collapsedControl"],
        button[data-testid="baseButton-headerNoPadding"] {
            display: flex !important;
        }
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #e8eaf0;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: #3d52a0;
        color: #ffffff;
        border: 1px solid #4a6cf7;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(61, 82, 160, 0.4);
    }

    .stButton > button:hover {
        background: #4a6cf7;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(74, 108, 247, 0.5);
    }

    /* ===== INPUTS ===== */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background: #16213e !important;
        border: 1px solid #2d3561 !important;
        border-radius: 10px !important;
        color: #e8eaf0 !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #4a6cf7 !important;
        box-shadow: 0 0 0 2px rgba(74, 108, 247, 0.3) !important;
    }

    /* ===== FILE UPLOADER ===== */
    .stFileUploader {
        background: #16213e;
        border: 2px dashed #4a5568;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .stFileUploader:hover {
        border-color: #4a6cf7;
        background: #1e2a4a;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: #16213e !important;
        border-radius: 10px;
        font-weight: 600;
        color: #e8eaf0 !important;
    }

    .streamlit-expanderContent {
        background: #0f172a;
        border-radius: 0 0 10px 10px;
        border: 1px solid #2d3561;
    }

    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: #2d3561;
        margin: 1.5rem 0;
    }

    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.75rem 1rem;
        }

        .header-gradient {
            padding: 1.5rem 1rem;
            border-radius: 12px;
        }

        .header-gradient h1 {
            font-size: 1.75rem;
        }

        .glass-card, .job-card {
            padding: 1rem;
            border-radius: 10px;
        }

        .metric-value {
            font-size: 1.75rem;
        }
    }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ===== SCROLLBAR STYLING ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #16213e;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: #2d3561;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #4a5568;
    }

    /* ===== LINKS ===== */
    a {
        color: #7c9ef8;
        text-decoration: none;
        transition: all 0.2s ease;
    }

    a:hover {
        color: #a5b4fc;
        text-decoration: underline;
    }

    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetricValue"] {
        color: #7c9ef8 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #a0aec0 !important;
    }

    /* ===== INFO/SUCCESS/WARNING BOXES ===== */
    .stAlert {
        border-radius: 10px !important;
    }

    /* ===== TEXT COLORS ===== */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    .stText, p, span, label, div, li, td, th,
    .job-card *, .glass-card *,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"],
    .element-container * {
        color: #e8eaf0 !important;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #ffffff !important;
    }

    /* Job card titles */
    .job-card h3, .job-card h4, .job-card strong, .job-card b {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Labels and captions */
    .stCaption, small {
        color: #a0aec0 !important;
    }

    /* Checkboxes and radio labels */
    .stCheckbox label, .stRadio label, .stSelectbox label {
        color: #e8eaf0 !important;
    }

    /* Expander text */
    .streamlit-expanderContent *, .streamlit-expanderHeader * {
        color: #e8eaf0 !important;
    }

    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #e8eaf0 !important;
    }

    /* Tab text */
    .stTabs [data-baseweb="tab"] {
        color: #e8eaf0 !important;
    }

    /* Code blocks */
    code {
        color: #a5b4fc !important;
        background: #16213e !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("GOOGLE_API_KEY", "")
    if "resume_data" not in st.session_state:
        st.session_state.resume_data = None
    if "matched_jobs" not in st.session_state:
        st.session_state.matched_jobs = []
    if "jobs" not in st.session_state:
        st.session_state.jobs = []
    if "matching_engine" not in st.session_state:
        st.session_state.matching_engine = None
    if "demo_mode" not in st.session_state:
        st.session_state.demo_mode = False
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "web_search_enabled" not in st.session_state:
        st.session_state.web_search_enabled = True
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def render_sidebar():
    """Render the sidebar with settings and file upload."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Key Configuration
        with st.expander("🔑 API Configuration", expanded=not st.session_state.api_key):
            api_key = st.text_input(
                "Google Gemini API Key",
                value=st.session_state.api_key,
                type="password",
                help="Get your free API key from Google AI Studio"
            )
            if api_key != st.session_state.api_key:
                st.session_state.api_key = api_key
                st.session_state.matching_engine = None  # Reset engine
            
            st.session_state.demo_mode = st.checkbox(
                "🎮 Demo Mode (No API needed)",
                value=st.session_state.demo_mode,
                help="Use mock data and basic matching without AI features"
            )
            
            st.divider()
            
            # Web Search Toggle
            st.session_state.web_search_enabled = st.checkbox(
                "🌐 Search Real Jobs (Web)",
                value=st.session_state.web_search_enabled,
                help="Search real job listings from LinkedIn, Indeed, etc."
            )
            
            if st.session_state.web_search_enabled:
                st.success("✅ No API key required! Searches real jobs automatically.")
                
                st.session_state.search_query = st.text_input(
                    "Job Search Query (optional)",
                    value=st.session_state.search_query or "",
                    placeholder="Leave empty to auto-search using your resume skills"
                )
                st.caption("💡 Leave blank — we'll use your resume skills to find matching jobs automatically")
                
                with st.expander("🔑 Optional: Add API for better results"):
                    st.caption("Our Google Jobs scraper works without API. Add these for more results:")
                    
                    rapidapi_key = st.text_input(
                        "RapidAPI Key (JSearch - 500 free/month)",
                        type="password",
                        help="Optional backup source"
                    )
                    if rapidapi_key:
                        os.environ["RAPIDAPI_KEY"] = rapidapi_key
                    
                    serper_key = st.text_input(
                        "Serper.dev API Key (2500 free)",
                        type="password",
                        help="Optional backup source"
                    )
                    if serper_key:
                        os.environ["SERPER_API_KEY"] = serper_key
        
        st.divider()
        
        # Resume Upload
        st.markdown("## 📄 Upload Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"],
            help="We'll extract your skills and experience to find matching jobs",
            key="resume_uploader"
        )
        
        if uploaded_file is not None:
            with st.spinner("📖 Parsing resume..."):
                parser = ResumeParser()
                resume_data = parser.parse_pdf(uploaded_file)
                st.session_state.resume_data = resume_data
                
                # Show parsed info
                st.success("✅ Resume parsed!")
                with st.expander("View extracted info"):
                    st.write(f"**Skills:** {len(resume_data.get('skills', []))} found")
                    st.write(f"**Experience:** {resume_data.get('experience_years', 0)} years")
                    if resume_data.get('email'):
                        st.write(f"**Email:** {resume_data['email']}")
        
        st.divider()
        
        # Auto-Search Settings
        st.markdown("## ⏰ Auto-Search Settings")
        
        schedule_enabled = st.toggle("Enable Scheduled Search", value=False)
        
        if schedule_enabled:
            col1, col2 = st.columns(2)
            with col1:
                frequency = st.selectbox(
                    "Frequency",
                    ["Daily", "Weekly"],
                    index=0
                )
            with col2:
                notify_time = st.time_input("Time", value=None)
            
            notification_channel = st.radio(
                "Notification Channel",
                ["📧 Email", "📱 WhatsApp", "Both"],
                horizontal=True
            )
            
            if "Email" in notification_channel or notification_channel == "Both":
                notify_email = st.text_input("Email Address")
            if "WhatsApp" in notification_channel or notification_channel == "Both":
                notify_phone = st.text_input("WhatsApp Number (+1...)")
            
            if st.button("💾 Save Schedule", use_container_width=True):
                st.success("✅ Schedule saved!")
        
        st.divider()
        
        # Quick Stats
        if st.session_state.matched_jobs:
            st.markdown("## 📊 Quick Stats")
            st.metric("Jobs Matched", len(st.session_state.matched_jobs))
            if st.session_state.matched_jobs:
                top_score = st.session_state.matched_jobs[0].final_score
                st.metric("Best Match Score", f"{int(top_score * 100)}%")


def render_header():
    """Render the header section."""
    st.markdown("""
    <div class="header-gradient">
        <h1>🎯 Job Genie AI</h1>
        <p>Find your perfect job match powered by AI-driven resume analysis</p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(matched_jobs: List[MatchResult]):
    """Render metrics cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(matched_jobs)}</div>
            <div class="metric-label">Jobs Matched</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        excellent = sum(1 for j in matched_jobs if j.final_score >= 0.8)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value-success">{excellent}</div>
            <div class="metric-label">Excellent Matches</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if matched_jobs:
            avg_score = sum(j.final_score for j in matched_jobs) / len(matched_jobs)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{int(avg_score * 100)}%</div>
                <div class="metric-label">Avg Match Score</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">-</div>
                <div class="metric-label">Avg Match Score</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if st.session_state.resume_data:
            skills = len(st.session_state.resume_data.get("skills", []))
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{skills}</div>
                <div class="metric-label">Skills Detected</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">-</div>
                <div class="metric-label">Skills Detected</div>
            </div>
            """, unsafe_allow_html=True)


def render_job_card(match: MatchResult, index: int):
    """Render a single job card."""
    job = match.job
    score_pct = int(match.final_score * 100)
    
    # Determine score class
    if score_pct >= 80:
        score_class = "score-excellent"
        score_emoji = "🟢"
    elif score_pct >= 60:
        score_class = "score-good"
        score_emoji = "🔵"
    else:
        score_class = "score-partial"
        score_emoji = "🟡"
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {index}. {job.get('title', 'Position')}")
            st.markdown(f"**{job.get('company', 'Company')}** • {job.get('location', 'Location')}")
            st.markdown(f"💰 {job.get('salary', 'Salary not specified')}")
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding-top: 0.5rem;">
                <span class="score-badge {score_class}">{score_emoji} {score_pct}%</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("📋 View Details & AI Analysis"):
            st.markdown("#### Job Description")
            st.write(job.get("description", "No description available")[:500] + "...")
            
            # Skills section with match indicators
            st.markdown("#### 🎯 Skills Match")
            job_skills = job.get("required_skills", [])
            resume_skills = st.session_state.resume_data.get("skills", []) if st.session_state.resume_data else []
            resume_skills_lower = [s.lower() for s in resume_skills]
            
            if job_skills or resume_skills:
                # Build skill badges HTML
                matched_skills = []
                unmatched_skills = []
                
                for skill in job_skills:
                    if skill.lower() in resume_skills_lower:
                        matched_skills.append(skill)
                    else:
                        unmatched_skills.append(skill)
                
                # Extra resume skills not in job
                extra_resume = [s for s in resume_skills if s.lower() not in [js.lower() for js in job_skills]]
                
                badges_html = ""
                
                # Matched skills - green
                for skill in matched_skills:
                    badges_html += f'''<span title="✅ MATCHED - This skill is in your resume AND required by the job" 
                        style="display:inline-block; margin:3px; padding:5px 12px; 
                        background:#14532d; border:1px solid #16a34a; 
                        border-radius:20px; font-size:0.85rem; color:#86efac; cursor:help;
                        font-weight:600;">✅ {skill}</span>'''
                
                # Unmatched job skills - red/orange
                for skill in unmatched_skills:
                    badges_html += f'''<span title="❌ GAP - This skill is required but NOT in your resume" 
                        style="display:inline-block; margin:3px; padding:5px 12px; 
                        background:#450a0a; border:1px solid #b91c1c; 
                        border-radius:20px; font-size:0.85rem; color:#fca5a5; cursor:help;
                        font-weight:500;">❌ {skill}</span>'''
                
                # Stats summary
                total_job = len(job_skills)
                matched_count = len(matched_skills)
                match_pct = int((matched_count / total_job * 100)) if total_job > 0 else 0
                
                st.markdown(f"""
                <div style="background:#16213e; border-radius:12px; padding:12px; margin-bottom:10px;
                    border:1px solid #2d3561;">
                    <div style="font-size:0.9rem; margin-bottom:8px; color:#7c9ef8;">
                        <strong>📊 Skill Match: {matched_count}/{total_job} skills ({match_pct}%)</strong>
                        &nbsp;|&nbsp; ✅ Matched: {matched_count} &nbsp;|&nbsp; ❌ Gaps: {len(unmatched_skills)}
                    </div>
                    <div>{badges_html}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show extra resume skills
                if extra_resume[:5]:
                    extra_html = ""
                    for skill in extra_resume[:5]:
                        extra_html += f'''<span title="💡 BONUS - You have this skill but it's not listed as required"
                            style="display:inline-block; margin:3px; padding:4px 10px;
                            background:#1e3a5f; border:1px solid #2563eb;
                            border-radius:20px; font-size:0.8rem; color:#93c5fd; cursor:help;">
                            💡 {skill}</span>'''
                    st.markdown(f"""
                    <details style="margin-top:6px;">
                        <summary style="cursor:pointer; color:#7c9ef8; font-size:0.85rem;">
                            💡 Your bonus skills ({len(extra_resume)} not required but valuable)
                        </summary>
                        <div style="margin-top:6px;">{extra_html}</div>
                    </details>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("_No skills data available_")
            
            st.divider()
            
            st.markdown("#### 🤖 AI Match Analysis")
            st.markdown(match.explanation)
            
            st.divider()
            
            # Score Breakdown
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Skills Match", f"{int(match.skills_score * 100)}%")
            with col_b:
                st.metric("Experience", f"{int(match.experience_score * 100)}%")
            with col_c:
                st.metric("Semantic", f"{int(match.semantic_score * 100)}%")
            
            st.divider()
            
            # Actions - Apply link opens in new tab
            apply_url = job.get("apply_url", "#")
            col_x, col_y = st.columns(2)
            with col_x:
                st.markdown(f'''
                <a href="{apply_url}" target="_blank" style="
                    display: inline-block;
                    width: 100%;
                    padding: 0.5rem 1rem;
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    text-align: center;
                    font-weight: 500;
                ">🔗 Apply Now</a>
                ''', unsafe_allow_html=True)
            
            with col_y:
                if st.button(f"✉️ Generate Cover Letter", key=f"cover_{index}", use_container_width=True):
                    st.session_state.selected_job = job
                    st.rerun()
        
        st.divider()


def render_job_list(matched_jobs: List[MatchResult]):
    """Render the list of matched jobs with pagination."""
    if not matched_jobs:
        st.info("👆 Upload your resume to see matched jobs!")
        return
    
    st.markdown("## 📋 Matched Jobs")
    st.markdown(f"Showing top {len(matched_jobs)} matches for your profile")
    
    # Filter/Sort Options
    col1, col2 = st.columns([1, 3])
    with col1:
        min_score = st.slider("Min Score", 0, 100, 0, 10)
    
    # Filter jobs
    filtered_jobs = [j for j in matched_jobs if j.final_score * 100 >= min_score]
    
    if not filtered_jobs:
        st.warning("No jobs match your filter criteria.")
        return
    
    # Pagination
    JOBS_PER_PAGE = 10
    total_pages = max(1, (len(filtered_jobs) + JOBS_PER_PAGE - 1) // JOBS_PER_PAGE)
    
    if 'job_page' not in st.session_state:
        st.session_state.job_page = 0
    
    # Ensure page is in bounds
    st.session_state.job_page = min(st.session_state.job_page, total_pages - 1)
    
    start = st.session_state.job_page * JOBS_PER_PAGE
    end = min(start + JOBS_PER_PAGE, len(filtered_jobs))
    page_jobs = filtered_jobs[start:end]
    
    st.markdown(f"**Page {st.session_state.job_page + 1} of {total_pages}** — Showing jobs {start + 1}-{end} of {len(filtered_jobs)}")
    
    # Render jobs for current page
    for i, match in enumerate(page_jobs, start + 1):
        render_job_card(match, i)
    
    # Pagination buttons
    if total_pages > 1:
        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️ Previous", disabled=(st.session_state.job_page == 0), use_container_width=True):
                st.session_state.job_page -= 1
                st.rerun()
        
        with col_info:
            st.markdown(f"<div style='text-align:center; padding:0.5rem; color:#a78bfa;'>"
                       f"<strong>Page {st.session_state.job_page + 1} / {total_pages}</strong></div>", 
                       unsafe_allow_html=True)
        
        with col_next:
            if st.button("Next ➡️", disabled=(st.session_state.job_page >= total_pages - 1), use_container_width=True):
                st.session_state.job_page += 1
                st.rerun()


def render_cover_letter_generator():
    """Render cover letter generation section."""
    if not st.session_state.selected_job:
        return
    
    job = st.session_state.selected_job
    
    st.markdown("---")
    st.markdown("## ✉️ Cover Letter Generator")
    st.markdown(f"Generating cover letter for: **{job.get('title')}** at **{job.get('company')}**")
    
    if st.button("🪄 Generate Cover Letter", use_container_width=True):
        if not st.session_state.resume_data:
            st.error("Please upload your resume first!")
            return
        
        api_key = st.session_state.api_key if not st.session_state.demo_mode else None
        
        with st.spinner("✨ Generating your personalized cover letter..."):
            generator = CoverLetterGenerator(api_key=api_key)
            cover_letter = generator.generate(job, st.session_state.resume_data)
            
            st.markdown("### Your Cover Letter")
            st.text_area("", value=cover_letter, height=400, key="cover_letter_output")
            
            st.download_button(
                "📥 Download Cover Letter",
                cover_letter,
                file_name=f"cover_letter_{job.get('company', 'company').replace(' ', '_')}.txt",
                mime="text/plain"
            )
    
    if st.button("❌ Cancel", use_container_width=True):
        st.session_state.selected_job = None
        st.rerun()


def render_chat_section():
    """Render the AI recruiter chat section."""
    st.markdown("---")
    st.markdown("## 💬 Ask the AI Recruiter")
    st.markdown("Ask questions about your matches, get career advice, or explore opportunities.")
    
    # Chat input
    user_question = st.text_input(
        "Your question",
        placeholder="e.g., Why is the Data Scientist role a good match for me?",
        key="chat_input"
    )
    
    if st.button("🤖 Ask AI", use_container_width=True) and user_question:
        api_key = st.session_state.api_key if not st.session_state.demo_mode else None
        
        with st.spinner("Thinking..."):
            # Create context from current matches
            context = {}
            if st.session_state.matched_jobs:
                context["matched_jobs"] = [
                    {
                        "title": m.job.get("title"),
                        "company": m.job.get("company"),
                        "score": m.final_score
                    }
                    for m in st.session_state.matched_jobs[:5]
                ]
            
            assistant = RecruiterAssistant(
                api_key=api_key,
                query_engine=st.session_state.matching_engine.get_query_engine() if st.session_state.matching_engine else None
            )
            
            response = assistant.chat(user_question, context)
            
            # Add to chat history
            st.session_state.chat_history.append({
                "question": user_question,
                "answer": response
            })
    
    # Display chat history
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history[-5:]):
            with st.container():
                st.markdown(f"**You:** {chat['question']}")
                st.markdown(f"**AI:** {chat['answer']}")
                st.divider()


def run_matching():
    """Run the job matching process."""
    if not st.session_state.resume_data:
        return []
    
    # Load jobs - either from web or mock data
    if st.session_state.web_search_enabled:
        # Build search query from resume skills if not provided
        resume_skills = st.session_state.resume_data.get("skills", [])
        
        # Use manual query or build from resume skills
        if st.session_state.search_query:
            search_query = st.session_state.search_query
        elif resume_skills:
            # Use all resume skills as search query
            search_query = " ".join(resume_skills) + " jobs Remote"
            st.info(f"🔍 Searching jobs based on your skills: {', '.join(resume_skills)}")
        else:
            search_query = "Software Developer Remote"
        
        # Use web search
        with st.spinner(f"🌐 Searching jobs for: {search_query}"):
            try:
                searcher = WebJobSearch()
                job_listings = searcher.search_jobs(
                    search_query,
                    num_results=20,
                    resume_skills=resume_skills
                )
                jobs = [j.to_dict() for j in job_listings]
                
                if jobs:
                    st.success(f"✅ Found {len(jobs)} REAL jobs matching your skills!")
                else:
                    st.warning("⚠️ No real jobs found. Using mock data filtered by your skills.")
                    jobs = load_mock_jobs()
            except Exception as e:
                st.warning(f"⚠️ Web search error. Using mock data. ({str(e)[:50]})")
                jobs = load_mock_jobs()
    else:
        # Use mock data (demo mode)
        jobs = load_mock_jobs()
        st.info("📦 Using demo data. Enable '🌐 Search Real Jobs' for live results.")
    
    st.session_state.jobs = jobs
    
    # Create matching engine
    api_key = st.session_state.api_key if not st.session_state.demo_mode else None
    engine = MatchingEngine(api_key=api_key)
    
    # Index jobs
    engine.index_jobs(jobs)
    st.session_state.matching_engine = engine
    
    # Match resume
    matches = engine.match_resume(st.session_state.resume_data, top_k=20)
    st.session_state.matched_jobs = matches
    st.session_state.job_page = 0  # Reset pagination
    
    return matches


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render header
    render_header()
    
    # Run matching if resume is uploaded
    if st.session_state.resume_data and not st.session_state.matched_jobs:
        with st.spinner("🔍 Analyzing your resume and finding matches..."):
            run_matching()
    
    # Render metrics
    render_metrics(st.session_state.matched_jobs)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main content area
    if st.session_state.selected_job:
        render_cover_letter_generator()
    else:
        render_job_list(st.session_state.matched_jobs)
    
    # Chat section
    if st.session_state.matched_jobs:
        render_chat_section()


if __name__ == "__main__":
    main()
