import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Create data directory
os.makedirs("data", exist_ok=True)

def scrape_linkedin_jobs():
    # LinkedIn requires authentication - use session with cookies
    session = requests.Session()
    
    # Set realistic headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    session.headers.update(headers)
    
    # LinkedIn job search URL (Python jobs)
    url = "https://www.linkedin.com/jobs/search/?keywords=python&location=United%20States"
    
    try:
        # First get the page to establish session
        response = session.get(url, timeout=15)
        print(f"Initial Status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"Initial request failed with {response.status_code}")
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selector patterns since LinkedIn changes their HTML frequently
        jobs = []
        
        # Pattern 1 (newer LinkedIn versions)
        jobs = soup.find_all('div', class_='base-card')
        if not jobs:
            # Pattern 2 (older versions)
            jobs = soup.find_all('li', class_='jobs-search-results__list-item')
        if not jobs:
            # Pattern 3 (alternative)
            jobs = soup.select('div.job-search-card')
        
        print(f"Found {len(jobs)} job containers")
        
        jobs_list = []
        for job in jobs[:15]:  # Limit to first 15 jobs
            try:
                # Try multiple extraction patterns
                title = job.find('h3', class_='base-search-card__title')
                if not title:
                    title = job.find('h3', class_='job-card-search__title')
                title = title.text.strip() if title else "N/A"
                
                company = job.find('h4', class_='base-search-card__subtitle')
                if not company:
                    company = job.find('a', class_='hidden-nested-link')
                company = company.text.strip() if company else "N/A"
                
                location = job.find('span', class_='job-search-card__location')
                if not location:
                    location = job.find('span', class_='job-card-search__location')
                location = location.text.strip() if location else "Remote"
                
                link = job.find('a', class_='base-card__full-link')
                if not link:
                    link = job.find('a', class_='job-card-search__link-wrapper')
                link = link['href'].split('?')[0] if link else "#"
                
                jobs_list.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'link': link,
                    'source': 'LinkedIn',
                    'date_scraped': pd.Timestamp.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Skipping job - extraction error: {e}")
                continue
                
        return jobs_list
        
    except Exception as e:
        print(f"Scraping failed: {e}")
        return []

# Run the scraper
jobs_data = scrape_linkedin_jobs()

if jobs_data:
    df = pd.DataFrame(jobs_data)
    df.to_csv('data/jobs.csv', index=False)
    print(f"Successfully saved {len(df)} jobs to data/jobs.csv")
    print("Sample of saved jobs:")
    print(df.head())
else:
    print("No jobs retrieved - trying alternative approach...")
    # Fallback to RemoteOK if LinkedIn fails
    def scrape_remoteok():
        try:
            url = "https://remoteok.com/api?tags=python"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            jobs = response.json()
            return [{
                'title': job.get('position', 'N/A'),
                'company': job.get('company', 'N/A'),
                'location': job.get('location', 'Remote'),
                'link': job.get('url', '#'),
                'source': 'RemoteOK',
                'date_scraped': pd.Timestamp.now().strftime('%Y-%m-%d')
            } for job in jobs if isinstance(jobs, list)]  # Ensure we got a list
        except:
            return []
    
    remote_jobs = scrape_remoteok()
    if remote_jobs:
        df = pd.DataFrame(remote_jobs)
        df.to_csv('data/jobs.csv', index=False)
        print(f"Saved {len(df)} remote jobs to data/jobs.csv")
        print(df.head())
    else:
        print("Failed to retrieve jobs from both LinkedIn and RemoteOK")
        # Create empty file to prevent errors
        pd.DataFrame(columns=['title','company','location','link','source','date_scraped']).to_csv('data/jobs.csv', index=False)


import pandas as pd

# Load the scraped data
df = pd.read_csv('data/jobs.csv')

# Clean and standardize the data
df['title'] = df['title'].str.lower().str.strip()
df['company'] = df['company'].str.lower().str.strip()
df['location'] = df['location'].str.lower().str.strip()

# Add additional features
df['is_remote'] = df['location'].str.contains('remote', case=False).astype(int)
df.to_csv('data/jobs_clean.csv', index=False)

# scraper.py
from flask import Flask
app = Flask(__name__)  # <-- Must be named 'app'

@app.route("/")
def home():
    return "Hello, World!"

if __name__ == "__main__":
    app.run()

# In s.py
import schedule
import time

def scheduled_scrape():
    print("Running scheduled job scrape...")
    jobs_data = scrape_linkedin_jobs()
    if jobs_data:
        df = pd.DataFrame(jobs_data)
        df.to_csv('data/jobs.csv', index=False)
        print(f"Saved {len(df)} jobs")

# Schedule to run daily at 8 AM
schedule.every().day.at("08:00").do(scheduled_scrape)

while True:
    schedule.run_pending()
    time.sleep(60)

def test_with_sample_resume():
    # Initialize parser
    parser = UltimateResumeParser()
    
    # Path to sample resume (make sure it's in your project directory)
    sample_resume_path = os.path.join(os.path.dirname(__file__), 'sample_resume.pdf')
    
    if os.path.exists(sample_resume_path):
        # Parse the sample resume
        resume_data = parser.parse(sample_resume_path)
        print("\n=== SAMPLE RESUME PARSING RESULTS ===")
        print(f"Name: {resume_data.get('name', 'N/A')}")
        print(f"Email: {resume_data.get('email', 'N/A')}")
        print("Skills:", ", ".join(resume_data.get('skills', [])))
        print("Experience:", resume_data.get('experience', 'N/A'))
        print("Education:", resume_data.get('education', 'N/A'))
        
        # Get job matches
        matcher = JobMatcher()
        jobs = matcher.match(resume_data)
        
        print("\n=== RECOMMENDED JOBS ===")
        print(jobs[['title', 'company', 'match_score']].head(5))
    else:
        print("Error: sample_resume.pdf not found in project directory")

# Add this to your main scraping function
if __name__ == "__main__":
    # Your existing scraping code
    scrape_linkedin_jobs()
    
    # Test with sample resume
    test_with_sample_resume()