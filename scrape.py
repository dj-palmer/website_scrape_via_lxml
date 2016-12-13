#!/usr/bin/python
# -*- coding: utf-8 -*-

import pdb
import requests
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

    def update(self, url=URL):
        """ parses the html of the given url """
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

    def get_events_for_listings(self):
        """ Goes through each event in our listings, and tries to scrape
            the event details

            Results are stored in the _events array
        """
        for listing in self._listings:
            self.get_event_details(listing._link, listing._event_name)

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
            if (event_name == ""): event_name = artist

            support = self.get_support_act()
            prices=self.get_prices()
            venue_details=self.get_venue_details()

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

        try :
            artist_details = event.xpath('//div[@class="%s"]' % (CLASS_EVENT))

            artist_seek = artist_details[0].xpath('./h1/text()')
            artist = artist_seek[0] if (len(artist_seek) > 0) else ""

        except IndexError:
            print "Warning : Cannot find artist for %s" % (self._url)

        return artist

    def get_support_act(self):
        support = ""
        event = self._tree

        try :
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

        try :
            venue_details = event.xpath('//div[@class="%s"]' % (CLASS_VENUE))

            if (len(venue_details) > 0):
                
                city_loc_seek = venue_details[0].xpath('./h2/text()')
                city_loc_details =  city_loc_seek[0] if (len(city_loc_seek)>0) else ""
                city = city_loc_details.split(":", 1)[0]
                
                if (len(city_loc_details.split(":", 1)) > 1):
                    loc = city_loc_details.split(":", 1)[1]
             
                time_seek = venue_details[0].xpath('./h4/text()')
                time = time_seek[0] if (len(time_seek)>0) else ""

            venue.update({'city': city})
            venue.update({'loc': loc})
            venue.update({'time': time})

        except IndexError:
            print "Warning : Cannot find venue for %s" % (self._url)

        return venue

    def get_prices(self):
        """ Scrapes prices from our webpage and returns them in format
            { type : 'price_type', price : '£X.XX'}
        """
        prices = {}
        event = self._tree

        try :
            # Get a list of pricing blocks
            prices_seek = event.xpath('//div[@class="%s"]' % CLASS_PRICE)

            # Now try to scrape pricing and ticket type info from the block
            for price in prices_seek:
                amount = None
                amount_seek = price.xpath('.//strong/text()')
                amount_cur = amount_seek[0] if len(amount_seek)>0 else None
                if amount_cur :
                    # strip the currency symbol from our amount and print to 2dp
                    amount = "%.2f" % (float(amount_cur[amount_cur.find(CURRENCY.decode("utf8"))+1:]))
                conc_seek = price.xpath('.//a[@class="concession"]/text()')
                concession = conc_seek[0] if len(conc_seek)>0 else None

                prices.update({"type": concession or "All", "amount": amount})

        except IndexError:
            print "Warning : Cannot find prices for %s" % (self._url)

        return prices


def main():
    # scraper = Scraper()
    # scraper.update("http://www.wegottickets.com/event/381189")
    # print scraper.get_prices()
    do_scrape()

def do_scrape():

    scraper = Scraper()
    # Scraping one web page as proof of concept, then can loop through these
    # steps for each page.
    # Using the 'all' search page to find the basic listing details, and then
    # we'll use the link we find to gather more details
    scraper.update(URL)
    scraper.get_listings()
    scraper.get_events_for_listings()
    # print html.tostring(listings[0], pretty_print=True, method="html")

    print scraper

if __name__ == "__main__":
    main()
