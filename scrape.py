#!/usr/bin/python
# -*- coding: utf-8 -*-

# import pdb
import requests
import argparse
from lxml import html
from concert_item import SummaryListing, EventInfo

# Some global constants - containing details of the website you want to scrape.
# The below Scraper class uses specific classes of data items to search,
# rather than reference divisions of the website that are likely
# to change per event
URL = "http://www.wegottickets.com/searchresults/all"
CLASS_LISTING = "event_link"
CLASS_EVENT = "left full-width-mobile event-information event-width"
CLASS_SUPPORT = "support"
CLASS_VENUE = "venue-details"
CLASS_PRICE = "BuyBox diptych block"
CLASS_CONCESSION = "concession"
CLASS_PAGINATION = "pagination_link"
CURRENCY = "£"


class Scraper(object):

    """ A class for retrieving a single webpage of listings (from a url),
        parsing its HTML, and scraping data from those listings.

        To use the scraper, first call the update method with an appropriate
        url. You can then call the get methods, to start scraping data.
    """

    def __init__(self):
        self._url = None
        self._page = None
        self._tree = None
        # An array of SummaryListing objects
        self._listings = []
        # An array of EventInfo objects
        self._events = []
        self._max_page_num = 1

    def __repr__(self):
        return (
                "{'concerts': [{'listings': %s, {'events': %s}]}" %
                (self._listings, self._events)
               )

    def __str__(self):
        return (
                "{Concerts: \n   Listings : %s \n   Events : %s }" %
                (self._listings, self._events)
        )

    def get_events_json(self):
        return (
                "{'Events' : %s }" % str(self._events)
        )

    def update(self, url=URL):
        """ parses the html of the given url into our element tree """
        self._url = url
        self._page = requests.get(self._url)
        self._tree = html.fromstring(self._page.content)

    def add_listing(self, listing):
        if listing is not None:
            self._listings.append(listing)

    def add_event(self, event):
        if event is not None:
            self._events.append(event)

    def get_listings(self):
        """ For our page, comb for listings using an xpath search

            Each listing has the name of an event, with a link direct
            to that events own page

            Results are stored in the _listings array
        """
        listings = self._tree.xpath('//a[@class="%s"]' % (CLASS_LISTING))
        for listing in listings:
            try:
                event_name = listing.xpath('text()')[0]
                link = listing.xpath('@href')[0]
                self.add_listing(SummaryListing(event_name, link))
            except IndexError:
                # we've not been able to find details, move onto the next
                pass

        return self._listings

    def get_events_for_listings(self, verbose=False):
        """ Goes through each event in our listings, and tries to scrape
            the event details

            Results are stored in the _events array
        """
        count = 0
        if verbose:
            print "{ events: ["

        for listing in self._listings:
            event_info = self.get_event_details(listing._link, listing._event_name)
            if verbose:
                if event_info:
                    print ((" " + str(event_info)) if count == 0 else ("," + str(event_info)))
                    count += 1

        if verbose:
            print "]}"

        return self._events

    def get_event_details(self, link, event_name=""):
        """ For our page, comb for event details using an xpath search

            Result is stored in the _events array
        """
        event_info = None

        self.update(link)
        event = self._tree

        try:
            artist = self.get_artist()
            # In case we were called directly with only a link
            if (event_name == ""):
                event_name = artist

            support = self.get_support_act()
            prices = self.get_prices()
            venue_details = self.get_venue_details()

            # Store our event
            event_info = EventInfo(artist=artist,
                                   support=support,
                                   city=venue_details['city'],
                                   venue=venue_details['loc'],
                                   gig_date=venue_details['time'],
                                   prices=prices,
                                   event_name=event_name,
                                   link=link)

            self.add_event(event_info)

        except IndexError:
            print "Warning : Cannot find event details for %s" % (link)

        return event_info

    def get_artist(self):
        artist = ""
        event = self._tree

        try:
            artist_details = event.xpath('//div[@class="%s"]' % (CLASS_EVENT))

            artist_seek = artist_details[0].xpath('./h1/text()')
            artist = artist_seek[0] if (len(artist_seek) > 0) else ""

        except IndexError:
            print "Warning : Cannot find artist for %s" % (self._url)

        return artist

    def get_support_act(self):
        support = ""
        event = self._tree

        try:
            support_details = event.xpath('//div[@class="%s"]' % (CLASS_EVENT))

            support_seek = support_details[0].xpath(
                                './h4[@class="%s"]/text()' % (CLASS_SUPPORT)
                           )

            support = support_seek[0] if (len(support_seek) > 0) else ""

        except IndexError:
            print "Warning : Cannot find support for %s" % (self._url)

        return support

    def get_venue_details(self):
        """ Scrapes venue details from our webpage and returns them in format
            {'city': city, 'loc': location, 'time': time}
        """
        loc = ""
        city = ""
        time = ""

        venue = {'city': city, 'loc': loc, 'time': time}
        event = self._tree

        try:
            venue_details = event.xpath('//div[@class="%s"]' % (CLASS_VENUE))

            if (len(venue_details) > 0):

                city_loc_seek = venue_details[0].xpath('./h2/text()')
                city_loc_details = city_loc_seek[0] if (len(city_loc_seek) > 0) else ""
                city = city_loc_details.split(":", 1)[0]

                if (len(city_loc_details.split(":", 1)) > 1):
                    loc = city_loc_details.split(":", 1)[1]

                time_seek = venue_details[0].xpath('./h4/text()')
                time = time_seek[0] if (len(time_seek) > 0) else ""

            venue.update({'city': city})
            venue.update({'loc': loc})
            venue.update({'time': time})

        except IndexError:
            print "Warning : Cannot find venue for %s" % (self._url)

        return venue

    def get_prices(self):
        """ Scrapes prices from our webpage and returns them in format
            { type : 'price_type', price : 'X.XX'}
        """
        prices = []
        event = self._tree

        try:
            # Get a list of pricing blocks
            prices_seek = event.xpath('//div[@class="%s"]' % CLASS_PRICE)

            # Now try to scrape pricing and ticket type info from each block
            for price in prices_seek:
                amount = None
                amount_seek = price.xpath('.//strong/text()')
                amount_cur = amount_seek[0] if len(amount_seek) > 0 else None
                if amount_cur:
                    # strip the currency symbol from our amount and print to 2dp
                    amount = "%.2f" % (float(amount_cur[amount_cur.find(CURRENCY.decode("utf8"))+1:]))
                conc_seek = price.xpath('.//a[@class="concession"]/text()')
                concession = conc_seek[0] if len(conc_seek) > 0 else None

                if amount:
                    prices.append({"type": concession or "All", "amount": amount})

        except IndexError:
            print "Warning : Cannot find prices for %s" % (self._url)

        return prices

    def get_site_max_page_num(self):
        try:
            event = self._tree
            page_seek = event.xpath('//a[@class="%s"][last()]/text()' % CLASS_PAGINATION)
            max_page_num = page_seek[0] if len(page_seek) > 0 else None

        except IndexError:
            print "Warning : Cannot find max pagination for %s. Returning last known pagination" % (self._url)

        return int(max_page_num)

    def set_max_page_num(self, max_pages=None):
        max_page_num = self._max_page_num
        if max_pages:
            max_page_num = max_pages
        else:
            max_page_num = self.get_site_max_page_num()

        self._max_page_num = int(max_page_num)


def main():
    do_WGT_scrape()


def do_WGT_scrape(max_pages=1):
    """ Instanciates a Scraper for the wegottickets.com listings URL.
        It begins on the first of the search listing pages, then crawls through
        the remaining listing pages up to the number of pages specified.

        If no number of pages specified, the Scraper will try and identify
        the max pagination and crawl all listings.

        Once all listings have been identified, the scraper will scrape each
        event page for those listings

        Finally the script will output to
    """
    args = parse_args()
    base_url = "http://www.wegottickets.com/searchresults/page/%s/all#paginate"
    verbose = args.verbose or False
    outfile = args.output_file or None
    max_pages = None if args.page_limit is None else int(args.page_limit)

    # Get listings on each search results page
    scraper = Scraper()
    scraper.update()
    scraper.set_max_page_num(max_pages)
    for pagenum in range(1, scraper._max_page_num+1):
        scraper.update(base_url % (pagenum))
        scraper.get_listings()

    # Scrape Events
    scraper.get_events_for_listings(verbose=verbose)

    # Output
    if outfile:
        fw = open(outfile, 'w')
        fw.write(scraper.get_events_json())
        fw.close
    else:
        print scraper.get_events_json()


def parse_args():
    parser = argparse.ArgumentParser(
                description =
                "Script to scrape the wegottickets.com website of event "
                "data. By default the script outputs to screen at the very "
                "end of our scraping, but you can specify an output file "
                "for the event JSON too"
             )
    parser.add_argument('-of', '--output_file', default="/tmp/events.json",
                        help="Output file for JSON")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Outputs event JSON to screen as we find it")
    parser.add_argument('-p', '--page_limit',
                        help="max number of listing pages to scrape")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
