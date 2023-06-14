# Feeds
## _News articles API_

[![Coypu](https://pbs.twimg.com/profile_banners/1421069821723267072/1641392854/1500x500)](https://coypu.org/)

This is a simple API that gathers news articles from several sources and returns them according to multiple filters. Currently, the sources of these feeds are:
- RSS Feeds (Feed library initialized by [Awesome RSS Feeds](https://github.com/plenaryapp/awesome-rss-feeds) GitHub )
- [The GDELT Project](https://blog.gdeltproject.org/)

All the calls must always be accompanied by the parameter **key**, the value must be the correct password. **In all the calls the parameters are sent in the body in a JSON format unless indicated otherwise.**

## Main Endpoint Call

The API can be accessed through a **POST** call to the URL ```https://feeds.skynet.coypu.org```. The call can be made with the following filters:
| Filter | Usage | Example | Default value |Required? |
| ------ | ------ |  ------ |  ------ |  ------ 
| keywords | Keywords that must appear in the news title or summary. **For multiple separate by semicolon.** | Floods in |  | ✅  
| domains | General domain that news must belong to. **For multiple separate by semicolon.** | www.dw.com | None |
| time_frame | Time constraint that limits the age of the news articles | 1h (more info ⬇️) |  1d ie. 24 hours
| initial_date | Initial constraint that limits the publishing time of the articles.  | 2023-04-20 (more info ⬇️) |  None
| final_date | Ending constraint that limits the publishing time of the articles | 2023-05-20 (more info ⬇️) |  Current date
| themes | General theme of the articles. **For multiple separate by semicolon.** | Political |  None |
| number_articles | Maximum number of articles | 10 | 250  |
| language | Language that the news are in | German (Germany) - de-de (more info ⬇️)  | English (United States) - en-us |
| countries | Countries where the articles are reported from. [Alpha-3 from ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) is allowed. The names of the countries are also taken from that standard.  **For multiple separate by semicolon.** | GER;Canada | Germany  |

For example the call to the URL with the body:
```
{
    "key" : "VD3WRN6RE2VM2ACJ",
    "keywords": "War in"
}
```
returns the articles reported the last 24 hours in Germany in English (United States) that have the keyword "War in" in either their title or summary.

And the call with the body:

```
{
    "key" : "VD3WRN6RE2VM2ACJ",
    "countries":"Canada", 
    "language":"English (Canada) - en-ca",
    "keywords":"Food inflation",
    "time_frame":"1w"
}
```

returns the articles that were reported in Canada for the last week with the keywords "Food inflation", in Canadian English.

## Main Endpoint Answer
The response of the API will be a JSON array with the different articles found. Each item has the following fields:
- title - Tittle of the news article
- url - URL link where the article can be found
- timestamp - Time formatted as ```%Y-%m-%dT%H:%M:%SZ``` according to the [Python datetime library](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **The time zone is UTC.**
- source - Source from where the news was taken. **Currently, it can only be either "RSS" or "GDELT"**
- country_name - Name of the country the article originates from, for human readable reasons
- country_alpha_3 - Code [Alpha-3 from ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) of the country the article came from

## Exceptions
Due to discrepancies in the libraries and standards used from the sources a JSON file for exceptions has been introduced, called "exceptions.json".
It is currently mainly used for the discrepancies between the countries from [ISO 3166](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) and [FIPS 10-4](https://en.wikipedia.org/wiki/List_of_FIPS_country_codes) used by GDELT.
Only the discrepancies that have been manually found are added, so it is a growing file. 

### Exceptions for Name of Country 

#### Listing
The endpoint on ```/get_country_names_exceptions``` can be used to check the current exceptions that the file holds. This call must be done with the **GET** protocol, no parameters are necessary.

The **answer** would be given as a list of the exception in the body of the response. Like so:
```
{
    "Russian Federation": "Russia",
    "Iran, Islamic Republic of": "Iran",
    "United States": "US"
}
```

#### Adding, Updating and Deleting
Due to the current architecture deployment, the actions taken with these endpoints are only **temporary**. For permanent action, please create an issue request.

To add, update or delete exception once can use the endpoint on ```/update_country_names_exceptions```. This call must be done with the **POST** protocol with the following parameters:
- country - Name of the country to add exception to, must be the name indicated in [ISO 3166](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes)
- exception - Term that is recognized by GDELT (discrepancies have been found between the names they say they have and the ones they actually accept)

To **add or update** an exception simply send both parameters, if the exception exist it will be updated if not it will be created. 
If the exception is correctly processed it returns the exception added:
```
{
    "Guatemala": "GT"
}
```
To **delete** an exception one must simply send an empty string for the exception field. If the exception is correctly deleted the response will have an object with the key "deleted_exception". For example:
```
{
    "deleted_exception": "Guatemala"
}
```

### RSS Feeds Library Maintenance 
The RSS Feeds libraries are a set of XML files with the different RSS feeds for each country. The following endpoints allow the general maintenance of them: 

#### Listing
To get all the feeds from a country one must use the endpoint ```/get_rss_library```. The call must be executed with the POST protocol indicating which country one wants to see, the parameter must be called ```country```. For example, requesting the listing of the country of Canada, can return the following:

```
[
    {
        "title": "CTVNews.ca - Top Stories - Public RSS",
        "description": "Latest news from CTVNews.ca",
        "url": "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009"
    },
    {
        "title": "National Post",
        "description": "Canadian News, World News and Breaking Headlines",
        "url": "https://nationalpost.com/feed/"
    }, 
]
```
### Removing, Adding and Updating
Due to the current architecture deployment, the actions taken with these endpoints are only **temporary**. For permanent action, please create an issue request.

The endpoint to remove feeds is ```/remove_elem_rss_library``` and the one for adding and updating is allocated to ```/add_elem_rss_library```. Both calls must be executed on **POST**. To remove it is necessary to send an array named ```deletions``` and to update it must be named ```modifications```. Each item of these arrays must have the parameter ```country``` and the array ```elements```. Multiple elements can be removed, added or updated from multiple countries.

The response of these endpoints are two arrays, called ```errors``` and ```successes```. They explained what was successfully processed and what not and what was the reason. If the ```successes``` array is missing it means nothing was able to be processed correctly.

#### Adding and Updating
The elements of the ```elements``` array must have these parameters:
- **url**: Link of the RSS feed, for example: ```https://rss.dw.com/rdf/rss-en-all```
- tittle (optional): Tittle of the entry, for easier understanding and readability.
- description (optional): Description of the entry, for easier understanding and readability.

These are the values of the entry that is to be added to the country's library. If an entry wants to be updated **it must match the url**, the other values will be overwritten. An example of the body of a call is the following:
```
{
"modifications" :
    [
        {
            "country" :  "United States",
            "elements" : [
                {
                    "url":"https://www.cnbc.com/id/100003114/device/rss/rss.html", 
                    "title":"US Top News and Analysisss",
                    "description":"CNBC is the world leader in business news and real-time financial market coverage."
                },
                {
                    "url":"https://feeds.a.dj.com/rss/RSSWorldNews.xml", 
                    "title":"Deutsche Welle",
                    "description":"Deutsche Welle"
                }
            ]
        }
    ]
}
```

#### Removing
The ```deletions``` array is a list of the URLs of the entries that are to be deleted from the country's library. For example this call can be made:
```
{
"deletions" :
    [
        {
            "country" :  "United States",
            "elements" : [
                "https://rss.dw.com/rdf/rss-en-all",
                "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
            ]
        },
        {
            "country" :  "Germany",
            "elements" : [
                "https://www.cnbc.com/id/100003114/device/rss/rss.html"
            ]
        }
    ]
}
```

## More info on filters

The filter **time_frame** can take these following values:
- 1h - One hour
- 1d - One day, that is the last 24 hours
- 1w - One week, that is the last 7 days
- 15m - 15 minutes

The filters **initial_date** and **final_date** expect the format ```%Y-%m-%d``` according to the [Python datetime library](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).  **The time zone is UTC.** This range is inclusive only in the initial_date side, it excludes the latest date in the final_date side. For example the values
- initial_date: 2023-04-20 
- final_date: 2023-04-25

The system will return the articles published between the first second of 2023-04-20 and midnight of 2023-04-24.

If the final_date filter is not given it defaults to the current date. However, if the initial_date filter is missing the **time_frame** filter will be taking priority **even** if the final_date value has ben sent. If both filters are given but the initial_date is later than the final_date it will be returning an error.

The filter **language** comes from the [official collection of languages from the RSS standard](https://www.rssboard.org/rss-language-codes). So the filter must be one of the following (sent in the exact form):
- Afrikaans - af
- Albanian - sq
- Basque - eu
- Belarusian - be
- Bulgarian - bg
- Catalan - ca
- Chinese (Simplified) - zh-cn
- Chinese (Traditional) - zh-tw
- Croatian - hr
- Czech - cs
- Danish - da
- Dutch - nl
- Dutch (Belgium) - nl-be
- Dutch (Netherlands) - nl-nl
- English - en
- English (Australia) - en-au
- English (Belize) - en-bz
- English (Canada) - en-ca
- English (Ireland) - en-ie
- English (Jamaica) - en-jm
- English (New Zealand) - en-nz
- English (Phillipines) - en-ph
- English (South Africa) - en-za
- English (Trinidad) - en-tt
- English (United Kingdom) - en-gb
- English (United States) - en-us
- English (Zimbabwe) - en-zw
- Estonian - et
- Faeroese - fo
- Finnish - fi
- French - fr
- French (Belgium) - fr-be
- French (Canada) - fr-ca
- French (France) - fr-fr
- French (Luxembourg) - fr-lu
- French (Monaco) - fr-mc
- French (Switzerland) - fr-ch
- Galician - gl
- Gaelic - gd
- German - de
- German (Austria) - de-at
- German (Germany) - de-de
- German (Liechtenstein) - de-li
- German (Luxembourg) - de-lu
- German (Switzerland) - de-ch
- Greek - el
- Hawaiian - haw
- Hungarian - hu
- Icelandic - is
- Indonesian - in
- Irish - ga
- Italian - it
- Italian (Italy) - it-it
- Italian (Switzerland) - it-ch
- Japanese - ja
- Korean - ko
- Macedonian - mk
- Norwegian - no
- Polish - pl
- Portuguese - pt
- Portuguese (Brazil) - pt-br
- Portuguese (Portugal) - pt-pt
- Romanian - ro
- Romanian (Moldova) - ro-mo
- Romanian (Romania) - ro-ro
- Russian - ru
- Russian (Moldova) - ru-mo
- Russian (Russia) - ru-ru
- Serbian - sr
- Slovak - sk
- Slovenian - sl
- Spanish - es
- Spanish (Argentina) - es-ar
- Spanish (Bolivia) - es-bo
- Spanish (Chile) - es-cl
- Spanish (Colombia) - es-co
- Spanish (Costa Rica) - es-cr
- Spanish (Dominican Republic) - es-do
- Spanish (Ecuador) - es-ec
- Spanish (El Salvador) - es-sv
- Spanish (Guatemala) - es-gt
- Spanish (Honduras) - es-hn
- Spanish (Mexico) - es-mx
- Spanish (Nicaragua) - es-ni
- Spanish (Panama) - es-pa
- Spanish (Paraguay) - es-py
- Spanish (Peru) - es-pe
- Spanish (Puerto Rico) - es-pr
- Spanish (Spain) - es-es
- Spanish (Uruguay) - es-uy
- Spanish (Venezuela) - es-ve
- Swedish - sv
- Swedish (Finland) - sv-fi
- Swedish (Sweden) - sv-se
- Turkish - tr
- Ukranian - uk