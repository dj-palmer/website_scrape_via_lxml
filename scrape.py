#!/usr/bin/python

import pdb
import requests
from lxml import html
from concert_item import SummaryListing, EventInfo

# Some global constants - Details of the website you want to scrape
# listings from
URL = "http://www.wegottickets.com/searchresults/all"
LISTING_CLASS = "event_link"
EVENT_CLASS = "left full-width-mobile event-information event-width"
SUPPORT_CLASS = "support"
VENUE_CLASS = "venue-details"


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
        listings = self._tree.xpath('//a[@class="%s"]' % (LISTING_CLASS))
        for listing in listings:
            event_name = listing.xpath('text()')[0] or ""
            link = listing.xpath('@href')[0] or ""
            self.add_listing(SummaryListing(event_name, link))

        return self._listings

    def get_events_for_listings(self):
        """ Goes through each event in our listings, and tries to scrape
            the event details

            Results are stored in the _events array
        """
        for listing in self._listings:
            self.update(listing._link)
            self.get_event_details(listing._event_name, listing._link)

        return self._events

    def get_event_details(self, event_name="", link=""):
        """ For our page, comb for event details using an xpath search

            Result is stored in the _events array
        """
        print "Get_event_details called"
        event = self._tree

        # Get our event details, made up of name and support in form
        #   <div class="left full-width-mobile event-information event-width">
        #       <h1>main_event</h1>
        #       <h4 class="support_act">bar</h4>
        #   </div>
        #
        # Note: We could just get our event name from the one we got from
        # the listing, but we may want to re-use this method directly.
        event_details = event.xpath('//div[@class="%s"]' % (EVENT_CLASS))
        event_name = event_details[0].xpath('./h1/text()')[0]
        support_artists = event_details[0].xpath(
                            './h4[@class="%s"]/text()' % (SUPPORT_CLASS)
                          )[0]
        # print html.tostring(support_artists[0], pretty_print=True, \
        # method="html")

        # Venue details in form
        #  <div class="venue-details">
        #        <h2>GOUDHURST: Parish Church</h2>
        #        <h4>SUN 11TH DEC, 2016 6:00pm</h4>
        #    </div>
        venue_details = event.xpath('//div[@class="%s"]' % (VENUE_CLASS))

        city_loc_details = venue_details[0].xpath('./h2/text()')[0] or ""
        city = city_loc_details.split(":", 1)[0]
        if (len(city_loc_details.split(":", 1)) > 1):
            loc = city_loc_details.split(":", 1)[1]
        else:
            loc = ""

        date_time = venue_details[0].xpath('./h4/text()')[0]

        # Prices TBC

        # Some other useful info TBC

        # Store our event
        event_info = EventInfo(artist=event_name,
                               support=support_artists,
                               city=city,
                               venue=loc,
                               gig_date=date_time,
                               event_name=event_name,
                               link=link)

        self.add_event(event_info)

        return event_info


def main():
    scraper = Scraper()
    scraper.update("http://www.wegottickets.com/event/371642")
    print scraper.get_event_details()


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


if __name__ == "__main__":
    main()
