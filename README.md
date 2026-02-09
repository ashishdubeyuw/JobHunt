# Job Matching & Resume Analysis Application

🎯 An AI-powered job matching platform that uses LlamaIndex (Vector Search/RAG), LangChain (Agentic Workflow), and Google Gemini 2.5 Flash to help you find your perfect job match.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **📄 Resume Parsing**: Upload your PDF resume and extract skills, experience, and contact info
- **🔍 Hybrid Matching Engine**: 
  - 50% Skills matching (keyword analysis)
  - 30% Experience matching (years comparison)
  - 20% Semantic similarity (LlamaIndex vector search)
- **🤖 AI-Powered Insights**: Ask questions about your job matches using natural language
- **✉️ Cover Letter Generator**: Auto-generate tailored cover letters for any job
- **⏰ Scheduled Search**: Set up daily/weekly job searches with email/WhatsApp notifications
- **📱 Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/JobMatchingApp.git
cd JobMatchingApp
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required:**
- `GOOGLE_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional (for notifications):**
- `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`: For email notifications
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`: For WhatsApp notifications

### 5. Run the Application

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

## 🎮 Demo Mode

No API key? No problem! Enable **Demo Mode** in the sidebar to:
- Use mock job data
- Test skill matching and scoring
- See the full UI without AI features

## 📱 Mobile Testing

The app is fully responsive. To test on mobile:

1. Run the app with network access:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```

2. Find your local IP:
   ```bash
   ifconfig | grep "inet "  # Mac/Linux
   ipconfig                  # Windows
   ```

3. Open `http://YOUR_IP:8501` on your phone/tablet

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/test_app.py -v

# Run specific test class
pytest tests/test_app.py::TestMatchingEngine -v

# Run with coverage
pip install pytest-cov
pytest tests/test_app.py --cov=modules --cov-report=html
```

## 📁 Project Structure

```
JobMatchingApp/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # This file
│
├── modules/
│   ├── __init__.py           # Module exports
│   ├── scrapers.py           # Job scraping / data fetching
│   ├── parsers.py            # Resume PDF parsing
│   ├── matching_engine.py    # Hybrid matching (LlamaIndex + scoring)
│   ├── agents.py             # LangChain agents and chains
│   ├── scheduler.py          # Scheduled job search automation
│   └── notifications.py      # WhatsApp/Gmail notification handlers
│
├── data/
│   ├── mock_jobs.json        # Mock job data for development
│   └── user_profiles.json    # User preferences & schedules
│
└── tests/
    └── test_app.py           # Test suite
```

## 🔧 Configuration

### API Keys

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini 2.5 Flash for LLM features |
| `SCRAPINGDOG_API_KEY` | No | For real job scraping |
| `GMAIL_ADDRESS` | No | For email notifications |
| `GMAIL_APP_PASSWORD` | No | Gmail App Password |
| `TWILIO_ACCOUNT_SID` | No | For WhatsApp notifications |
| `TWILIO_AUTH_TOKEN` | No | Twilio authentication |

*Not required if using Demo Mode

### Getting a Gmail App Password

1. Go to [Google Account](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail" on "Other (Custom name)"
4. Use this password in `.env`

## 📊 Matching Algorithm

The hybrid matching score is calculated as:

```
Final Score = (Skills × 0.50) + (Experience × 0.30) + (Semantic × 0.20)
```

- **Skills (50%)**: Keyword overlap between resume and job requirements
- **Experience (30%)**: Comparison of years vs. job requirements
- **Semantic (20%)**: LlamaIndex vector similarity for contextual matching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LlamaIndex](https://www.llamaindex.ai/) for vector search and RAG
- [LangChain](https://www.langchain.com/) for agentic workflows
- [Google Gemini](https://ai.google.dev/) for LLM capabilities
- [Streamlit](https://streamlit.io/) for the beautiful UI framework
