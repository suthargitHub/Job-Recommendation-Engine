import os
import logging
from typing import Dict, List, Any
import re
import pdfplumber
import docx
import tempfile

logger = logging.getLogger(__name__)

class UltimateResumeParser:
    def __init__(self):
        logger.info("Resume Parser initialized successfully")

    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            # Extract text from file
            text = self._extract_text_from_file(file_path)
            
            if not text or not text.strip():
                return {"error": "Empty file or no text could be extracted"}
            
            # Parse the text
            result = self._parse_text(text)
            result["file"] = os.path.basename(file_path)
            result["text_length"] = len(text)
            
            logger.info(f"Successfully parsed resume: {result.get('name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            return {"error": f"Failed to process resume: {str(e)}"}

    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF, DOCX, or TXT files"""
        text = ""
        
        try:
            if file_path.lower().endswith('.pdf'):
                text = self._extract_from_pdf(file_path)
            elif file_path.lower().endswith('.docx'):
                text = self._extract_from_docx(file_path)
            else:
                text = self._extract_from_text(file_path)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            # Fallback: try reading as text file
            text = self._extract_from_text(file_path)
        
        return text

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx"""
        text = ""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            raise
        return text

    def _extract_from_text(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Text file reading failed: {e}")
            return ""

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse resume text to extract information using advanced regex"""
        # Clean the text
        text = self._clean_text(text)
        
        result = {
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "skills": self._extract_skills(text),
            "experience": self._extract_section(text, 'experience'),
            "education": self._extract_section(text, 'education'),
            "raw_text": text[:500] + "..." if len(text) > 500 else text  # Store first 500 chars for debugging
        }
        
        return result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize the text"""
        # Replace multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s@\.\-\+\(\)]', ' ', text)
        return text.strip()

    def _extract_name(self, text: str) -> str:
        """Extract name from resume text"""
        # Look for patterns like "John Doe" at the beginning
        name_patterns = [
            r'^([A-Z][a-z]+ [A-Z][a-z]+)',
            r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
            r'Name[:\s]*([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown"

    def _extract_email(self, text: str) -> str:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        phone_patterns = [
            r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        skills = set()
        
        # Common tech skills
        tech_skills = [
            'python', 'java', 'javascript', 'typescript', 'html', 'css', 
            'react', 'angular', 'vue', 'node', 'express', 'django', 'flask',
            'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'machine learning', 'data analysis',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'git', 'linux',
            'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'go', 'rust',
            'data science', 'ai', 'artificial intelligence', 'deep learning',
            'big data', 'hadoop', 'spark', 'tableau', 'power bi', 'excel'
        ]
        
        # Extract skills mentioned in the text
        for skill in tech_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text.lower()):
                skills.add(skill.title())
        
        # Extract from skills section
        skills_section = self._extract_section_text(text, 'skills')
        if skills_section:
            for skill in tech_skills:
                if skill in skills_section.lower():
                    skills.add(skill.title())
        
        # Extract capitalized tech terms
        capitalized_skills = re.findall(r'\b[A-Z][a-z]+\b', text)
        for word in capitalized_skills:
            if word.lower() in tech_skills:
                skills.add(word)
        
        return sorted(list(skills))

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract content from a specific section"""
        section_text = self._extract_section_text(text, section_name)
        if section_text:
            # Return first 200 characters of the section
            return section_text[:200] + "..." if len(section_text) > 200 else section_text
        return ""

    def _extract_section_text(self, text: str, section_name: str) -> str:
        """Extract text from a specific section using multiple patterns"""
        patterns = [
            rf'(?i){section_name}[:\s]*(.*?)(?=\n\s*\n|\n[A-Z]|\n\w+:|$)',
            rf'(?i){section_name}[:\s]*(.*?)(?=\n[A-Z][a-z]+\s*:|$)',
            rf'(?i){section_name}\s*\\n(.*?)(?=\\n\\n|\\n[A-Z]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""

# Test function
def test_parser():
    """Test the parser with sample text"""
    parser = UltimateResumeParser()
    
    # Sample resume text matching your PDF content
    sample_text = """
    John Doe

    Data Scientist | john.doe@example.com | (123) 456-7890

    SKILLS: Python, Machine Learning, SQL

    EXPERIENCE: Data Scientist at ABC Corp (2020-Present)

    EDUCATION: BSc Computer Science, XYZ University
    """
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_file = f.name
    
    try:
        result = parser.parse(temp_file)
        print("Test parsing result:")
        print(f"Name: {result.get('name')}")
        print(f"Email: {result.get('email')}")
        print(f"Skills: {result.get('skills')}")
        print(f"Experience: {result.get('experience')}")
        print(f"Education: {result.get('education')}")
    finally:
        os.unlink(temp_file)

if __name__ == "__main__":
    test_parser()