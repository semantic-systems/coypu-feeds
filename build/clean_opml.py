import os
import fileinput

directory = "{0}/rss-feeds/countries/".format(os.getcwd())

for file in os.listdir(directory):
    for line in fileinput.input(directory + str(file), inplace=True, encoding="utf8"):
        print('{}'.format(line.replace("&", "&amp;")), end='')
