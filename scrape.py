#!/usr/bin/python
# -*- coding: utf-8 -*-

import pdb
import requests
from lxml import html
from concert_item import SummaryListing, EventInfo

# Some global constants - containing details of the website you want to scrape.
# When scraping I prefer to use specific classes of data items to search,
# rather than reference divisions of the website that are likely
# to change per event
URL = "http://www.wegottickets.com/searchresults/all"
CLASS_LISTING = "event_link"
CLASS_EVENT = "left full-width-mobile event-information event-width"
CLASS_SUPPORT = "support"
CLASS_VENUE = "venue-details"
CLASS_PRICE = "BuyBox diptych block"
CLASS_CONCESSION = "concession"


class ScraperStore(object):

    """ Storage to collect together all the events our Scraper
        gets from each of the indiviudal pages it scrapes
    """

    def __init__(self):
        self._events = {'events': []}

    def __repr__(self):
        return str(self._events)

    def add_events(self, events):
        if events is not None:
            self._events['events'].append(events)


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
        return str(
                  {'concerts': [{'listings': self._listings},
                                {'events': self._events}]}
               )

    def __str__(self):
        return (
                "{Concerts: \n   Listings : %s \n   Events : %s }" %
                (str(self._listings), str(self._events))
        )

    def update(self, url=URL):
        """ parse the html of the given url """
        self._url = url
        self._page = requests.get(self._url)
        self._tree = html.fromstring(self._page.content)

    def destroy(self):
        self._url = None
        self._page = None
        self._tree = None
        self._listings = []
        self._events = []

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

    def get_event_details(self, link=_url, event_name=""):
        """ For our page, comb for event details using an xpath search

            Result is stored in the _events array
        """
        event_info = None

        # Details we will try and scrape
        artist=""
        support_artists=""
        city="",
        loc="",
        date_time=""

        self.update(link)
        event = self._tree

        try:
            # Get our event details, made up of artist and support in form
            #   <div class="left full-width-mobile event-information event-width">
            #       <h1>main_artist</h1>
            #       <h4 class="support">support_act</h4>
            #   </div>
            #
            # Note: We could just get our event name from the one we got from
            # the listing, but allowing for use of this method on its own.
            event_details = event.xpath('//div[@class="%s"]' % (CLASS_EVENT))

            artist_seek = event_details[0].xpath('./h1/text()')
            artist = artist_seek[0] if (len(artist_seek) > 0) else ""
            # In case we were called directly with only a link
            if (event_name == ""): event_name = artist

            support_artists_seek = event_details[0].xpath(
                                    './h4[@class="%s"]/text()' % (CLASS_SUPPORT)
                                   )
            support_artists = support_artists_seek[0] if (len(support_artists_seek) > 0) else ""

            # print html.tostring(support_artists[0], pretty_print=True, method="html")

            # Venue details in form
            #  <div class="venue-details">
            #        <h2>GOUDHURST: Parish Church</h2>
            #        <h4>SUN 11TH DEC, 2016 6:00pm</h4>
            #    </div>
            venue_details = event.xpath('//div[@class="%s"]' % (CLASS_VENUE))

            if (len(venue_details) > 0):
                city_loc_seek = venue_details[0].xpath('./h2/text()')
                city_loc_details =  city_loc_seek[0] if (len(city_loc_seek)>1) else ""
                city = city_loc_details.split(":", 1)[0]
                if (len(city_loc_details.split(":", 1)) > 1):
                    loc = city_loc_details.split(":", 1)[1]
                else:
                    loc = ""

                date_time = venue_details[0].xpath('./h4/text()')[0]
            else:
                city = ""
                loc = ""
                date_time = ""

            # Some other useful info
            prices=self.get_prices(link)

            # Store our event
            event_info = EventInfo(artist=artist,
                                   support=support_artists,
                                   city=city,
                                   venue=loc,
                                   gig_date=date_time,
                                   prices=prices,
                                   event_name=event_name,
                                   link=link)

            self.add_event(event_info)

        except IndexError:
            print "Warning : Cannot find event details for %s" % (link)

        return event_info

    def get_prices(self, link=_url):
        """ Scrapes prices from a webpage and returns them in a JSON format
            { type : 'price_type', price : '£X.XX'}
        """
        # Prices TBC
        # XPATH = //*[@id="content"]/div[2]/div[5]'
        # <div class="block-group block-group-flex">
        # <div class="BuyBox diptych block">
        #     <div>
        #         <div>£10.00 + £1.00 Booking fee = <strong>£11.00</strong></div>
        #         <br>
        #         <div></div>
        #         <div>&nbsp;</div>
        #         <div><br><a href="http://www.wegottickets.com/faqs/22">No reallocation</a><br>All ages</div>
        #
        # <span><a href="http://www.wegottickets.com/faqs/7" class="offsaleLink">Not currently available</a></span>
        #
        #         <span class="VariantAlert"></span>
        #     </div>
        # </div>
        #
        # <div class="BuyBox diptych block">
        #     <div>
        #         <div>£5.00 + £0.50 Booking fee = <strong>£5.50</strong></div>
        #         <br>
        #         <div></div>
        #         <div><a href="http://www.wegottickets.com/faqs/8" class="concession">Children</a></div>
        #         <div><br><a href="http://www.wegottickets.com/faqs/22">No reallocation</a><br>All ages</div>
        #
        # <span><a href="http://www.wegottickets.com/faqs/7" class="offsaleLink">Not currently available</a></span>
        #
        #         <span class="VariantAlert"></span>
        #     </div>
        # </div>
        # </div>
        # //*[@id="Content"]/div[2]/div[5]/div
        prices = {}
        event = self._tree

        try :
            # pdb.set_trace()
            # Get a list of pricing blocks
            prices_seek = event.xpath('//div[@class="%s"]' % CLASS_PRICE)

            # Now try to scrape pricing and ticket type info from the block
            for price in prices_seek:
                amount = price.xpath('.//strong/text()')
                concession_seek = price.xpath('.//a[@class="concession"]/text()')
                concession = concession_seek[0] if len(concession_seek)>0 else None

                prices.update({"type": concession or "All", "amount": amount})

        except IndexError:
            print "Warning : Cannot find prices for %s" % (link)

        return str(prices)


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
