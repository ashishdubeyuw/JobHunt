"""
LangChain Agents Module
Recruiter Assistant and Cover Letter Generator
"""

import os
from typing import Optional, Dict, List

# LangChain imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️ LangChain not fully installed.")


class RecruiterAssistant:
    """
    AI-powered recruiter assistant that can answer questions about
    job matches and candidates using the LlamaIndex query engine.
    """
    
    def __init__(self, api_key: Optional[str] = None, query_engine=None):
        """
        Initialize the recruiter assistant.
        
        Args:
            api_key: Google API key for Gemini
            query_engine: LlamaIndex query engine for job data
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.query_engine = query_engine
        self.llm = None
        self.agent = None
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            self._setup_agent()
    
    def _setup_agent(self):
        """Set up the LangChain agent with tools."""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=self.api_key,
                temperature=0.7
            )
            
            tools = self._create_tools()
            
            # Create a simple conversational prompt
            prompt = PromptTemplate.from_template("""
You are a helpful AI recruiter assistant. You help analyze job matches and explain why certain jobs are good fits for candidates.

You have access to the following tools:
{tools}

Use them to answer questions about job matches.

Tool Names: {tool_names}

Question: {input}
{agent_scratchpad}

Provide a helpful, professional response.
""")
            
            if tools:
                self.agent = create_react_agent(self.llm, tools, prompt)
                
        except Exception as e:
            print(f"⚠️ Error setting up agent: {e}")
    
    def _create_tools(self) -> List:
        """Create tools for the agent."""
        tools = []
        
        if self.query_engine and LANGCHAIN_AVAILABLE:
            def query_jobs(query: str) -> str:
                """Query the job database."""
                try:
                    response = self.query_engine.query(query)
                    return str(response)
                except Exception as e:
                    return f"Error querying jobs: {e}"
            
            tools.append(Tool(
                name="query_jobs",
                func=query_jobs,
                description="Search and query job listings. Use this to find information about jobs, compare positions, or explain job requirements."
            ))
        
        return tools
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Chat with the recruiter assistant.
        
        Args:
            message: User's question or message
            context: Optional context about current matches
            
        Returns:
            Assistant's response
        """
        if not LANGCHAIN_AVAILABLE or not self.llm:
            return self._fallback_response(message, context)
        
        try:
            # If we have an agent, use it
            if self.agent:
                executor = AgentExecutor(
                    agent=self.agent, 
                    tools=self._create_tools(),
                    verbose=False,
                    handle_parsing_errors=True
                )
                result = executor.invoke({"input": message})
                return result.get("output", "I couldn't process that request.")
            
            # Otherwise, use direct LLM response
            return self._direct_llm_response(message, context)
            
        except Exception as e:
            print(f"⚠️ Chat error: {e}")
            return self._fallback_response(message, context)
    
    def _direct_llm_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Get direct LLM response without agent."""
        context_str = ""
        if context:
            if "matched_jobs" in context:
                jobs = context["matched_jobs"][:3]
                job_summaries = []
                for j in jobs:
                    job_summaries.append(f"- {j.get('title')} at {j.get('company')} (Score: {j.get('score', 'N/A')})")
                context_str = f"\n\nCurrent Top Matches:\n" + "\n".join(job_summaries)
        
        prompt = f"""You are a helpful AI recruiter assistant. 
{context_str}

User Question: {message}

Provide a helpful, professional response about job matching and career advice."""
        
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    def _fallback_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Provide fallback response when LLM is unavailable."""
        return ("I'm currently unable to provide AI-powered responses. "
                "Please check that your Google API key is configured correctly.")


class CoverLetterGenerator:
    """
    Generate tailored cover letters based on resume and job description.
    """
    
    COVER_LETTER_TEMPLATE = """
You are an expert career coach and professional writer. Generate a compelling, tailored cover letter.

## Job Details:
- Title: {job_title}
- Company: {company}
- Description: {job_description}
- Required Skills: {required_skills}

## Candidate Information:
- Skills: {candidate_skills}
- Experience: {experience_years} years
- Background: {candidate_summary}

## Instructions:
1. Write a professional cover letter (250-350 words)
2. Highlight relevant skills that match the job requirements
3. Show enthusiasm for the specific company and role
4. Include a strong opening and call to action
5. Use a professional but personable tone
6. Do NOT include placeholder brackets like [Your Name] - use "Candidate" if name unknown

Generate the cover letter now:
"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the cover letter generator.
        
        Args:
            api_key: Google API key for Gemini
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.llm = None
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=self.api_key,
                    temperature=0.7
                )
            except Exception as e:
                print(f"⚠️ Error initializing LLM: {e}")
    
    def generate(
        self,
        job: Dict,
        resume_data: Dict,
        tone: str = "professional"
    ) -> str:
        """
        Generate a tailored cover letter.
        
        Args:
            job: Job dictionary with title, company, description, etc.
            resume_data: Parsed resume data with skills, experience, etc.
            tone: Writing tone (professional, enthusiastic, formal)
            
        Returns:
            Generated cover letter text
        """
        if not LANGCHAIN_AVAILABLE or not self.llm:
            return self._fallback_cover_letter(job, resume_data)
        
        try:
            prompt = self.COVER_LETTER_TEMPLATE.format(
                job_title=job.get("title", "Position"),
                company=job.get("company", "the company"),
                job_description=job.get("description", "")[:1000],
                required_skills=", ".join(job.get("required_skills", [])),
                candidate_skills=", ".join(resume_data.get("skills", [])[:10]),
                experience_years=resume_data.get("experience_years", 0),
                candidate_summary=resume_data.get("summary", "Experienced professional")
            )
            
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"⚠️ Cover letter generation error: {e}")
            return self._fallback_cover_letter(job, resume_data)
    
    def _fallback_cover_letter(self, job: Dict, resume_data: Dict) -> str:
        """Generate a basic cover letter template when LLM is unavailable."""
        skills = ", ".join(resume_data.get("skills", [])[:5])
        return f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('title', 'position')} role at {job.get('company', 'your company')}.

With my background in {skills}, I am confident that I would be a valuable addition to your team.

[Please configure your Google API key to generate a personalized cover letter]

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to your team.

Best regards,
[Candidate]
"""


def create_recruiter_assistant(api_key: Optional[str] = None, query_engine=None) -> RecruiterAssistant:
    """Factory function to create a RecruiterAssistant."""
    return RecruiterAssistant(api_key=api_key, query_engine=query_engine)


def create_cover_letter_generator(api_key: Optional[str] = None) -> CoverLetterGenerator:
    """Factory function to create a CoverLetterGenerator."""
    return CoverLetterGenerator(api_key=api_key)
