from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
import logging
from typing import Dict 

logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self, jobs_data_path="data/jobs_clean.csv"):
        try:
            # Load data
            self.jobs_df = pd.read_csv(jobs_data_path)
            logger.info(f"Loaded {len(self.jobs_df)} jobs")
            
            # Initialize AI model (FREE)
            self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Precompute job embeddings
            job_texts = (
                self.jobs_df['title'] + " " +
                self.jobs_df['company'] + " " +
                self.jobs_df['location']
            ).tolist()
            
            self.job_embeddings = self.sbert_model.encode(job_texts)
            
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise ValueError(f"Failed to initialize JobMatcher: {str(e)}")

    def match(self, resume_data: Dict, top_n: int = 5) -> pd.DataFrame:
        """AI-powered matching using semantic similarity"""
        try:
            # Prepare resume text
            resume_text = self._prepare_resume_text(resume_data)
            
            # AI semantic matching
            resume_embedding = self.sbert_model.encode([resume_text])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(resume_embedding, self.job_embeddings)[0]
            
            # Add scores to dataframe
            self.jobs_df['match_score'] = similarities
            
            # Get top matches
            results = self.jobs_df.sort_values('match_score', ascending=False).head(top_n)
            
            logger.info(f"AI matching completed. Top score: {results['match_score'].max():.2f}")
            return results[['title', 'company', 'location', 'link', 'match_score']]
            
        except Exception as e:
            logger.error(f"Matching error: {str(e)}")
            return pd.DataFrame()

    def _prepare_resume_text(self, resume_data: Dict) -> str:
        """Combine resume data for AI processing"""
        skills_text = " ".join(resume_data.get('skills', []))
        experience = resume_data.get('experience', '')
        education = resume_data.get('education', '')
        
        return f"{skills_text} {experience} {education}".strip()