import os
import fileinput

directory = "awesome-rss-feeds/countries/without_category/"

for file in os.listdir(directory):
    for line in fileinput.input(directory + str(file), inplace=True, encoding="utf8"):
        print('{}'.format(line.replace("&", "&amp;")), end='')
