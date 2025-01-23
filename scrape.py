import requests
from bs4 import BeautifulSoup
import time
import re
from difflib import get_close_matches
from fake_user_agent import user_agent
from urllib.parse import urlparse, urljoin
import json
import os
# use: ua = user_agent(browser="chrome", use_cache=False) # now add this to headers

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
    info = scrape_pages(pages,timestp,url,divs, tile_names)
    print("done gathering info")
    return info

# function to fetch or load HTML and return BeautifulSoup object
# allows us to save html requests and use them later
# rather than putting in a new request each time
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



"""
uses the selenium webdriver to navigate to different product categories 
from the shop dropdown menu 
Parameters:
    url (str): page url

Returns:
    responses (list): a list of responses from the shop dropdown menu 

"""

# filter links so theyre unique and dont contain duplicates
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
        "Referer": "https://reddit.com/r/yeti",
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
uses given page urls to get product data using beautiful soup

Parameters:
    pages (2d list): list of shop page urls, organized by wayback urls collected

Returns:
    products (2d list): a list of helpful product information

"""
def scrape_info(parent_element, class_names): # class_names can either be 1d or 2d list
    info = {} # dict of info were collecting
    # extract name and type of product
    for names in class_names:
        elems = parent_element.findAll(True, class_=names)
        for elem in elems:
            info[str(names)] = elem.text.strip()

    return info # return 2d list of divs and their corresponding text
def scrape_pages(pages,timestp,url_base,divs, tile_names):
    items = []
    for page_index in range(len(pages)):
        items.append(gather_items(page_index, pages, timestp, url_base,divs, tile_names))

    for i in items:
        print(i)
        print("")

    return items

def gather_items(page_ind, pages, timestp, url_base, divs, tile_names):
    items = []
    try:
        page = pages[page_ind]
        #time.sleep(2) # a little sleep to prevent limiting
        print(page)
        #print("currently on page " + page + " at page ind " + str(page_ind))
        # request the page and parse with BeautifulSoup
        ua = user_agent()
        print(ua)
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://reddit.com/",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        # print(response.text)
        soup = get_html_soup(page, headers)
        if soup is None:
            return items

        selectors = ",".join(format_as_css_selectors(tile_names)) # format tile names if needed and use as selectors

        item_tiles = soup.select(selectors) # find the tile selectors on the page
        if len(item_tiles) == 0:
            if (soup.find('p', class_="code shift red")): # a captcha block error makes a page unusable
                print("cant collect information for this page due to an inbuilt captcha")
        for item_elem in item_tiles:
            info = scrape_info(item_elem, divs)
            items.append(info) # append timestp and the elements found

    # on connection errors, try again since these errors are due to too many requests
    except ConnectionRefusedError as e:
        print(e)
        print("trying again...")
        time.sleep(5)
        items = gather_items(page_ind, pages, timestp, url_base,divs, tile_names)
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("trying again...")
        time.sleep(5)
        items = gather_items(page_ind, pages, timestp, url_base,divs, tile_names)

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
