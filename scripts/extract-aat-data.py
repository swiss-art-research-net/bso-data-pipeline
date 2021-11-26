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
        print("retrieve", url)
        r = requests.get(url, allow_redirects=True)
        print(r.url)
        # except:
        #     print("Could not retrieve", url)
        # print(r.content)

    outputFile.close()
