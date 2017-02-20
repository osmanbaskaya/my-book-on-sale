from __future__ import print_function
import mechanize
import codecs
from bs4 import BeautifulSoup


MAX_PAGE = 50
AMAZON_KINDLE_STORE_URL = "https://www.amazon.com/b/ref=sv_kstore_4?ie=UTF8&node=11552285011"
GOODREADS_URL = "https://www.goodreads.com/review/list/{}?shelf={}"


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


if __name__ == '__main__':
    check_any_book_on_sale()
    print("Done.")
