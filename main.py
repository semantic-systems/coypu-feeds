import pytz
from gdeltdoc import GdeltDoc, Filters
import feedparser
from os import listdir
from os.path import isfile, join
import opml
from lxml.etree import XMLSyntaxError
import json
from datetime import datetime
import dateparser
from flask import Flask, request

app = Flask(__name__)

file_dir_countries = "awesome-rss-feeds/countries/without_category/"
country_files = [f.replace(".opml", "") for f in listdir(file_dir_countries) if isfile(join(file_dir_countries, f))]
SOURCES = ["RSS", "GDELT"]
DEFAULT_LANGUAGE = "English (United States) - en-us"
DEFAULT_COUNTRY = "Germany"
DELAULT_TRIME_FRAME = "1d"

@app.route('/')
def get_feed():
    keywords = request.args.get('keywords')
    domains = request.args.get('domains')
    time_frame = request.args.get('time_frame')
    themes = request.args.get('themes')
    number_articles = int(request.args.get('number_articles')) if request.args.get('number_articles') else 0
    language = request.args.get('language')
    countries = request.args.get('countries')

    #Setting of default values
    language = language if language else DEFAULT_LANGUAGE
    countries = countries if countries else DEFAULT_COUNTRY
    time_frame = time_frame if time_frame else DELAULT_TRIME_FRAME

    if keywords == "":
        return "Error: at least a keyword is required."

    language_rss = language.split(" - ")[1] if language != "" else language
    language_gdelt = language.split(" - ")[0].split(" (")[0]
    article_feed = []
    countries = countries.split(";")
    limit_number_articles = 0

    for index, country in enumerate(countries):

        #Checking the number of articles limit
        if number_articles > 0:
            number_sources = len(SOURCES)
            if len(countries) == 1:
                limit_number_articles = (number_articles / number_sources)
            elif len(countries) % 2 == 0:
                limit_number_articles = (number_articles / number_sources) / len(countries)
            else:
                if index == len(countries) - 1:
                    limit_number_articles = int((number_articles / number_sources) / len(countries)) + 1
                else:
                    limit_number_articles = int((number_articles / number_sources) / len(countries))

        article_counter = 0
        if country in country_files:
            """
            Iterating on the RSS Feeds
            """
            try:
                for item in opml.parse(file_dir_countries + country + ".opml"):
                    # Checking for domains
                    if domains:
                        is_in_domain = False
                        for domain in domains.split(";"):
                            if domain in item.xmlUrl:
                                is_in_domain = True
                                break
                        if not is_in_domain:
                            continue

                    feed = feedparser.parse(item.xmlUrl)

                    # Checking for language constraint
                    try:
                        if language and feed.feed.language.lower() != language_rss:
                            continue
                    except AttributeError:
                        continue

                    # Iterating over the entries in the feeds
                    for entry in feed.entries:
                        try:
                            # Checking for keywords constraint
                            is_keyword_in = False
                            for keyword in keywords.split(";"):
                                if keyword in entry.title or keyword in entry.summary:
                                    is_keyword_in = True
                                    break
                            if not is_keyword_in:
                                continue

                            # Checking for theme constraint
                            if themes:
                                is_theme_in = False
                                for theme in themes.split(";"):
                                    for tag in entry.tags:
                                        if theme in tag.term:
                                            is_theme_in = True
                                            break
                                if not is_theme_in:
                                    continue

                            # Checking for time_frame constraint
                            timestamp = dateparser.parse(entry.published)
                            if time_frame:

                                now = datetime.now(pytz.utc)
                                diff = now - timestamp
                                if time_frame == "1h":
                                    if diff.total_seconds() > 3600:
                                        continue
                                elif time_frame == "1d":
                                    if diff.days > 0:
                                        continue
                                elif time_frame == "1w":
                                    if diff.days > 6:
                                        continue
                                elif time_frame == "15m":
                                    if diff.total_seconds() > 900:
                                        continue

                            if number_articles > 0 and article_counter >= limit_number_articles:
                                break
                            article_counter += 1
                            if "*" in entry.link:
                                article_feed.append(
                                    {"tittle": entry.title, "link": entry.link.split("*")[1],
                                     "time": timestamp.strftime("%a, %d %b %Y %H:%M:%S %z"),
                                     "source": SOURCES[0]})
                            else:
                                article_feed.append({"tittle": entry.title, "link": entry.link,
                                                     "time": timestamp.strftime("%a, %d %b %Y %H:%M:%S %z"),
                                                     "source": SOURCES[0]})
                        except AttributeError:
                            continue
            except XMLSyntaxError:
                print("Error on XML file for RSS links : " + file_dir_countries + country + ".opml")

        """
        Going through the Gdelt feed
        """

        if ";" in keywords:
            keywords = keywords.split(";")

        if domains and ";" in domains:
            domains = domains.split(";")

        if themes and ";" in themes:
            themes = themes.split(";")

        gdelt_filters = Filters(
            keyword=keywords,
            timespan=time_frame,
            domain=domains,
            country=country.lower().replace(" ", ""),
            theme=themes,
            num_records=limit_number_articles if number_articles > 0 else 250
        )

        gd = GdeltDoc()

        # Iterating through the articles from the Gdelt after applying the filters, if there are any
        for index_row, row in gd.article_search(gdelt_filters).iterrows():
            # Checking for language constraint
            if language != "" and row.language.lower() != language_gdelt.lower():
                continue
            time_string = row.seendate.replace("T", "").replace("Z", "")+"UTC"
            timestamp = dateparser.parse(date_string=time_string,
                                         date_formats=["%Y%m%d%H%M%S%Z"])

            article_feed.append({"tittle": row.title, "link": row.url,
                                 "time": timestamp.strftime("%a, %d %b %Y %H:%M:%S %z"), "source": SOURCES[1]})

    if not bool(article_feed):
        return "No results found on this topic or country for the keywords inserted"
    return json.dumps(article_feed, indent=2)


app.run()
