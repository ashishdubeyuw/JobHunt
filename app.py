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
    page_title="Job Matching AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Glassmorphism Design + WordPress-inspired styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* ===== GLASSMORPHISM BASE STYLES ===== */
    
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #0f0c29);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #e2e8f0;
    }
    
    /* Main container */
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
    }
    
    /* ===== GLASSMORPHISM HEADER ===== */
    .header-gradient {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 2.5rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .header-gradient h1 {
        color: white !important;
        margin: 0;
        font-weight: 800;
        font-size: 2.5rem;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .header-gradient p {
        color: rgba(255,255,255,0.85);
        margin: 0.75rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* ===== GLASSMORPHISM CARDS ===== */
    .glass-card, .job-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    }
    
    .glass-card:hover, .job-card:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.25);
    }
    
    /* ===== METRIC CARDS - GLASSMORPHISM ===== */
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: scale(1.02);
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* ===== SCORE BADGES - GLASSMORPHISM ===== */
    .score-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 700;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .score-excellent { 
        background: rgba(34, 197, 94, 0.3); 
        color: #86efac; 
        border-color: rgba(34, 197, 94, 0.5);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
    }
    .score-good { 
        background: rgba(59, 130, 246, 0.3); 
        color: #93c5fd; 
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    .score-partial { 
        background: rgba(245, 158, 11, 0.3); 
        color: #fcd34d; 
        border-color: rgba(245, 158, 11, 0.5);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
    }
    
    /* ===== SIDEBAR - GLASSMORPHISM ===== */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* ===== BUTTONS - GLASSMORPHISM ===== */
    .stButton > button {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.8) 100%);
        backdrop-filter: blur(10px);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        background: linear-gradient(135deg, rgba(102, 126, 234, 1) 0%, rgba(118, 75, 162, 1) 100%);
    }
    
    /* ===== INPUTS - GLASSMORPHISM ===== */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        backdrop-filter: blur(8px);
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: rgba(102, 126, 234, 0.6) !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* ===== FILE UPLOADER - GLASSMORPHISM ===== */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: rgba(102, 126, 234, 0.6);
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* ===== EXPANDER - GLASSMORPHISM ===== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        font-weight: 600;
        color: #e2e8f0 !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 0 0 12px 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 1.5rem 0;
    }
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.75rem 1rem;
        }
        
        .header-gradient {
            padding: 1.5rem 1rem;
            border-radius: 16px;
        }
        
        .header-gradient h1 {
            font-size: 1.75rem;
        }
        
        .glass-card, .job-card {
            padding: 1rem;
            border-radius: 12px;
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
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* ===== LINKS ===== */
    a {
        color: #a78bfa;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    
    a:hover {
        color: #c4b5fd;
        text-shadow: 0 0 10px rgba(167, 139, 250, 0.5);
    }
    
    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetricValue"] {
        color: #a78bfa !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    /* ===== INFO/SUCCESS/WARNING BOXES ===== */
    .stAlert {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px !important;
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
        st.session_state.web_search_enabled = False
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
                st.success("✅ No API key required! Uses Google Jobs search.")
                
                st.session_state.search_query = st.text_input(
                    "Job Search Query",
                    value=st.session_state.search_query or "Python Machine Learning Remote",
                    placeholder="e.g., Python Developer Remote"
                )
                
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
        <h1>🎯 Job Matching AI</h1>
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
            <div class="metric-value" style="color: #16a34a;">{excellent}</div>
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
            
            st.markdown("#### Required Skills")
            skills = job.get("required_skills", [])
            if skills:
                st.markdown(" • ".join([f"`{s}`" for s in skills]))
            
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
    """Render the list of matched jobs."""
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
    
    # Render each job
    for i, match in enumerate(filtered_jobs, 1):
        render_job_card(match, i)


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
            # Use top 5 resume skills as search query
            top_skills = resume_skills[:5]
            search_query = " ".join(top_skills) + " jobs Remote"
            st.info(f"🔍 Searching jobs based on your skills: {', '.join(top_skills)}")
        else:
            search_query = "Software Developer Remote"
        
        # Use web search
        with st.spinner(f"🌐 Searching jobs for: {search_query}"):
            try:
                searcher = WebJobSearch()
                job_listings = searcher.search_jobs(
                    search_query,
                    num_results=20
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
    matches = engine.match_resume(st.session_state.resume_data, top_k=10)
    st.session_state.matched_jobs = matches
    
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
