from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from src.resume_parser import UltimateResumeParser
from src.job_matcher import JobMatcher
from src.career_advisor import CareerAdvisor
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-123')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI components
openai_key = os.getenv('OPENAI_API_KEY')
career_advisor = CareerAdvisor(openai_key)
job_matcher = JobMatcher()

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'txt'}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        resume_data = {}
        file_uploaded = False
        filepath = None
        
        # Handle file upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Save the file
                    file.save(filepath)
                    logger.info(f"Saved resume to: {filepath}")
                    
                    # Parse resume with better error handling
                    parser = UltimateResumeParser()
                    resume_data = parser.parse(filepath)
                    
                    # Clean up file
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(f"Could not remove file {filepath}: {e}")
                    
                    if 'error' in resume_data:
                        flash(f'Resume parsing error: {resume_data["error"]}', 'error')
                        return redirect(url_for('home'))
                    
                    file_uploaded = True
                    logger.info(f"Successfully parsed resume for: {resume_data.get('name', 'Unknown')}")
                    
                except Exception as e:
                    logger.error(f"Resume processing error: {str(e)}")
                    # Clean up file if it exists
                    try:
                        if filepath and os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not clean up file: {cleanup_error}")
                    
                    flash('Error processing resume file. Please try a different file or format.', 'error')
                    return redirect(url_for('home'))
        
        # Fallback to form data if no file was uploaded or parsing failed
        if not file_uploaded:
            skills = request.form.get('skills', '').strip()
            experience = request.form.get('experience', '').strip()
            education = request.form.get('education', '').strip()
            
            if not skills:
                flash('Please either upload a resume or enter your skills', 'error')
                return redirect(url_for('home'))
                
            resume_data = {
                'skills': [s.strip() for s in skills.split(',') if s.strip()],
                'experience': experience,
                'education': education,
                'name': 'Candidate',
                'email': ''
            }
            
            logger.info(f"Using manual input data: {resume_data}")
        
        # Get job matches and AI advice
        try:
            # AI Job Matching
            matches = job_matcher.match(resume_data)
            logger.info(f"Found {len(matches)} job matches")
            
            # AI Career Advice (only show for file uploads with sufficient data)
            ai_advice = None
            if file_uploaded and resume_data.get('skills'):
                try:
                    ai_advice = career_advisor.get_career_suggestions(resume_data)
                    logger.info("Successfully generated AI career advice")
                except Exception as e:
                    logger.error(f"AI advice generation failed: {str(e)}")
                    ai_advice = "Could not generate AI advice at this time."
            else:
                logger.info("Skipping AI advice for manual input")
            
            # Convert matches to list of dicts for template
            jobs_list = []
            for _, row in matches.iterrows():
                job = {
                    'title': row.get('title', 'N/A'),
                    'company': row.get('company', 'N/A'),
                    'location': row.get('location', 'N/A'),
                    'link': row.get('link', '#'),
                    'match_score': float(row.get('match_score', 0))
                }
                jobs_list.append(job)
            
            return render_template('result.html',
                               resume=resume_data,
                               jobs=jobs_list,
                               ai_advice=ai_advice)
                               
        except Exception as e:
            logger.error(f"Error in matching/advice generation: {str(e)}")
            flash('Error generating recommendations. Please try again.', 'error')
            return redirect(url_for('home'))
    
    # GET request - show the form
    return render_template('form.html')

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large. Please upload a file smaller than 16MB.', 'error')
    return redirect(url_for('home'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create data directory for jobs if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create a default jobs file if it doesn't exist
    default_jobs_path = 'data/jobs_clean.csv'
    if not os.path.exists(default_jobs_path):
        import pandas as pd
        default_jobs = pd.DataFrame({
            'title': ['Software Developer', 'Data Analyst', 'Web Developer'],
            'company': ['Tech Company', 'Data Corp', 'Web Solutions'],
            'location': ['Remote', 'New York, NY', 'San Francisco, CA'],
            'link': ['#', '#', '#']
        })
        default_jobs.to_csv(default_jobs_path, index=False)
        logger.info(f"Created default jobs file at {default_jobs_path}")
    
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)