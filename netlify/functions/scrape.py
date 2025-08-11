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
MAX_LINKS_TO_CHECK = 25 # Limit to avoid function timeouts
PAGES_TO_SCRAPE = 3 # How many pages of search results to scrape

def get_links(url):
    """
    Gets all job links from the first few pages of a search result.
    """
    all_links = []
    
    # Loop through the first N pages. For Indeed, each page is a 'start' parameter incremented by 10.
    for page in range(PAGES_TO_SCRAPE):
        start_index = page * 10
        
        # Correctly append the start parameter to the URL
        separator = '&' if '?' in url else '?'
        paginated_url = f"{url}{separator}start={start_index}"
        
        print(f"Scraping links from page {page + 1}: {paginated_url}")

        try:
            response = requests.get(paginated_url, headers={'User-Agent': USER_AGENT})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links_on_page = [a['href'] for a in soup.select(LINK_SELECTOR) if 'href' in a.attrs]
            full_links = [BASE_URL + link if link.startswith('/') else link for link in links_on_page]
            all_links.extend(full_links)
            
            # Small delay between page requests
            time.sleep(0.2)

        except Exception as e:
            print(f"Could not scrape page {page + 1}. Reason: {e}")
            # Continue to the next page even if one fails
            continue
            
    return list(set(all_links)) # Return unique links from all pages

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
        
        print(f"Found {len(all_links)} total links across {PAGES_TO_SCRAPE} pages. Checking the first {len(links_to_check)}.")

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
