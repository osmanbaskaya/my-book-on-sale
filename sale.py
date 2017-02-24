from __future__ import print_function
import requests
import mechanize
import datetime
import codecs
from bs4 import BeautifulSoup
from multiprocessing import Pool


MAX_PAGE = 50
AMAZON_KINDLE_STORE_URL = "https://www.amazon.com/b/ref=sv_kstore_4?ie=UTF8&node=11552285011"
GOODREADS_URL = "https://www.goodreads.com/review/list/{}?shelf={}"
GOODREADS_BASE_URL = "https://www.goodreads.com"
HEADERS = {'User-agent': "Firefox"}


def check_any_book_on_sale():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=False, default="18882054-osman-ba-kaya",
                        help="Provide user information formatted like 18882054-osman-ba-kaya")
    parser.add_argument('--filename', required=False, default=None)
    parser.add_argument('--shelf', required=False, default='to-read')
    args = parser.parse_args()
    if args.filename is None:
        if args.user is None:
            raise ValueError("Either --filename or --user should be set")
        url = GOODREADS_URL.format(args.user, args.shelf)
        goodreads_books = get_books_from_goodreads(url)
    else:
        with open(args.filename) as f:
            goodreads_books = set(f.read().splitlines())

    amazon_books = get_books_on_sale()

    inters = goodreads_books.intersection(amazon_books)
    print("Intersection:\n{}".format("\n".join(inters)))


def get_books_on_sale():

    br = mechanize.Browser()
    br.set_handle_robots(False)  # no robots
    br.set_handle_refresh(False)
    br.addheaders = [('User-agent', 'Firefox')]

    br.open(AMAZON_KINDLE_STORE_URL)

    next_link = None
    for link in br.links():
        if link is not None:
            if link.text == "See all of today's deals":
                next_link = link
                break

    r = br.follow_link(next_link)
    text = r.read()
    soup = BeautifulSoup(text, 'lxml')
    items = soup.find_all("div", {"class": "productTitle"})

    amazon_books = set()

    for item in items:
        amazon_books.add(item.a.text)

    print("{} books retrieved from Amazon.\n".format(len(amazon_books)))
    return amazon_books


def get_books_from_goodreads(user_to_read_shelf_link, out_fn="books-in-to-read.txt"):

    user_to_read_shelf_link = "%s&view=covers&page={}" % user_to_read_shelf_link

    goodreads_book_titles = set()

    br = mechanize.Browser()
    br.set_handle_robots(False)  # no robots
    br.set_handle_refresh(False)
    br.addheaders = [('User-agent', 'Firefox')]

    for i in range(1, MAX_PAGE):
        print("Processing Goodreads page-%d" % i)
        r = br.open(user_to_read_shelf_link.format(i))
        text = r.read()
        soup = BeautifulSoup(text, 'lxml')
        items = soup.find_all("div", {"class": "bookalike review"})
        if len(items) != 0:
            for item in items:
                title = item.a.img['alt']
                goodreads_book_titles.add(title)
        else:
            break

    print("\n{} books retrieved from Goodreads.".format(len(goodreads_book_titles)))

    with codecs.open(out_fn, 'w', encoding='utf8') as f:
        f.write("\n".join(goodreads_book_titles))

    return goodreads_book_titles


def get_amazon_price(amazon_book_response):
    soup = BeautifulSoup(amazon_book_response.text, 'lxml')
    prices = soup.find_all('input', {"name": "displayedPrice"})
    if len(prices) != 0:
        return prices[0]['value']
    else:
        prices = soup.find_all("span", {'class': "a-size-small a-color-price"})
        if len(prices) != 0:
            return prices[0].text[1:]
        else:
            prices = soup.find_all("span", {'class': "a-size-base mediaTab_subtitle"})
            price_titles = soup.find_all("span", {'class': "a-size-large mediaTab_title"})
            idx = -1
            for i, t in enumerate(price_titles):
                if t.text == 'eTextbook' or t.text == 'Kindle':
                    idx = i
                    break
            if len(prices) != 0 and idx != -1:
                return prices[0].text.strip()[1:]
            else:
                return "NA"


def get_amazon_book_url(goodread_book_response):
    soup = BeautifulSoup(goodread_book_response.text, 'lxml')
    urls = soup.find_all('a', {"class": 'buttonBar'})
    for url in urls:
        if u'Amazon' in url.text:
            return "{}{}".format(GOODREADS_BASE_URL, url['href'])


def get_goodread_book_url(div):
    return "{}{}".format(GOODREADS_BASE_URL, div.find('a')['href'])


def get_book_price(item, headers=HEADERS):
    book_url = get_goodread_book_url(item)
    book_name = item.img['alt']
    r = requests.get(book_url, headers=headers)
    amazon_book_url = get_amazon_book_url(r)
    amazon_book_response = requests.get(amazon_book_url, headers=headers)
    price = get_amazon_price(amazon_book_response)
    row = u"{}\t{}\t{}\t{}".format(book_url, amazon_book_url, book_name, price)
    # print(u"{} {}".format(book_name, price))
    return row


def get_price_list_for_books(headers=HEADERS):

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=False, default="18882054-osman-ba-kaya",
                        help="Provide user information formatted like 18882054-osman-ba-kaya")
    parser.add_argument('--filename', required=False, default=None)
    parser.add_argument('--shelf', required=False, default='to-read')
    args = parser.parse_args()

    today = datetime.datetime.today()

    print("Date: {}".format(today.strftime("%Y-%m-%d %H:%M")))

    url = GOODREADS_URL.format(args.user, args.shelf)

    user_to_read_shelf_url = "%s&view=covers&page={}" % url

    items = []
    for i in range(1, MAX_PAGE):
        print("Goodreads page-%d processing" % i)
        r = requests.get(user_to_read_shelf_url.format(i), headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        curr_items = soup.find_all("div", {"class": "bookalike review"})
        if len(curr_items) == 0:
            break
        items.extend(curr_items)

    print("Total # of books: {}".format(len(items)))

    # price_list = list(map(get_book_price, items))
    pool = Pool(10)
    price_list = pool.map(get_book_price, items)

    out_fn = 'prices/{}-price-list.txt'.format(today.strftime("%Y-%m-%d"))
    with codecs.open(out_fn, 'w', encoding='utf8') as f:
        f.write("\n".join(price_list))


if __name__ == '__main__':
    get_price_list_for_books()
    print("Done.")
