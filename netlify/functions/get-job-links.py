import requests
from bs4 import BeautifulSoup
from netlify_python_blobs import NetlifyBlobs
import os
import json

# --- START: YOU MUST CUSTOMIZE THIS SECTION ---
SEARCH_URL = 'https://careers.regeneron.com/en/jobs/?keyword=&country=United+States+of+America&pagesize=100#results' # The URL of your job search
USER_AGENT = 'George Jefferson - Moving on up bot' # Be a good citizen, identify your bot
# --- END: CUSTOMIZATION SECTION ---

def handler(event, context):
    """
    Netlify Function handler. Fetches job links and saves them to Netlify Blobs.
    """
    print("Running 'get-job-links' function...")

    try:
        # 1. Fetch the main search page
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(SEARCH_URL, headers=headers)
        response.raise_for_status()

        # 2. Parse the HTML and find all job links
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- IMPORTANT: This selector depends entirely on the website's HTML. ---
        # --- You MUST inspect the site and find the correct selector for the links. ---
        # --- Example for Indeed: 'a.jcs-JobTitle' ---
        link_elements = soup.select('a.jcs-JobTitle')
        
        # Construct full, unique URLs
        base_url = "https://www.indeed.com"
        job_links = list(set([base_url + link['href'] for link in link_elements if 'href' in link.attrs]))

        if not job_links:
            print("No job links found. Check your URL and HTML selector.")
            return {'statusCode': 200, 'body': 'No links found.'}

        print(f"Found {len(job_links)} unique job links.")

        # 3. Save the list of links to Netlify Blobs
        # The store name 'job_links_store' is defined by you
        blobs = NetlifyBlobs(
            site_id=os.environ['SITE_ID'], 
            api_token=os.environ['NETLIFY_API_TOKEN'], 
            store_name='job_links_store'
        )
        
        # We store the list as a JSON string under the key 'links_to_process'
        blobs.set_json('links_to_process', job_links)
        
        print("Successfully saved links to Netlify Blobs store.")
        return {'statusCode': 200, 'body': f'Saved {len(job_links)} links.'}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'statusCode': 500, 'body': f'Error: {e}'}
