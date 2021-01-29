import json
import rdflib

from urllib import request
from os import path, walk
from tqdm import tqdm

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/gnd.ttl'

# Look at all Turtle files
inputFiles = [path.join(root, name)
             for root, dirs, files in walk(ttlFolder)
             for name in files
             if name.endswith((".ttl"))]

# Identify GND identifiers by looking at triples where the object is  a GND identifier
gndIdentifiers = []
for file in tqdm(inputFiles):
    g = rdflib.Graph()
    g.parse(file, format='ttl')
    queryResults = g.query(
    """SELECT DISTINCT ?gnd WHERE {
        ?s ?p ?gnd .
        FILTER(REGEX(STR(?gnd),"https://d-nb.info/gnd/"))
    }""")
    for row in queryResults:
        gndIdentifiers.append(str(row[0]))

# Filter non-unique valeus
gndIdentifiers = list(set(gndIdentifiers))

# Clear output file
with open(ttlOutput, 'w') as outputFile:
    outputFile.write('')
    outputFile.close()
    
# Retrieve ttl data from GND and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for identifier in tqdm(gndIdentifiers):
        url = "%s.ttl" % identifier.replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
        try:
            with request.urlopen(url) as r:
                content = r.read().decode()
            outputFile.write(content + "\n")
            outputFile.flush()
        except:
            print("Could not retrieve", url)

    outputFile.close()
