import json
import rdflib

import requests
from os import path, walk
from tqdm import tqdm
from urllib.request import urlopen

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/loc.ttl'

additionalFiles = ['/data/ttl/additional/zbzTypeLabels.trig']

# Look at all Turtle files
inputFiles = [path.join(root, name)
             for root, dirs, files in walk(ttlFolder)
             for name in files
             if name.endswith((".ttl"))]

# Add additional files
inputFiles.extend(additionalFiles)

# Identify LOC identifiers by looking at triples where the object is a LCO identifier
locIdentifiers = []
for file in tqdm(inputFiles):
    if file.endswith('.trig'):
        g = rdflib.Dataset()
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?loc WHERE {
            GRAPH ?g {
                ?s ?p ?loc .
            }
            FILTER(REGEX(STR(?loc),"http://id.loc.gov/"))
        }""")
    else:
        g = rdflib.Graph()
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?loc WHERE {
            ?s ?p ?loc .
            FILTER(REGEX(STR(?loc),"http://id.loc.gov/"))
        }""")
    for row in queryResults:
        locIdentifiers.append(str(row[0]))

# Filter non-unique valeus
locIdentifiers = list(set(locIdentifiers))

# Clear output file
with open(ttlOutput, 'w') as outputFile:
    outputFile.write('')
    outputFile.close()
    
# Retrieve ttl data from loc and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for identifier in tqdm(locIdentifiers):
        url = "%s.nt" % identifier
        try:
            firstRequest = requests.get(url)
            # Follow redirect
            secondRequest = requests.get(firstRequest.url)
            outputFile.write(secondRequest.text + "\n")
            outputFile.flush()
        except:
            print("Could not retrieve", url)

    outputFile.close()
