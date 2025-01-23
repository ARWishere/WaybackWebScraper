import wayback_generator
import scrape_async as scrape

def wb_scraper(url,start,end,interval, keywords):
    # gather wayback snapshots using the wayback api
    snap_items = []
    snapshots = wayback_generator.collect_urls(url, start, end, interval)

    # continue the setup process
    print("Now using your browser, right click and inspect the page on any item on the page")
    print("Move around a little, once all components of an item are highlighted (ie the name, image, and price) in a square")
    print("Copy and paste the class name (should be like class=name) of the object you are highlighting here from the inspect window")
    print("Common identifiers to look for in this name are: grid, tile, product, item, card, etc.")
    print("Alternatively, leave this blank and move on to the next section and data can be sorted manually later")
    parent_tile_names = (input("name: "))
    print("Now do the same on a few of the web archive links below, separate them with a ,")
    for snap in snapshots:
        print(snap)
    print("Only enter them if they're different")
    parent_tile_names = parent_tile_names + ", " + (input("names: "))
    parent_tile_names = parent_tile_names.split()
    parent_tile_names = [i.strip() for i in parent_tile_names]

    print("Now, inspect element only the components of the item you want gathered and enter that class name here")
    print("For example, if you want to scrape the name inspect it by right clicking and copy the corresponding class name from the inspect window")
    print("Separate all the component class names with a , and hit enter when done")
    class_names = input("names: ")
    print("Now do the same on a few of the web archive links from above")
    print("Only type them if they're different and separate them with a ,")
    class_names = class_names + ", " + input("names: ")
    class_names = class_names.split(',')
    class_names = [i.strip() for i in class_names] # remove trailing and leading white spaces

    # examples of input post formatting if needed:
    #class_names = ["product-variation-name", "product-master-name", "value"] # example classes i scraped
    #parent_tile_names = ["product", "product-tile", "product.grid-tile"] # example parent tiles i used
    #keywords = ["new-arrivals", "drinkware", "coolers", "bags", "cargo", "outdoor-living", "apparel",
    #            "chairs", "gear", "accessories", "more-gear", "dogs"]  # example keywords i used

    print("::::Now Scraping::::")

    for snap in snapshots:
        snap_items.append(scrape.scrape_items(snap.archive_url,snap.timestamp, class_names, parent_tile_names, url, format_keywords(keywords)))
    for snap in snap_items:
        for prods in snap:
            out_str = ""
            for name in class_names:
                out_str += name + ": "
                try:
                    out_str += prods[name]
                except KeyError:
                    out_str += " "
                out_str += ", "

            print(out_str)

    return snap_items


# format a list of words so that they can be compatible with links, ie replace ' ' with '-'
def format_keywords(keywords):
    return [keyword.replace(' ', '-') for keyword in keywords]

if __name__ == '__main__':
    print("Copy and paste the HOMEPAGE URL you want to scrape items from, as if you were entering it into the wayback machine")
    url = input("URL: ")
    print("Enter a few product category keywords to scrape (ie apparel, bags, gear, food, toys, etc.) and seperate them with a , :")
    print("Think words that are typically at the end of a url for each category like example.com/shop or example.com/bags")
    print("Alternatively, hit enter and leave this question blank and every page found will be searched")
    keywords = input("Keywords: ")
    print("Enter start date in yyyymmdd format:")
    start = input("Start Date: ") + "000000" # use 000000 for hhmmss
    print("Enter end date in yyyymmdd format:")
    end = input("End Date: ") + "000000"
    print("Enter minimum interval of days between wayback snapshots:")
    interval = input("Interval: ")
    # we have all the info we need to gather snapshots, so lets begin the program and continue the setup later
    all_items = wb_scraper(url, start, end, int(interval), keywords)


