#!/usr/bin/python

import pdb
import requests
from lxml import html
from concert_item import SummaryListing, EventInfo

# Website details of the website you want to scrape listings from:
_url = "http://www.wegottickets.com/searchresults/all"
_listing_class = "event_link"


class Scraper(object):

    """ A class for retrieving a website, parsing its HTML into an
        XPath format, and storing scraped data
    """

    def __init__(self):
        self._page = None
        self._tree = None
        self._listings = {'listings': []}
        self._events = {'events': []}

    def _update(self, url):
        try:
            self._page = requests.get(url)
            self._tree = html.fromstring(self._page.content)
        except:
            print "Invalid url"

    def _add_listing(self, listing):
        if listing is not None:
            self._listings.append(listing)


def main():

    # Use the search page to find the basic listing details, and then we'll
    # use the link we find to gather more details

    scraper = Scraper()
    scraper._update(_url)

    # listings = scraper._tree.xpath('//div[@class="content block-group chatterbox-margin"]')
    listings = scraper._tree.xpath('//a[@class="%s"]' % (_listing_class))

    print(listings)

    foo = html.tostring(listings[0], pretty_print=True, method="html")
    print foo
    # for listing in listings:
    print listings[0].xpath('text()')
    print listings[0].xpath('@href')

    # listing_names = scraper._tree.xpath('//a[@class="event_link"]/text')
    # event_urls = scraper._tree.xpath('//a[@class="event_link"]/@href')
    # print "listing is : " + str(listing)
    # print "event is : " + str(event)


if __name__ == "__main__":
    main()
