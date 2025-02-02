import requests
from bs4 import BeautifulSoup
import time
import re
from difflib import get_close_matches
from fake_user_agent import user_agent
from urllib.parse import urlparse, urljoin
import json
import os
import asyncio
import nest_asyncio
import aiohttp
# use: ua = user_agent(browser="chrome", use_cache=False)

session = requests.Session()
"""
scrapes the items and shop page of a website
basically the main function to use this file
Parameters:
    urls (list of str): list of urls closest to first of a specific month
"""
def scrape_items(url, timestp, divs, tile_names, non_wb_url, keywords):
    info = []
    pages = scan_pages(url, non_wb_url, keywords) # pages is a list of urls that lead to the
                                # items were collecting
    print("done scanning pages")
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    info = loop.run_until_complete(scrape_pages_async(pages, timestp, url, divs, tile_names))

    print("done gathering info")
    return info

# function to fetch or load HTML and return BeautifulSoup object
# allows us to save html requests and use them later
# rather than putting in a new request each time
async def get_html_soup_async(url, headers, session):
    folder = "html_requests_wbscraper"
    filename = sanitize_filename(url) + ".html"

    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    # Check if file already exists, load it if it does
    if os.path.exists(filepath):
        print(f"Loading HTML from file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as file:
            html_content = file.read()
    else:
        print(f"Fetching HTML from URL: {url}")
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    # Save the fetched HTML
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(html_content)
                    print(f"HTML saved to: {filepath}")
                    time.sleep(2)
                else:
                    print(f"Error: Response code {response.status}")
                    return None
        except aiohttp.ClientConnectionError as e:
            print(e)
            print("Retrying...")
            await asyncio.sleep(5)
            return await get_html_soup_async(url, headers, session)

    # Create and return a BeautifulSoup object
    return BeautifulSoup(html_content, "html.parser")


def get_html_soup(url, headers):
    folder = "html_requests_wbscraper"
    filename = sanitize_filename(url) + ".html"

    # create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    # check if file already exists, load it if it does
    if os.path.exists(filepath):
        print(f"Loading HTML from file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as file:
            html_content = file.read()
    else:
        print(f"Fetching HTML from URL: {url}")
        try:
            #session = requests.Session()
            session.headers.update(headers)
            response = session.get(url)
            #print(response.headers)
            print(response.status_code)
            if response.status_code == 200:
                html_content = response.text
                # Save the fetched HTML
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(html_content)
                print(f"HTML saved to: {filepath}")
                time.sleep(2)
            else:
                print("an error occurred with response code: " + str(response.status_code))
                return None
        except ConnectionRefusedError as e:
            print(e)
            print("trying again...")
            time.sleep(5)
            return get_html_soup(url, headers)
        except requests.exceptions.ConnectionError as e:
            print(e)
            print("trying again...")
            time.sleep(5)
            return get_html_soup(url, headers)

    # Create and return a BeautifulSoup object
    return BeautifulSoup(html_content, "html.parser")


def sanitize_filename(url):
    # Replace invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', url)


def filter_links(links, base_url, url):
    # Step 1: remove non-absolute urls and irrelevant ones
    normalized_links = [link for link in links if (base_url in link and "web.archive.org" in link)]

    # Step 2: Remove exact duplicates
    unique_links = list(set(normalized_links))

    # Step 3: Sort links by length (shortest first)
    unique_links.sort(key=len)

    # Step 4: Filter out links that are sub-links of others
    filtered_links = []
    for link in unique_links:
        # Add link if it's not a sub-link of an already added link
        if not any(link.startswith(existing_link) and link != existing_link for existing_link in filtered_links):
            filtered_links.append(link)

    return filtered_links

# find the website pages we want to webscrape
# returns a 2d list
def scan_pages(url, non_wb_url, keywords):
    urls_pages = [] # a list organized of all the urls found on the homepage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://reddit.com/",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    pages_for_url = scan_page(url, headers, non_wb_url, keywords) # returns a list of links found on the page
    if len(pages_for_url) == 0:
        print("an error occurred with url " + url + " it will not be used, see stat code above")
    else:
        urls_pages = pages_for_url # add links found on url to the 2d list

    return urls_pages
def scan_page(url, headers, non_wb_url, keywords):
    try:
        soup = get_html_soup(url, headers)

        # find all links on the page
        links = soup.find_all("a", href=True)
        matching_links = []

        for link in links:
            href = link.get("href")
            if any(keyword.lower() in href.lower() for keyword in keywords) and "http" in href and "stg" not in href:
                matching_links.append(href)

        matching_links = filter_links(matching_links, non_wb_url, url)

        for i in matching_links:
            print(i)
            # on connection errors, try again since these errors are due to to many requests
    except ConnectionRefusedError as e:
        print(e)
        print("trying again...")
        time.sleep(5)
        matching_links = scan_page(url, headers, non_wb_url)
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("trying again...")
        time.sleep(5)
        matching_links = scan_page(url, headers, non_wb_url)

    return matching_links

"""
uses given page urls to get item data using beautiful soup

Parameters:
    pages (2d list): list of page urls from the home website

Returns:
    products (2d list): a list of product information

"""
def scrape_info(parent_element, class_names): # class_names can either be 1d or 2d list
    info = {} # dict of info were collecting
    # extract name and type of product
    for names in class_names:
        info[str(names)] = []
        elems = parent_element.findAll(True, class_=names)
        for elem in elems:
            info[str(names)].append(elem.text.strip())

    return info # return 2d list of divs and their corresponding text


# Function to gather items asynchronously
async def gather_items_async(page_ind, pages, timestp, url_base, divs, tile_names, session):
    items = []
    try:
        page = pages[page_ind]
        print(f"Processing page: {page}")

        # Prepare headers
        ua = user_agent()
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://reddit.com/",
            "DNT": "1",
            "Connection": "keep-alive",
        }

        # Fetch and parse HTML
        soup = await get_html_soup_async(page, headers, session)
        if soup is None:
            return items

        if tile_names == "": # on no specific tile names, scrape the entire page
            item_tiles = soup
        else:
            selectors = ",".join(format_as_css_selectors(tile_names))  # Format tile names if needed and use as selectors
            item_tiles = soup.select(selectors)  # Find the tile selectors on the page


        if not item_tiles and soup.find('p', class_="code shift red"):
            print("Can't collect information for this page due to an inbuilt captcha.")
        else:
            for item_elem in item_tiles:
                info = scrape_info(item_elem, divs)
                items.append(info)  # Append the scraped information

    except Exception as e:
        print(f"Error on page {page_ind}: {e}")

    return items


# Main asynchronous function to scrape pages
async def scrape_pages_async(pages, timestp, url_base, divs, tile_names):
    items = []

    async with aiohttp.ClientSession() as session:
        tasks = [
            gather_items_async(page_index, pages, timestp, url_base, divs, tile_names, session)
            for page_index in range(len(pages))
        ]
        results = await asyncio.gather(*tasks)

    # Flatten results into a single list
    for result in results:
        if result:
            items.extend(result)

    return items


def format_as_css_selectors(strings):
    """
    Formats a list of strings to make them valid CSS selectors.

    - Adds '.' before class names (strings starting without '.' or '#').
    - Leaves IDs (strings starting with '#') unchanged.
    - Leaves tags or combinators (e.g., 'div', '>') unchanged.

    Args:
        strings (list of str): The list of strings to format.

    Returns:
        list of str: A new list with formatted CSS selectors.
    """
    formatted = []
    for s in strings:
        if not s.startswith(('.', '#')):  # If it doesn't start with '.' or '#'
            formatted.append(f".{s}")  # Assume it's a class and add '.'
        else:
            formatted.append(s)  # Leave IDs or already valid selectors unchanged
    return formatted
