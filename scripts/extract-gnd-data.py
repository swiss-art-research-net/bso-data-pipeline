import json
import rdflib

from urllib import request
from os import path, walk
from tqdm import tqdm

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/gnd.ttl'

additionalFiles = [] # Additional files that should be scanned can be added here

# Read the output file and query for existing URIs
existingIdentifiers = []
if path.exists(ttlOutput):
    gndData = rdflib.Graph()
    gndData.load(ttlOutput, format='turtle')
    queryResults = gndData.query("""
    PREFIX gndo:  <https://d-nb.info/standards/elementset/gnd#>
    SELECT DISTINCT ?gnd WHERE {
        ?gnd a gndo:AuthorityResource .
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

# Identify GND identifiers by looking at triples where the object is  a GND identifier
gndIdentifiers = []

for file in tqdm(inputFiles):
    if file.endswith('.trig'):
        g = rdflib.Dataset() 
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?gnd WHERE {
            GRAPH ?g {
                ?s ?p ?gnd .
            }
            FILTER(REGEX(STR(?gnd),"https://d-nb.info/gnd/"))
        }""")
    else:
        g = rdflib.Graph() 
        g.parse(file)
        queryResults = g.query(
        """SELECT DISTINCT ?gnd WHERE {
            ?s ?p ?gnd .
            FILTER(REGEX(STR(?gnd),"https://d-nb.info/gnd/"))
        }""")
    for row in queryResults:
        gndIdentifiers.append(str(row[0]))

# Filter non-unique valeus
gndIdentifiers = list(set(gndIdentifiers))

# Remove existing identifiers from the list
gndIdentifiersToQuery = [d for d in gndIdentifiers if d not in existingIdentifiers]

# Report on the number of identifiers in the data, already retrieved and yet to retrieve
print("Total number of GND identifiers in the data: " + str(len(gndIdentifiers)))
print("Total number of GND identifiers already retrieved: " + str(len(existingIdentifiers)))
print("Total number of GND identifiers to retrieve: " + str(len(gndIdentifiersToQuery)))

# Retrieve ttl data from GND and append to ttl file
with open(ttlOutput, 'a') as outputFile:
    for identifier in tqdm(gndIdentifiersToQuery):
        url = "%s.ttl" % identifier.replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
        try:
            with request.urlopen(url) as r:
                content = r.read().decode()
            outputFile.write(content + "\n")
            outputFile.flush()
        except:
            print("Could not retrieve", url)

    outputFile.close()
