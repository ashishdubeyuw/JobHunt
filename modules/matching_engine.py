"""
Hybrid Matching Engine
Combines LlamaIndex semantic search with algorithmic scoring
"""

import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# LlamaIndex imports
try:
    from llama_index.core import VectorStoreIndex, Document, Settings
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.gemini import GeminiEmbedding
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    print("⚠️ LlamaIndex not fully installed. Using basic matching.")


@dataclass
class MatchResult:
    """Result of job matching with scores."""
    job: Dict
    final_score: float
    skills_score: float
    experience_score: float
    semantic_score: float
    explanation: str


class MatchingEngine:
    """
    Hybrid matching engine combining:
    - Semantic similarity (LlamaIndex vector search) - 20%
    - Skills matching (keyword overlap) - 50%
    - Experience matching (years comparison) - 30%
    """
    
    # Scoring weights
    SKILLS_WEIGHT = 0.50
    EXPERIENCE_WEIGHT = 0.30
    SEMANTIC_WEIGHT = 0.20
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the matching engine.
        
        Args:
            api_key: Google API key for Gemini (uses env var if not provided)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.index = None
        self.jobs = []
        self.job_documents = []
        
        if LLAMA_INDEX_AVAILABLE and self.api_key:
            self._configure_llm()
    
    def _configure_llm(self):
        """Configure LlamaIndex with Gemini."""
        try:
            # Set up Gemini as the LLM and embedding model
            Settings.llm = Gemini(
                model="models/gemini-2.0-flash",
                api_key=self.api_key
            )
            Settings.embed_model = GeminiEmbedding(
                model_name="models/text-embedding-004",
                api_key=self.api_key
            )
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 100
        except Exception as e:
            print(f"⚠️ Error configuring Gemini: {e}")
    
    def index_jobs(self, jobs: List[Dict]) -> bool:
        """
        Create a vector index from job descriptions.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            True if indexing successful
        """
        self.jobs = jobs
        
        if not LLAMA_INDEX_AVAILABLE or not self.api_key:
            print("⚠️ Semantic search unavailable. Using keyword matching only.")
            return False
        
        try:
            # Create documents from jobs
            self.job_documents = []
            for job in jobs:
                doc_text = self._job_to_text(job)
                doc = Document(
                    text=doc_text,
                    metadata={
                        "job_id": job.get("id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", "")
                    }
                )
                self.job_documents.append(doc)
            
            # Build vector index
            self.index = VectorStoreIndex.from_documents(self.job_documents)
            print(f"✅ Indexed {len(jobs)} jobs for semantic search")
            return True
            
        except Exception as e:
            print(f"⚠️ Error creating index: {e}")
            return False
    
    def _job_to_text(self, job: Dict) -> str:
        """Convert job dictionary to searchable text."""
        parts = [
            f"Job Title: {job.get('title', '')}",
            f"Company: {job.get('company', '')}",
            f"Location: {job.get('location', '')}",
            f"Description: {job.get('description', '')}",
            f"Required Skills: {', '.join(job.get('required_skills', []))}",
            f"Experience Required: {job.get('experience_years', 0)} years",
            f"Salary: {job.get('salary', 'Not specified')}"
        ]
        return "\n".join(parts)
    
    def match_resume(
        self, 
        resume_data: Dict, 
        top_k: int = 10
    ) -> List[MatchResult]:
        """
        Match a resume against indexed jobs.
        
        Args:
            resume_data: Parsed resume dictionary with skills, experience, text
            top_k: Number of top matches to return
            
        Returns:
            List of MatchResult objects sorted by final score
        """
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))
        resume_years = resume_data.get("experience_years", 0)
        resume_text = resume_data.get("raw_text", "") or resume_data.get("summary", "")
        
        results = []
        semantic_scores = {}
        
        # Get semantic similarity scores if index is available
        if self.index and resume_text:
            semantic_scores = self._get_semantic_scores(resume_text, top_k * 2)
        
        for job in self.jobs:
            job_id = job.get("id", "")
            
            # Calculate skills match (50%)
            skills_score = self._calculate_skills_score(resume_skills, job)
            
            # Calculate experience match (30%)
            experience_score = self._calculate_experience_score(resume_years, job)
            
            # Get semantic score (20%)
            semantic_score = semantic_scores.get(job_id, 0.5)  # Default 0.5 if unavailable
            
            # Calculate weighted final score
            final_score = (
                skills_score * self.SKILLS_WEIGHT +
                experience_score * self.EXPERIENCE_WEIGHT +
                semantic_score * self.SEMANTIC_WEIGHT
            )
            
            # Generate explanation
            explanation = self._generate_match_explanation(
                job, skills_score, experience_score, semantic_score, resume_skills
            )
            
            results.append(MatchResult(
                job=job,
                final_score=final_score,
                skills_score=skills_score,
                experience_score=experience_score,
                semantic_score=semantic_score,
                explanation=explanation
            ))
        
        # Sort by final score (highest first)
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        return results[:top_k]
    
    def _calculate_skills_score(self, resume_skills: set, job: Dict) -> float:
        """
        Calculate skills match score (0.0 to 1.0).
        """
        job_skills = set(s.lower() for s in job.get("required_skills", []))
        
        if not job_skills:
            return 0.5  # Neutral score if no skills specified
        
        # Check job description for additional skills
        job_desc = job.get("description", "").lower()
        
        matching_skills = 0
        for skill in job_skills:
            if skill in resume_skills or skill in job_desc:
                for rs in resume_skills:
                    if skill in rs or rs in skill:
                        matching_skills += 1
                        break
        
        # Direct intersection
        direct_matches = len(resume_skills.intersection(job_skills))
        matching_skills = max(matching_skills, direct_matches)
        
        return min(matching_skills / len(job_skills), 1.0)
    
    def _calculate_experience_score(self, resume_years: int, job: Dict) -> float:
        """
        Calculate experience match score (0.0 to 1.0).
        """
        required_years = job.get("experience_years", 0)
        
        if required_years == 0:
            return 0.8  # Good score if no requirement specified
        
        if resume_years >= required_years:
            # Meeting or exceeding requirements
            return 1.0
        elif resume_years >= required_years * 0.75:
            # Close to requirements (within 25%)
            return 0.8
        elif resume_years >= required_years * 0.5:
            # Half the requirements
            return 0.5
        else:
            # Less than half
            return max(0.2, resume_years / required_years)
    
    def _get_semantic_scores(self, resume_text: str, top_k: int) -> Dict[str, float]:
        """
        Get semantic similarity scores using vector search.
        """
        scores = {}
        
        try:
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=top_k
            )
            
            nodes = retriever.retrieve(resume_text[:2000])  # Limit query length
            
            # Normalize scores to 0-1 range
            if nodes:
                max_score = max(node.score for node in nodes) if nodes else 1.0
                for node in nodes:
                    job_id = node.metadata.get("job_id", "")
                    if job_id:
                        normalized = (node.score / max_score) if max_score > 0 else 0
                        scores[job_id] = normalized
        
        except Exception as e:
            print(f"⚠️ Semantic search error: {e}")
        
        return scores
    
    def _generate_match_explanation(
        self,
        job: Dict,
        skills_score: float,
        experience_score: float,
        semantic_score: float,
        resume_skills: set
    ) -> str:
        """Generate human-readable match explanation."""
        job_skills = set(s.lower() for s in job.get("required_skills", []))
        matched_skills = resume_skills.intersection(job_skills)
        missing_skills = job_skills - resume_skills
        
        parts = []
        
        # Overall assessment
        final = skills_score * 0.5 + experience_score * 0.3 + semantic_score * 0.2
        if final >= 0.8:
            parts.append("🎯 **Excellent Match!**")
        elif final >= 0.6:
            parts.append("✅ **Good Match**")
        elif final >= 0.4:
            parts.append("⚠️ **Partial Match**")
        else:
            parts.append("❌ **Low Match**")
        
        # Skills breakdown
        if matched_skills:
            parts.append(f"**Matching Skills:** {', '.join(s.title() for s in list(matched_skills)[:5])}")
        
        if missing_skills:
            parts.append(f"**Skills to Develop:** {', '.join(s.title() for s in list(missing_skills)[:3])}")
        
        # Experience
        required = job.get("experience_years", 0)
        if experience_score >= 0.8:
            parts.append(f"**Experience:** Meets {required}+ year requirement ✓")
        else:
            parts.append(f"**Experience:** May need more experience (requires {required}+ years)")
        
        return "\n".join(parts)
    
    def get_query_engine(self):
        """
        Get LlamaIndex query engine for conversational queries.
        Returns None if index not available.
        """
        if not self.index:
            return None
        
        try:
            return self.index.as_query_engine()
        except Exception as e:
            print(f"⚠️ Error creating query engine: {e}")
            return None


def create_matching_engine(api_key: Optional[str] = None) -> MatchingEngine:
    """
    Factory function to create a matching engine.
    
    Args:
        api_key: Optional Google API key
        
    Returns:
        Configured MatchingEngine instance
    """
    return MatchingEngine(api_key=api_key)
