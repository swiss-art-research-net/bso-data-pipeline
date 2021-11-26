import json
import rdflib

import requests
from os import path, walk
from tqdm import tqdm
from urllib.request import urlopen

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/aat.ttl'

# Look at all Turtle files
inputFiles = [path.join(root, name)
             for root, dirs, files in walk(ttlFolder)
             for name in files
             if name.endswith((".ttl"))]

# Identify AAT identifiers by looking at triples where the object is a AAT identifier
aatIdentifiers = []
for file in tqdm(inputFiles):
    g = rdflib.Graph()
    g.parse(file, format='ttl')
    queryResults = g.query(
    """SELECT DISTINCT ?aat WHERE {
        ?s ?p ?aat .
        FILTER(REGEX(STR(?aat),"http://vocab.getty.edu/aat/"))
    }""")
    for row in queryResults:
        aatIdentifiers.append(str(row[0]))

# Filter non-unique valeus
aatIdentifiers = list(set(aatIdentifiers))

# Clear output file
with open(ttlOutput, 'w') as outputFile:
    outputFile.write('')
    outputFile.close()
    
# Retrieve ttl data from aat and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for identifier in tqdm(aatIdentifiers):
        url = "%s.ttl" % identifier
        try:
            r = requests.get(url)
        except:
            print("Could not retrieve", url)
        for i in r.history:
            print(url,i.url)
            # with urlopen(i.url) as redirectedRequest:
            #     content = redirectedRequest.read().decode()
            # outputFile.write(content + "\n")
            # outputFile.flush()
            # break

    outputFile.close()
