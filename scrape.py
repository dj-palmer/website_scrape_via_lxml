#!/usr/bin/python

import pdb
import requests
from lxml import html
from concert_item import SummaryListing, EventInfo

# Some global constants - Website details you want to scrape listings from
URL = "http://www.wegottickets.com/searchresults/all"
LISTING_CLASS = "event_link"


class Scraper(object):

    """ A class for retrieving a webpage, parsing its HTML,
        and storing scraped data.
    """

    def __init__(self):
        self._page = None
        self._tree = None
        self._listings = {'summary_listings': []}
        self._events = {'events': []}

    def __repr__(self):
        return str({'concerts': [self._listings, self._events]})

    def __str__(self):
        return ("{'concerts': \n %s \n %s }" % (str(self._listings),
                                                str(self._events)))

    def update(self, url):
        """ parse the html of the given url """
        try:
            self._page = requests.get(url)
            self._tree = html.fromstring(self._page.content)
        except:
            raise Exception("Invalid url")

    def add_listing(self, listing):
        if listing is not None:
            self._listings['summary_listings'].append(listing)

    def add_event(self, event):
        if event is not None:
            self._events['events'].append(event)

    def get_listings(self):
        """ for our page, comb for listings using an xpath
            search, and then store them in our scraper
        """
        listings = self._tree.xpath('//a[@class="%s"]' % (LISTING_CLASS))
        for listing in listings:
            event_name = listing.xpath('text()')[0] or ""
            link = listing.xpath('@href')[0] or ""
            summary_listing = SummaryListing(event_name, link)
            self.add_listing(summary_listing)


def main():

    scraper = Scraper()
    # Scraping one web page as proof of concept, then can loop through these
    # steps for each page.
    # Using the 'all' search page to find the basic listing details, and then
    # we'll use the link we find to gather more details
    scraper.update(URL)

    scraper.get_listings()

    print scraper
    # print html.tostring(listings[0], pretty_print=True, method="html")


if __name__ == "__main__":
    main()
