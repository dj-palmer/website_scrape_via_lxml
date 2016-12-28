# concert_scraper

Just some more playing with Python libraries!

## Synopsis

An example implementation of a website scraper in python, using the lxml library. 

This is not intended to be a generic website scraper, merely an example of
how lxml can be used to process html, and navigate through it using xpath calls.

Run scrape.py with the -h flag to see runtime options. By default the script
will output to screen.

## scrape.py

Scrapes a website of information based on a URL and website classes, as defined 
in the scripts global variables.

get_prices method has a nice demonstration of stripping currency symbols from
prices, since currency symbols can be a bit tricky to process when they're
not ASCII (Python v2 default encoding)

## concert_item.py

Definitions of the event info to scrape from the website