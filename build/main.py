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
import lxml.etree as le

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
    """
    Main endpoint of the API, to obtain set of articles from different sources.

        These following arguments must come on a POST request. ONLY keywords is required. Everything else fall into
        the default values if missing.
        keywords = Keywords that must appear in the news title or summary. For multiple separate by semicolon.
        domains = General domain that news must belong too. For multiple separate by semicolon.
            default value -> None
        time_frame = Time constraint that limits the age of the news articles
            default value -> 1d (24 hours)
        initial_date = Initial constraint that limits the publishing time of the articles
            default value -> None
        final_date = Ending constraint that limits the publishing time of the articles
            default value -> None or Current date if initial date was given
        themes = General theme of the articles
            default value -> None
        number_articles = Maximum number of articles
            default value -> 250
        language = Language that the news are in
            default value -> English (United States) - en-us
        countries = Countries where the articles are reported from
            default value -> Germany
    :return: Set of news articles in JSON format with these fields: title,url, timestamp,source,country name in alpha 3
    and country name.
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    keywords = request.json.get('keywords')
    domains = request.json.get('domains')
    time_frame = request.json.get('time_frame')
    initial_date = request.json.get('initial_date')
    final_date = request.json.get('final_date')
    themes = request.json.get('themes')
    number_articles = int(request.json.get('number_articles')) if request.json.get('number_articles') else 0
    language = request.json.get('language')
    countries = request.json.get('countries')

    # Setting of default values
    language = language if language else DEFAULT_LANGUAGE
    countries = countries if countries else DEFAULT_COUNTRY

    if not keywords:
        return json.dumps({'error': 'Missing keywords for the search'}, indent=2), 400

    # If neither time frame or initial date is given it will be given the default value and time_frame takes priority
    if not time_frame and not initial_date:
        time_frame = time_frame if time_frame else DELAULT_TRIME_FRAME
    elif not time_frame and initial_date:
        initial_date = dateparser.parse(initial_date).replace(tzinfo=pytz.utc)
        if final_date:
            final_date = dateparser.parse(final_date).replace(tzinfo=pytz.utc)
            # Checking that the final date is not earlier than the initial date
            if final_date < initial_date:
                return json.dumps({'error': 'Contrasting date ranges, make sure they are ordered correctly with time.'}
                                  , indent=2), 400
        # The final date defaults to current date if not specified
        else:
            final_date = datetime.now(pytz.utc)

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
                    return json.dumps(
                        {'error': "No results found on this country, please verify the code or name of it"},
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
                              ".opml. The URL rasing this error is: " + item.xmlUrl)
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

                            timestamp = dateparser.parse(entry.published)
                            # Checking for time_frame constraint
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
                            # Checking for the time interval
                            else:
                                # Making sure the timestamp from the feed is timezone aware, else it can't be compared
                                if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
                                    timestamp = timestamp.replace(tzinfo=pytz.utc)

                                if not (initial_date < timestamp < final_date):
                                    continue

                            if number_articles > 0 and article_counter >= limit_number_articles:
                                break
                            article_counter += 1
                            if "*" in entry.link:
                                article_feed.append(
                                    {"title": entry.title, "url": entry.link.split("*")[1],
                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "source": SOURCES[0], "country_alpha_3": country.alpha_3,
                                     "country_name": country.name})
                            else:
                                article_feed.append({"title": entry.title, "url": entry.link,
                                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                                     "source": SOURCES[0], "country_alpha_3": country.alpha_3,
                                                     "country_name": country.name})
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
                timespan=time_frame if time_frame else None,
                start_date=initial_date.strftime("%Y-%m-%d") if not time_frame else None,
                end_date=final_date.strftime("%Y-%m-%d") if not time_frame else None,
                domain=domains,
                country=country.name if not is_exception else json_exceptions[country.name],
                theme=themes,
                num_records=limit_number_articles if number_articles > 0 else 250
            )

            resulting_articles = GdeltDoc().article_search(gdelt_filters)

            # Iterating through the articles from the Gdelt after applying the filters, if there are any
            for index_row, row in resulting_articles.iterrows():
                # Checking for language constraint
                if language != "" and row.language.lower() != language_gdelt.lower():
                    continue
                timestamp = dateparser.parse(date_string=row.seendate,
                                             date_formats=["%Y%m%dT%H%M%SZ"])

                article_feed.append({"title": row.title, "url": row.url,
                                     "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": SOURCES[1],
                                     "country_alpha_3": country.alpha_3, "country_name": country.name})
        except ValueError:
            print("Invalid or Unsupported Country: '" + country.name + "'.Please check the documentation.")

    if not bool(article_feed):
        return json.dumps({'error': "No results found on this topic or country for the keywords inserted"},
                          indent=2), 204
    return json.dumps(article_feed, indent=2), 200


@app.route('/get_country_names_exceptions', methods=['GET'])
def get_country_names_exceptions():
    """
        Obtains the list of current exceptions for country names.

    :return: List of all the exceptions, in JSON format
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    return json.dumps(json.load(open("exceptions.json"))['countries_names'], indent=2), 200


@app.route('/update_country_names_exceptions', methods=['POST'])
def update_country_names_exceptions():
    """
        Adds, updates or deletes a name exception for a country.
        If the exception does not exist it will be added. If it exists and a value was give it will be updated.
        If it exists and no value was given it will be deleted.

    :return: JSON formatted result. If the exception was deleted it will be an object with the key "deleted_exception".
    If it was added or updated it will return an object with the exception created.
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    country = request.json.get('country')
    exception = request.json.get('exception')

    try:
        country_iso = pycountry.countries.get(name=country)
        if not country_iso:
            country = pycountry.countries.get(alpha_3=country)
            if not country:
                return json.dumps(
                    {'error': "No results found on this country, please verify the code or name of it"},
                    indent=2), 404
        else:
            country = country_iso
    except ValueError:
        return json.dumps({'error': "No results found on this country, please verify the code or name of it"},
                          indent=2), 404

    json_exceptions = json.load(open("exceptions.json"))['countries_names']
    is_in_exception = country.name in json_exceptions

    with open('exceptions.json', 'r+') as f:
        if is_in_exception:
            json_exceptions.pop(country.name)
            if exception != '':
                json_exceptions[country.name] = exception
        else:
            if exception == '':
                return json.dumps({'error': "To set up an exception you must send the exception field, an empty value"
                                            " was sent."},
                                  indent=2), 404
            json_exceptions[country.name] = exception
        data = json.load(f)
        data['countries_names'] = json_exceptions
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    if is_in_exception and exception == '':
        return json.dumps({"deleted_exception": country.name}, indent=2), 200
    return json.dumps({country.name: exception}, indent=2), 200


@app.route('/add_elem_rss_library', methods=['POST'])
def add_elem_rss_library():
    """
    Adds or updates the entries of the library RSS Feeds from the countries sent
    :return: list of successes and errors, logging of the modifications
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401
    errors = []
    successes = []
    modifications = request.json.get('modifications')
    for modification in modifications:
        country = modification["country"]
        current_sent_country = country
        try:
            country_iso = pycountry.countries.get(name=country)
            if not country_iso:
                country = pycountry.countries.get(alpha_3=country)
                if not country:
                    errors.append({'country_name_sent': current_sent_country})
                    continue
            else:
                country = country_iso
            if country.name not in country_files:
                errors.append({'country_name_sent': country.name})
                continue
        except ValueError:
            errors.append({'country_name_sent': current_sent_country})
            continue
        elements = modification["elements"]
        for element in elements:
            url = element['url']
            if not url:
                errors.append({'country': country.name, 'error': "missing URL"})
                continue
            title = element['title']
            description = element['description']
            xml_string = None
            with open(file_dir_countries + country.name + ".opml", 'r') as f:
                doc = le.parse(f)
                parent = None
                xml_elements = doc.xpath('//*[attribute::xmlUrl]')
                for elem in xml_elements:
                    if not parent:
                        parent = elem.getparent()
                    if elem.attrib['xmlUrl'] == url:
                        parent.remove(elem)
                        break
                parent.insert(len(xml_elements) + 1, le.Element("output", text="", title=title, description=description,
                                                                xmlUrl=url, type="rss"))
                le.indent(doc)
                xml_string = le.tostring(doc, pretty_print=True)
            with open(file_dir_countries + country.name + ".opml", "wb") as output_file:
                output_file.write(xml_string)
                successes.append({'country': country.name, 'title': title, 'description': description, 'url': url})
    if successes:
        return json.dumps({'errors': errors, 'successes': successes}, indent=2), 200
    else:
        return json.dumps({'errors': errors}, indent=2), 400


@app.route('/remove_elem_rss_library', methods=['POST'])
def remove_elem_rss_library():
    """
    It removes the entries of the libraries feeds from the countries sent.
    :return: list of success and errors, logging the deletion process
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    errors = []
    successes = []
    deletions = request.json.get('deletions')
    for deletions in deletions:
        country = deletions["country"]
        current_sent_country = country
        try:
            country_iso = pycountry.countries.get(name=country)
            if not country_iso:
                country = pycountry.countries.get(alpha_3=country)
                if not country:
                    errors.append({'country_name_sent': current_sent_country})
                    continue
            else:
                country = country_iso
            if country.name not in country_files:
                errors.append({'country_name_sent': country.name})
                continue
        except ValueError:
            errors.append({'country_name_sent': current_sent_country})
            continue
        elements = deletions["elements"]
        for url in elements:
            deleted_element = None
            xml_string = None
            with open(file_dir_countries + country.name + ".opml", 'r') as f:
                doc = le.parse(f)
                for elem in doc.xpath('//*[attribute::xmlUrl]'):
                    if elem.attrib['xmlUrl'] == url:
                        deleted_element = elem
                        parent = elem.getparent()
                        parent.remove(elem)
                        le.indent(doc)
                        xml_string = le.tostring(doc, pretty_print=True)
                        break
            if deleted_element is not None:
                with open(file_dir_countries + country.name + ".opml", "wb") as output_file:
                    output_file.write(xml_string)
                successes.append({"country": country.name, "title": deleted_element.attrib['title'],
                                  "description": deleted_element.attrib['description'],
                                  "url": deleted_element.attrib['xmlUrl']})
            else:
                successes.append({"country": country.name, "url": url, "status": "previously deleted"})
    if successes:
        return json.dumps({'errors': errors, 'successes': successes}, indent=2), 200
    else:
        return json.dumps({'errors': errors}, indent=2), 400


@app.route('/get_rss_library', methods=['POST'])
def get_rss_library():
    """
    Iterates over the whole library of RSS Feeds of the country sent and returns it
    :return: list of RSS feeds as objects with the basic information
    """
    if 'key' not in request.json or request.json.get('key') != REQUEST_KEY:
        return json.dumps({'error': 'no valid API key'}, indent=2), 401

    country = request.json.get('country')

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

    if country.name in country_files:
        try:
            feeds = []
            for item in opml.parse(file_dir_countries + country.name + ".opml"):
                feeds.append({"title": item.title, "description": item.description, "url": item.xmlUrl})
            return json.dumps(feeds, indent=2), 200
        except XMLSyntaxError:
            print("Error on XML file for RSS links : " + file_dir_countries + country.name + ".opml")
    else:
        return json.dumps({'error': "No results found on this country, please verify the code or name of it. If this"
                                    "is expected please create the library for this country."},
                          indent=2), 204


if __name__ == "__main__":
    app.run(host='0.0.0.0')
