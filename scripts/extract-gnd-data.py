import json
import rdflib

from urllib import request
from os import listdir

ttlFolder='/output/'
ttlOutput='/output/gnd.ttl'

# Look at all Turtle files
inputFiles = []
for file in listdir(ttlFolder):
    if file.endswith('.ttl'):
        inputFiles.append(file)

# Identify GND identifiers by looking at triples where the object is  a GND identifier
gndIdentifiers = []
for file in inputFiles:
    g = rdflib.Graph()
    g.parse(ttlFolder + file, format='ttl')
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
    
# Retrieve ttl data from GND and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for row in queryResults:
        url = "%s.ttl" % row[0].replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
        try:
            with request.urlopen(url) as r:
                content = r.read().decode()
            outputFile.write(content + "\n")
        except:
            print("Could not retrieve", url)