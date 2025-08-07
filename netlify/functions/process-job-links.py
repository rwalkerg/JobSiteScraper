import requests
from bs4 import BeautifulSoup
from netlify_python_blobs import NetlifyBlobs
import os
import json
import time

# --- START: YOU MUST CUSTOMIZE THIS SECTION ---
KEYWORDS = ['python', 'django', 'fastapi', 'aws', 'remote']
USER_AGENT = 'Your Name/Email - Job Scraper Bot'
BATCH_SIZE = 5 # How many links to process per run to avoid timeouts
# --- END: CUSTOMIZATION SECTION ---

def check_page_for_keywords(url, keywords):
    """Visits a single job page and checks for keywords."""
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- IMPORTANT: This selector must match the job description container on the site. ---
        # --- Example for Indeed: 'div#jobDescriptionText' ---
        description_div = soup.select_one('div#jobDescriptionText')
        if not description_div:
            return False

        page_text = description_div.get_text().lower()
        return any(keyword in page_text for keyword in keywords)
    except Exception as e:
        print(f"Could not check page {url}. Reason: {e}")
        return False

def handler(event, context):
    """
    Netlify Function handler. Processes a batch of links from the blob store.
    """
    print("Running 'process-job-links' function...")

    blobs = NetlifyBlobs(
        site_id=os.environ['SITE_ID'], 
        api_token=os.environ['NETLIFY_API_TOKEN'], 
        store_name='job_links_store'
    )
    
    # 1. Get the list of links from storage
    links_to_process = blobs.get_json('links_to_process', default=[])
    
    if not links_to_process:
        print("No links to process. All jobs checked.")
        return {'statusCode': 200, 'body': 'No links left.'}

    print(f"{len(links_to_process)} links remaining.")
    
    # 2. Take a small batch to process now
    batch = links_to_process[:BATCH_SIZE]
    remaining_links = links_to_process[BATCH_SIZE:]
    
    # 3. Process the batch
    for link in batch:
        print(f"Checking: {link}")
        if check_page_for_keywords(link, KEYWORDS):
            # A MATCH IS FOUND!
            # The print statement will show up in your Netlify function logs.
            print(f"✅ MATCH FOUND: {link}")
        time.sleep(1) # Be polite to the server
        
    # 4. Save the remaining links back to storage
    blobs.set_json('links_to_process', remaining_links)
    
    print(f"Batch complete. {len(remaining_links)} links left to process.")
    return {'statusCode': 200, 'body': f'Processed {len(batch)} links.'}
