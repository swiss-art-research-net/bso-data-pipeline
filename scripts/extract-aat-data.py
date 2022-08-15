import json
import rdflib

import requests
from os import path, walk
from tqdm import tqdm
from urllib.request import urlopen

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/aat.ttl'

additionalFiles = [] # Additional files that should be scanned can be added here


# Read the output file and query for existing URIs
existingIdentifiers = []
if path.exists(ttlOutput):
    aatData = rdflib.Graph()
    aatData.load(ttlOutput, format='turtle')
    queryResults = aatData.query("""
    PREFIX gbp:  <http://vocab.getty.edu/ontology#>
    SELECT DISTINCT ?aat WHERE {
        ?aat a gvp:Concept .
    }
    """)
    for row in queryResults:
        existingIdentifiers.append(str(row[0]))

# Look at all Turtle files
inputFiles = [path.join(root, name)
             for root, dirs, files in walk(ttlFolder)
             for name in files
             if name.endswith((".ttl"))]

# Add additional files
inputFiles.extend(additionalFiles)

# Identify AAT identifiers by looking at triples where the object is a AAT identifier
aatIdentifiers = []
for file in tqdm(inputFiles):
    if file.endswith('.trig'):
        g = rdflib.Dataset()
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?aat WHERE {
            GRAPH ?g {
                ?s ?p ?aat .
            }
            FILTER(REGEX(STR(?aat),"http://vocab.getty.edu/aat/"))
        }""")
    else:
        g = rdflib.Graph()
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?aat WHERE {
            ?s ?p ?aat .
            FILTER(REGEX(STR(?aat),"http://vocab.getty.edu/aat/"))
        }""")
    for row in queryResults:
        aatIdentifiers.append(str(row[0]))

# Filter non-unique valeus
aatIdentifiers = list(set(aatIdentifiers))

# Filter existing values
aatIdentifiersToRetrieve = list(set(aatIdentifiers) - set(existingIdentifiers))

# Report on the number of identifiers in the data, already retrieved and yet to retrieve
print("Total number of AAT identifiers: " + str(len(aatIdentifiers)))
print("Total number of AAT identifiers already retrieved: " + str(len(existingIdentifiers)))
print("Total number of AAT identifiers to retrieve: " + str(len(aatIdentifiersToRetrieve)))

# Retrieve ttl data from aat and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for identifier in tqdm(aatIdentifiersToRetrieve):
        url = "%s.ttl" % identifier
        try:
            firstRequest = requests.get(url)
            # Follow redirect
            secondRequest = requests.get(firstRequest.url)
            outputFile.write(secondRequest.text + "\n")
            outputFile.flush()
        except:
            print("Could not retrieve", url)

    outputFile.close()
