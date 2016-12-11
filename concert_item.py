# -*- coding: utf-8 -*-


class SummaryListing(object):

    """ Holds summary info of an event, from the search listings """

    def __init__(self, event_name="", link=""):

        self._event_name = event_name
        self._link = link

    def __repr__(self):
        return "Listing name : " + self._event_name + ", Link : " + self._link


class EventInfo(object):

    """ Full event info """

    def __init__(self, event_name="", link="", artist="", city="", venue="",
                 gig_date="", price=""):
        # Details asked for in our exercise
        self._artist = artist
        self._city = city
        self._venue = venue
        self._gig_date = gig_date
        self._price = price

        # Other info that could be useful
        self._event_name = event_name
        self._link = link
        self._description = ""
        self._website = ""

    def _get_json(self):
        return {
            'artist': self._artist,
            'city': self._city,
            'venue': self._venue,
            'gig_date': self._gig_date,
            'price': self._price
        }

    def __repr__(self):
        return str(self._get_json())
