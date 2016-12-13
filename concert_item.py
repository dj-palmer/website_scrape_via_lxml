# -*- coding: utf-8 -*-


class SummaryListing(object):

    """ Holds summary info of an event, from the search listings """

    def __init__(self, event_name="", link=""):

        self._event_name = event_name
        self._link = link

    def __repr__(self):
        return str({'Listing name': self._event_name, 'Link': self._link})


class EventInfo(object):

    """ Full event info """

    def __init__(self, event_name="", link="", artist="", support="", city="", venue="",
                 gig_date="", price=""):
        # Details asked for in our exercise
        self._artist = artist
        self._support = support
        self._city = city
        self._venue = venue
        self._gig_date = gig_date
        self._price = price

        # Other info that could be useful
        self._event_name = event_name
        self._link = link
        self._description = ""
        self._website = ""

    def get_json(self):
        """ JSON representation of a concert event  """
        return {
            'artists': {
                'main': self._artist,
                'support': self._support
            },
            'city': self._city,
            'venue': self._venue,
            'gig_date': self._gig_date,
            'prices': self._price
        }

    def __repr__(self):
        return str(self.get_json())
