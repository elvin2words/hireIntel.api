import json

import requests


def main():

    # Google Search Setup
    google_url = "https://google.serper.dev/search"
    keyword = ""
    payload = json.dumps({"q": keyword})
    headers = {
        'X-API-KEY': '4b2bd8d449f606e0f71f57875c46bbe14fd93def',
        'Content-Type': 'application/json'
    }

    # Execute Google search query
    try:
        response = requests.post(google_url, headers=headers, data=payload)
        response.raise_for_status()

        # Parse the response JSON
        data = response.json()

        # Extract links from response
        links = []
        if 'organic' in data:
            links.extend([item['link'] for item in data['organic']])
    except requests.RequestException as e:
        return