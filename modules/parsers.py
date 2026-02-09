"""
Resume Parser Module
Extract text and structured information from PDF resumes
"""

import re
import io
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


class ResumeParser:
    """
    Parse PDF resumes and extract structured information.
    """
    
    # Common tech skills for matching
    COMMON_SKILLS = [
        # Programming Languages
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
        # Web Technologies
        "React", "Vue.js", "Angular", "Node.js", "Express", "Django", "Flask",
        "FastAPI", "Spring", "Next.js", "HTML", "CSS", "SASS", "GraphQL",
        # Data & ML
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras",
        "NLP", "Computer Vision", "Pandas", "NumPy", "Scikit-learn",
        # Cloud & DevOps
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "CI/CD", "Jenkins", "GitHub Actions", "Linux", "Bash",
        # Tools & Frameworks
        "Git", "Jira", "Agile", "Scrum", "REST API", "Microservices",
        "Kafka", "RabbitMQ", "Spark", "Hadoop", "Airflow", "dbt", "MLOps",
        # Soft Skills
        "Leadership", "Communication", "Problem Solving", "Team Management",
        "Project Management", "Agile Methodologies", "Product Management"
    ]
    
    # Patterns for experience extraction
    EXPERIENCE_PATTERNS = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)",
        r"experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|of|working)",
    ]
    
    def __init__(self):
        self.text = ""
        self.parsed_data = {}
    
    def parse_pdf(self, file_input) -> Dict:
        """
        Parse a PDF resume file.
        
        Args:
            file_input: File path (str/Path) or file-like object (BytesIO/uploaded file)
            
        Returns:
            Dictionary with extracted resume data
        """
        self.text = self._extract_text(file_input)
        
        self.parsed_data = {
            "raw_text": self.text,
            "skills": self.extract_skills(),
            "experience_years": self.extract_experience_years(),
            "email": self.extract_email(),
            "phone": self.extract_phone(),
            "education": self.extract_education(),
            "summary": self._generate_summary()
        }
        
        return self.parsed_data
    
    def _extract_text(self, file_input) -> str:
        """Extract text from PDF file."""
        try:
            if isinstance(file_input, (str, Path)):
                reader = PdfReader(str(file_input))
            else:
                # Handle file-like objects (Streamlit uploads)
                reader = PdfReader(file_input)
            
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            return "\n".join(text_parts)
        
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_skills(self, text: Optional[str] = None) -> List[str]:
        """
        Extract skills from resume text.
        
        Args:
            text: Optional text to parse (uses stored text if not provided)
            
        Returns:
            List of identified skills
        """
        text = text or self.text
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.COMMON_SKILLS:
            # Check for skill as whole word (case-insensitive)
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_experience_years(self, text: Optional[str] = None) -> int:
        """
        Estimate years of experience from resume text.
        
        Args:
            text: Optional text to parse
            
        Returns:
            Estimated years of experience (0 if not found)
        """
        text = text or self.text
        if not text:
            return 0
        
        text_lower = text.lower()
        
        # Try each pattern
        for pattern in self.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Return the maximum years found
                years = [int(m) for m in matches if m.isdigit()]
                if years:
                    return max(years)
        
        # Fallback: Count job entries with dates
        year_pattern = r'(20\d{2}|19\d{2})'
        years = re.findall(year_pattern, text)
        if len(years) >= 2:
            years = sorted([int(y) for y in years])
            experience = years[-1] - years[0]
            return min(experience, 30)  # Cap at 30 years
        
        return 0
    
    def extract_email(self, text: Optional[str] = None) -> Optional[str]:
        """Extract email address from resume."""
        text = text or self.text
        if not text:
            return None
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: Optional[str] = None) -> Optional[str]:
        """Extract phone number from resume."""
        text = text or self.text
        if not text:
            return None
        
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def extract_education(self, text: Optional[str] = None) -> List[str]:
        """Extract education information from resume."""
        text = text or self.text
        if not text:
            return []
        
        education_keywords = [
            r"(Bachelor'?s?|B\.?S\.?|B\.?A\.?)\s+(?:of|in)?\s*\w+",
            r"(Master'?s?|M\.?S\.?|M\.?A\.?|MBA)\s+(?:of|in)?\s*\w+",
            r"(Ph\.?D\.?|Doctorate)\s+(?:of|in)?\s*\w+",
            r"(Computer Science|Engineering|Data Science|Business|Mathematics)"
        ]
        
        found_education = []
        for pattern in education_keywords:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_education.extend(matches)
        
        return list(set(found_education))[:5]  # Limit to 5 entries
    
    def _generate_summary(self) -> str:
        """Generate a brief summary of the resume."""
        skills = self.parsed_data.get("skills", self.extract_skills())
        years = self.parsed_data.get("experience_years", self.extract_experience_years())
        
        skill_summary = ", ".join(skills[:5]) if skills else "various technologies"
        
        if years > 0:
            return f"Professional with {years}+ years of experience in {skill_summary}."
        else:
            return f"Professional with experience in {skill_summary}."
    
    def get_text_for_matching(self) -> str:
        """Get processed text suitable for semantic matching."""
        if not self.text:
            return ""
        
        # Return a condensed version for better matching
        skills_text = " ".join(self.parsed_data.get("skills", []))
        summary = self.parsed_data.get("summary", "")
        
        return f"{summary} Skills: {skills_text}. {self.text[:2000]}"


def parse_resume_file(file_path) -> Dict:
    """
    Convenience function to parse a resume file.
    
    Args:
        file_path: Path to PDF file or file-like object
        
    Returns:
        Parsed resume data dictionary
    """
    parser = ResumeParser()
    return parser.parse_pdf(file_path)
