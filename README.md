# Feeds
## _News articles API_

[![Coypu](https://pbs.twimg.com/profile_banners/1421069821723267072/1641392854/1500x500)](https://coypu.org/)

This is a simple API that gather news articles from several sources and returns them according to multiple filters. Currently, the sources of these feeds are:
- RSS Feeds (Feed library initialized by [Awesome RSS Feeds](https://github.com/plenaryapp/awesome-rss-feeds) GitHub )
- [The GDELT Project](https://blog.gdeltproject.org/)

## API Call

The API can be accessed through a *POST* call to the url *https://feeds.skynet.coypu.org*. The call must always be accompanied by the parameter **key** in its body, which value must be the correct password. The call can be made with the following filters:
| Filter | Usage | Example | Defaul value |Required? |
| ------ | ------ |  ------ |  ------ |  ------ 
| keywords | Keywords that must appear in the news title or summary. **For multiple separate by semicolon.** | Floods in |  | ✅  
| domains | General domain that news must belong too. **For multiple separate by semicolon.** | www.dw.com | None |
| time_frame | Time constraint that limits the age of the news articles | 1h (more info ⬇️) |  1d ie. 24 hours
| initial_date | Initial constraint that limits the publishing time of the articles.  | 2023-04-20 (more info ⬇️) |  None
| final_date | Ending constraint that limits the publishing time of the articles | 2023-05-20 (more info ⬇️) |  Current date
| themes | General theme of the articles. **For multiple separate by semicolon.** | Political |  None |
| number_articles | Maximum number of articles | 10 | 250  |
| language | Language that the news are in | German (Germany) - de-de (more info ⬇️)  | English (United States) - en-us |
| countries | Countries where the articles are reported from. [Alpha-3 from ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) is allowed. The names of the countries are also taken from that standard.  **For multiple separate by semicolon.** | GER;Canada | Germany  |

For example the call
```
https://feeds.skynet.coypu.org?keywords=War in
```
returns the articles reported the last 24 hours in Germany in English (United States) that has the keyword "War in" in either their title or summary.

And the call

```
https://feeds.skynet.coypu.org?countries=Canada&language=English (Canada) - en-ca&keywords=Food inflation&time_frame=1w
```

returns the articles that were reported in Canada for the last week with the keywords "Food inflation", in Canadian English.

## API Answer
The response of the API will be a JSON array with the different articles found. Each item has the following fields:
- title - Tittle of the news article
- url - URL link where the article can be found
- timestamp - Time formatted as ```%Y-%m-%dT%H:%M:%SZ``` according to the [Python datetime library](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). **The timezone is UTC.**
- source - Source from where the news was taken. **Currently, it can only be either "RSS" or "GDELT"**
- country_name - Name of the country the article originate from, for human readable reasons
- country_alpha_3 - Code [Alpha-3 from ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) of the country the article came from

## Exceptions
Due to discrepancies in the libraries and standards used from the sources a JSON file for exceptions has been introduced, called "exceptions.json".
It is currently mainly used for the discrepancies between the countries from [ISO 3166](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) and [FIPS 10-4](https://en.wikipedia.org/wiki/List_of_FIPS_country_codes) used by GDELT.
Only the discrepancies that have been manually found are added, so it is a growing file.

## More info on filters

The filter **time_frame** can take these following values:
- 1h - One hour
- 1d - One day, that is the last 24 hours
- 1w - One week, that is the last 7 days
- 15m - 15 minutes

The filters **initial_date** and **final_date** expect the format ```%Y-%m-%d``` according to the [Python datetime library](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).  **The timezone is UTC.** This range is inclusive only in the initial_date side, it excludes the latest date in the final_date side. For example the values
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