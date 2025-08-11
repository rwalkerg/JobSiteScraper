import json
import requests
from bs4 import BeautifulSoup
import time
import traceback

# --- Configuration ---
# Selectors for Indeed.com. These MUST be changed for other sites.
LINK_SELECTOR = 'h2.jobTitle > a'
DESCRIPTION_SELECTOR = 'div#jobDescriptionText'
BASE_URL = "https://www.indeed.com"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
MAX_LINKS_TO_CHECK = 15 # Limit to avoid function timeouts

def get_links(url):
    """Gets all job links from the main search page."""
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.select(LINK_SELECTOR) if 'href' in a.attrs]
        full_links = [BASE_URL + link if link.startswith('/') else link for link in links]
        return list(set(full_links)) # Return unique links
    except Exception as e:
        print(f"ERROR fetching main URL: {e}")
        raise ValueError(f"Could not fetch or parse the search URL. Please check the link. Error: {e}")

def get_keywords_from_page(url, keywords):
    """Checks a single job page for a list of keywords."""
    try:
        time.sleep(0.5) # Be respectful to the server
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        description_area = soup.select_one(DESCRIPTION_SELECTOR)
        if not description_area:
            return None

        page_text = description_area.get_text().lower()
        found_keywords = [kw for kw in keywords if kw in page_text]
        
        if found_keywords:
            title = soup.title.string.replace('- Indeed.com', '').strip() if soup.title else 'Job Listing'
            return {'title': title, 'link': url, 'found_keywords': found_keywords}
        return None
    except Exception:
        # We can ignore errors on individual pages
        return None

def handler(event, context):
    """The main Netlify Function handler."""
    try:
        body = json.loads(event.get('body', '{}'))
        search_url = body.get('search_url')
        keywords = body.get('keywords', [])

        if not search_url or not keywords:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing search URL or keywords.'})}

        all_links = get_links(search_url)
        links_to_check = all_links[:MAX_LINKS_TO_CHECK]
        
        matched_jobs = []
        for link in links_to_check:
            job_details = get_keywords_from_page(link, keywords)
            if job_details:
                matched_jobs.append(job_details)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'matched_jobs': matched_jobs})
        }
    except Exception as e:
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
