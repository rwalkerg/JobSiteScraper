import json
import requests
from bs4 import BeautifulSoup
import time

# --- IMPORTANT: You may need to adjust these selectors for different job sites ---
# These are examples for Indeed.com
LINK_SELECTOR = 'a.jcs-JobTitle'
DESCRIPTION_SELECTOR = 'div#jobDescriptionText'
BASE_URL = "[https://www.indeed.com](https://www.indeed.com)" # Used to construct full URLs if links are relative
# ---

# User agent to mimic a real browser
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_job_links(url):
    """Fetches the main search page and extracts all job links."""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        link_elements = soup.select(LINK_SELECTOR)
        
        # Handle both relative and absolute links
        job_links = []
        for link in link_elements:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    job_links.append(BASE_URL + href)
                else:
                    job_links.append(href)
        
        return list(set(job_links)) # Return unique links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching main page {url}: {e}")
        raise ValueError(f"Could not fetch the job search URL. Please check the link. Error: {e}")


def check_page_for_keywords(url, keywords):
    """Visits a single job page and checks which keywords are present."""
    headers = {'User-Agent': USER_AGENT}
    try:
        # Add a small delay to be respectful to the server
        time.sleep(0.5)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        description_div = soup.select_one(DESCRIPTION_SELECTOR)
        if not description_div:
            return None, [] # Return if no description found

        page_text = description_div.get_text().lower()
        
        found_keywords = [kw for kw in keywords if kw in page_text]
        
        # Extract job title if possible
        title = soup.title.string if soup.title else url

        if found_keywords:
            return {'title': title, 'link': url, 'found_keywords': found_keywords}, found_keywords
        return None, []
        
    except Exception as e:
        print(f"Could not check page {url}. Reason: {e}")
        return None, []


def handler(event, context):
    """
    Netlify Function handler. Receives a URL and keywords, scrapes the site,
    and returns a list of matched jobs.
    """
    try:
        # --- 1. Get data from the frontend ---
        body = json.loads(event.get('body', '{}'))
        search_url = body.get('search_url')
        keywords = body.get('keywords', [])

        if not search_url or not keywords:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing search_url or keywords.'})
            }

        # --- 2. Scrape the main page for links ---
        # Netlify functions have a timeout (around 10-26s). We limit the number of links to process.
        all_links = get_job_links(search_url)
        links_to_process = all_links[:15] # Process a maximum of 15 links to avoid timeouts
        print(f"Found {len(all_links)} links, processing the first {len(links_to_process)}.")

        # --- 3. Visit each page and check for keywords ---
        matched_jobs = []
        for link in links_to_process:
            job_details, _ = check_page_for_keywords(link, keywords)
            if job_details:
                matched_jobs.append(job_details)
        
        print(f"Found {len(matched_jobs)} matching jobs.")

        # --- 4. Return the results to the frontend ---
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'matched_jobs': matched_jobs})
        }

    except ValueError as ve:
        # Handle specific, user-facing errors
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)})
        }
    except Exception as e:
        # Handle unexpected server errors
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'An internal server error occurred.'})
        }
