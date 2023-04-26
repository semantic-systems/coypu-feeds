import os

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
import pycountry

app = Flask(__name__)

file_dir_countries = "{0}/rss-feed-library/countries/".format(os.getcwd())
country_files = [f.replace(".opml", "") for f in listdir(file_dir_countries) if isfile(join(file_dir_countries, f))]
SOURCES = ["RSS", "GDELT"]
DEFAULT_LANGUAGE = "English (United States) - en-us"
DEFAULT_COUNTRY = "Germany"
DELAULT_TRIME_FRAME = "1d"
REQUEST_KEY = 'VD3WRN6RE2VM2ACJ'


@app.route('/', methods=['POST'])
def get_feed():
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    keywords = request.json.get('keywords')
    domains = request.json.get('domains')
    time_frame = request.json.get('time_frame')
    themes = request.json.get('themes')
    number_articles = int(request.json.get('number_articles')) if request.json.get('number_articles') else 0
    language = request.json.get('language')
    countries = request.json.get('countries')

    # Setting of default values
    language = language if language else DEFAULT_LANGUAGE
    countries = countries if countries else DEFAULT_COUNTRY
    time_frame = time_frame if time_frame else DELAULT_TRIME_FRAME

    if not keywords:
        return json.dumps({'error': 'Missing keywords for the search'}, indent=2), 400

    language_rss = language.split(" - ")[1] if language != "" else language
    language_gdelt = language.split(" - ")[0].split(" (")[0]
    article_feed = []
    countries = countries.split(";")
    limit_number_articles = 0

    for index, country in enumerate(countries):
        try:
            country_iso = pycountry.countries.get(name=country)
            if not country_iso:
                country = pycountry.countries.get(alpha_3=country)
                if not country:
                    return json.dumps({'error': "No results found on this country, please verify the code or name of it"},
                                      indent=2), 204
            else:
                country = country_iso
        except ValueError:
            return json.dumps({'error': "No results found on this country, please verify the code or name of it"},
                              indent=2), 204

        # Checking the number of articles limit
        if number_articles > 0:
            number_sources = len(SOURCES)
            if len(countries) % 2 == 0 or len(countries) == 1:
                limit_number_articles = (number_articles / number_sources) / len(countries)
            else:
                if index == len(countries) - 1:
                    limit_number_articles = int((number_articles / number_sources) / len(countries)) + 1
                else:
                    limit_number_articles = int((number_articles / number_sources) / len(countries))

        article_counter = 0
        if country.name in country_files:
            """
            Iterating on the RSS Feeds
            """
            try:
                for item in opml.parse(file_dir_countries + country.name + ".opml"):
                    # Checking for domains
                    if domains:
                        is_in_domain = False
                        for domain in domains.split(";"):
                            if domain in item.xmlUrl:
                                is_in_domain = True
                                break
                        if not is_in_domain:
                            continue
                    try:
                        feed = feedparser.parse(item.xmlUrl)
                    except:
                        print("Error on request for the feed in the country file " + file_dir_countries + country.name +
                              ".opml. The URL rasing this error is: "+item.xmlUrl)
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
                                    {"title": entry.title, "url": entry.link.split("*")[1],
                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "source": SOURCES[0]})
                            else:
                                article_feed.append({"title": entry.title, "url": entry.link,
                                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                     "source": SOURCES[0]})
                        except AttributeError:
                            continue
            except XMLSyntaxError:
                print("Error on XML file for RSS links : " + file_dir_countries + country.name + ".opml")

        """
        Going through the Gdelt feed
        """

        if ";" in keywords:
            keywords = keywords.split(";")

        if domains and ";" in domains:
            domains = domains.split(";")

        if themes and ";" in themes:
            themes = themes.split(";")

        try:
            json_exceptions = json.load(open("exceptions.json"))['countries_names']
            is_exception = country.name in json_exceptions

            gdelt_filters = Filters(
                keyword=keywords,
                timespan=time_frame,
                domain=domains,
                country=country.name if not is_exception else json_exceptions[country.name],
                theme=themes,
                num_records=limit_number_articles if number_articles > 0 else 250
            )

            gd = GdeltDoc()

            # Iterating through the articles from the Gdelt after applying the filters, if there are any
            for index_row, row in gd.article_search(gdelt_filters).iterrows():
                # Checking for language constraint
                if language != "" and row.language.lower() != language_gdelt.lower():
                    continue
                timestamp = dateparser.parse(date_string=row.seendate,
                                             date_formats=["%Y%m%dT%H%M%SZ"])

                article_feed.append({"title": row.title, "url": row.url,
                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": SOURCES[1]})
        except ValueError:
            print("Invalid or Unsupported Country: '"+country.name + "'.Please check the documentation.")

    if not bool(article_feed):
        return json.dumps({'error': "No results found on this topic or country for the keywords inserted"},
                          indent=2), 204
    return json.dumps(article_feed, indent=2), 200


if __name__ == "__main__":
    app.run(host='0.0.0.0')
