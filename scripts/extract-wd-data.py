import json
import urllib.request
import rdflib
import time

from os import path, walk
from SPARQLWrapper import SPARQLWrapper, N3
from tqdm import tqdm

ttlFolder='/data/ttl/main/'
ttlOutput='/data/ttl/additional/wd.ttl'
batchSizeForRetrieval = 100
wdEndpoint = "https://query.wikidata.org/sparql"
agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"

# Read the output file and query for existing URIs
existingIdentifiers = []
if path.exists(ttlOutput):
    wdData = rdflib.Graph()
    wdData.load(ttlOutput, format='turtle')
    queryResults = wdData.query("""
    SELECT DISTINCT ?s WHERE {
        ?s ?p ?o .
        FILTER(REGEX(STR(?s),"http://www.wikidata.org/entity/"))
    }
    """)
    for row in queryResults:
        existingIdentifiers.append(str(row[0]))

# Look at all Turtle files
inputFiles = [path.join(root, name)
             for root, dirs, files in walk(ttlFolder)
             for name in files
             if name.endswith((".ttl"))]

# Identify WD identifiers by looking at triples where the object is a WD identifier
wdIdentifiers = []
for file in tqdm(inputFiles):
    g = rdflib.Graph()
    g.parse(file, format='ttl')
    queryResults = g.query(
    """SELECT DISTINCT ?wd WHERE {
        ?s ?p ?wd .
        FILTER(REGEX(STR(?wd),"http://www.wikidata.org/entity/"))
    }""")
    for row in queryResults:
        wdIdentifiers.append(str(row[0]))

# Filter non-unique valeus
wdIdentifiers = list(set(wdIdentifiers))

# Filter out existing identifiers
wdIdentifiersToRetrieve = [x for x in wdIdentifiers if x not in existingIdentifiers]

# Report on the number of identifiers in the data, already retrieved and yet to retrieve
print("Total number of Wikidata identifiers: {}".format(len(wdIdentifiers)))
print("Total number of Wikidata identifiers already retrieved: {}".format(len(existingIdentifiers)))
print("Total number of Wikidata identifiers to retrieve: {}".format(len(wdIdentifiersToRetrieve)))

# Add function to loop through list in chunks
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

# Retrieve relevant data from Wikidata and append to ttl file

sparql = SPARQLWrapper(wdEndpoint, agent=agent)    

with open(ttlOutput, 'a') as outputFile:
    for batch in tqdm(chunker(wdIdentifiersToRetrieve, batchSizeForRetrieval)):
        query = """
             PREFIX wdt: <http://www.wikidata.org/prop/direct/>
             CONSTRUCT {
                 ?entity wdt:P625 ?coordinates ;
                    wdt:P18 ?image .
             } WHERE {
                 {
                    ?entity wdt:P625 ?coordinates .
                 } UNION {
                     ?entity wdt:P18 ?image .
                 }
                 VALUES (?entity) {
                     %s
                 }
             }

        """ % ( "(<" + ">)\n(<".join(batch) + ">)" )
        sparql.setQuery(query)
        try:
            results = sparql.query().convert()
        except urllib.error.HTTPError as exception:
            print(exception)
        time.sleep(3)
        outputFile.write(results.serialize(format='turtle'))