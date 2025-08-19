from job_matcher import JobMatcher
import os

def main():
    # Sample resume data - modify with your actual data
    resume_data = {
        'skills': ['Python', 'Data Analysis', 'SQL'],
        'experience': ['2 years as Data Analyst'],
        'education': 'BSc in Computer Science'
    }
    
    # Initialize matcher with absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_csv_path = os.path.join(current_dir, "data", "jobs.csv")
    
    try:
        print("Initializing JobMatcher...")
        matcher = JobMatcher(jobs_csv_path)
        
        print("\nFinding best matches...")
        matches = matcher.match(resume_data, top_n=5)
        
        if matches.empty:
            print("No matches found or error occurred")
        else:
            print("\n=== TOP 5 JOB MATCHES ===")
            print(matches[['title', 'company', 'match_score']].to_string(index=False))
            
            # Save full results
            output_path = os.path.join(current_dir, "result", "job_matches.csv")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            matcher.save_matches(matches, output_path)
            
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()