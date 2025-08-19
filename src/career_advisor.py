import openai
from typing import Dict, List, Union
import logging
import json

logger = logging.getLogger(__name__)

class CareerAdvisor:
    def __init__(self, api_key: str = None):
        """
        Initialize with optional API key
        If no API key, uses free alternative approach
        """
        self.api_key = api_key
        if api_key:
            try:
                openai.api_key = api_key
                self.client = openai.OpenAI(api_key=api_key)
                self.has_openai = True
            except:
                self.has_openai = False
        else:
            self.has_openai = False
            
        logger.info(f"Career Advisor initialized. OpenAI: {self.has_openai}")

    def get_career_suggestions(self, resume_data: Dict) -> str:
        """Get AI career advice - uses OpenAI if available, else free alternative"""
        if self.has_openai:
            return self._get_openai_advice(resume_data)
        else:
            return self._get_free_advice(resume_data)

    def _get_openai_advice(self, resume_data: Dict) -> str:
        """Get advice using OpenAI GPT"""
        try:
            prompt = self._build_prompt(resume_data)
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI advice failed: {str(e)}")
            return self._get_free_advice(resume_data)

    def _get_free_advice(self, resume_data: Dict) -> str:
        """Free alternative using rule-based advice"""
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', '')
        
        # Rule-based career advice
        advice = []
        
        if any(skill in skills for skill in ['python', 'machine learning', 'data']):
            advice.extend([
                "🎯 **Career Path**: Data Scientist / ML Engineer",
                "📚 **Skills to Learn**: TensorFlow, PyTorch, AWS",
                "💡 **Certifications**: Google Data Analytics, AWS ML Specialty",
                "🚀 **Next Steps**: Build portfolio projects with real datasets"
            ])
        
        if any(skill in skills for skill in ['javascript', 'react', 'node']):
            advice.extend([
                "🎯 **Career Path**: Full-Stack Developer",
                "📚 **Skills to Learn**: React Native, GraphQL, Docker",
                "💡 **Certifications**: Google Cloud Associate, React Certification",
                "🚀 **Next Steps**: Contribute to open-source projects"
            ])
        
        if not advice:
            advice = [
                "🎯 **Career Path**: Based on your skills, consider technology roles",
                "📚 **Skills to Learn**: Python, Cloud Computing, Data Analysis",
                "💡 **Certifications**: Entry-level tech certifications",
                "🚀 **Next Steps**: Gain practical experience through projects"
            ]
        
        return "\n\n".join(advice)

    def _build_prompt(self, resume_data: Dict) -> str:
        """Build prompt for OpenAI"""
        skills = ", ".join(resume_data.get('skills', []))
        experience = resume_data.get('experience', 'Not specified')
        education = resume_data.get('education', 'Not specified')
        
        return f"""
        As a career advisor, analyze this resume and provide specific advice:

        Skills: {skills}
        Experience: {experience}
        Education: {education}

        Provide:
        1. 2-3 suitable career paths with explanations
        2. 2-3 skills to learn with resources
        3. Recommended certifications
        4. Actionable next steps

        Format with clear sections and emojis.
        """