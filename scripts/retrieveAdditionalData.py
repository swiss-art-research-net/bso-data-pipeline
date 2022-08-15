"""
Script to retrieve additional data based on identifiers found in the Turtle files in the given folder.
The sources that are queried and retrieved are specified in the sources parameter.
Currently, the following sources are supported:
- gnd: GND identifiers
- wd: Wikidata identifiers

Usage:
python retrieveAdditionalData.py --sourceFolder <sourceFolder> --targetFolder <targetFolder> --sources <sources>

sourceFolder: The folder where the Turtle files are stored.
targetFolder: The folder where the retrieved data will be stored.
sources: The sources to retrieve.
"""


import json
import requests
import sys

from rdflib import Graph
from urllib import request
from os import path, walk
from SPARQLWrapper import SPARQLWrapper, N3
from time import sleep
from tqdm import tqdm

PREFIXES = """
    PREFIX gvp:  <http://vocab.getty.edu/ontology#>
    PREFIX gndo:  <https://d-nb.info/standards/elementset/gnd#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    """

def retrieveData(options):

    def printStatus(status):
        if status['status'] == 'success':
            print(status['message'])
        else:
            print("Error:", status['message'])
            sys.exit(1)

    sourceFolder = options['sourceFolder']
    targetFolder = options['targetFolder']
    sources = options['sources']

    sourceIdentifiers = extractIdentifiers(sourceFolder, sources)

    if 'loc' in sourceIdentifiers and len(sourceIdentifiers['loc']) > 0:
        print("Retrieving LOC data")
        status = retrieveLocData(sourceIdentifiers['loc'], targetFolder)
        printStatus(status)

    if 'gnd' in sourceIdentifiers and len(sourceIdentifiers['gnd']) > 0:
        print("Retrieving GND data")
        status = retrieveGndData(sourceIdentifiers['gnd'], targetFolder)
        printStatus(status)

    if 'wd' in sourceIdentifiers and len(sourceIdentifiers['wd']) > 0:
        print("Retrieving Wikidata data")
        status = retrieveWdData(sourceIdentifiers['wd'], targetFolder)
        printStatus(status)
    
def extractIdentifiers(folder, sources):
    """
    Extracts the identifiers from the Turtle files in the given folder.
    The kind of identifiers that are extracted are specified in the sources parameter.

    :param folder: The folder where the Turtle files are stored.
    :param sources: The kind of identifiers that are extracted given as a list of strings.
    :return: A dictionary with the sources as keys and the list of distinct identifiers as value.
    """

    identifierQueries = {
        "aat": "?identifier a gvp:Concept .",
        "gnd": """
            ?s ?p ?identifier .
            FILTER(REGEX(STR(?identifier),"https://d-nb.info/gnd/"))
        """,
        "loc": """
            ?s ?p ?identifier .
            FILTER(REGEX(STR(?identifier),"http://id.loc.gov/"))
        """,
        "wd": """
            ?identifier ?p ?o .
            FILTER(REGEX(STR(?identifier),"http://www.wikidata.org/entity/"))
        """
    }

    identifiers = {}
    for source in sources:
        identifiers[source] = []

    files = [path.join(root, name)
             for root, dirs, files in walk(folder)
             for name in files
             if name.endswith((".ttl"))]
    
    for file in tqdm(files):
        g = Graph() 
        g.parse(file)
        for source in sources:
            query = PREFIXES + "SELECT DISTINCT ?identifier WHERE { " + identifierQueries[source] + " }"
            queryResults = g.query(query)
            for row in queryResults:
                identifiers[source].append(str(row[0]))
    
    return identifiers
    
def queryIdentifiersInFile(sourceFile, queryPart):
    """
    Queries the given file for identifiers and returns a list of the identifiers found.
    Expects a part of a SPARQL select query that is used in the WHERE clause that returns the identifier as ?identifier.
    
    :param sourceFile: The Turtle file to query.
    :param queryPart: A part of a SPARQL select query that is used in the WHERE clause that returns the identifier as ?identifier.
    :return: A list of the identifiers found.
    """
    identifiers = []
    if path.isfile(sourceFile):
        data = Graph()
        data.parse(sourceFile, format='turtle')
        queryResults = data.query("SELECT DISTINCT ?identifier WHERE {" + queryPart + "}")
        for row in queryResults:
            identifiers.append(str(row[0]))
    return identifiers

def retrieveGndData(identifiers, targetFolder):
    """
    Retrieves the data for the given identifiers and writes it to a file named gnd.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the LOBID API.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    targetFile = path.join(targetFolder, 'gnd.ttl')
    existingIdentifiers = queryIdentifiersInFile(targetFile, "?identifier a gndo:AuthorityResource .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(targetFile, 'a') as outputFile:
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.ttl" % identifier.replace("https://d-nb.info/gnd/","https://lobid.org/gnd/")
            try:
                with request.urlopen(url) as r:
                    content = r.read().decode()
                outputFile.write(content + "\n")
                outputFile.flush()
            except:
                print("Could not retrieve", url)
    return {
        "status": "success",
        "message": "Retrieved %d additional GND identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def retrieveLocData(identifiers, targetFolder):
    """
    Retrieves the data for the given identifiers and writes it to a file named loc.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Library of Congress API.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """
    # Read the output file and query for existing URIs
    targetFile = path.join(targetFolder, 'loc.ttl')
    existingIdentifiers = queryIdentifiersInFile(targetFile, "?identifier a <http://www.loc.gov/mads/rdf/v1#Authority> .")
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]
    # Retrieve ttl data from GND and append to ttl file
    with open(targetFile, 'a') as outputFile:
        for identifier in tqdm(identifiersToRetrieve):
            url = "%s.nt" % identifier
            try:
                firstRequest = requests.get(url)
                # Follow redirect
                if firstRequest.status_code == 200:
                    outputFile.write(firstRequest.text + "\n")
                elif firstRequest.status_code == 301:
                    url = firstRequest.headers['location']
                    secondRequest = requests.get(url)
                    outputFile.write(secondRequest.text + "\n")
            except:
                print("Could not retrieve", url)

        outputFile.close()
    return {
        "status": "success",
        "message": "Retrieved %d additional LOC identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

def retrieveWdData(identifiers, targetFolder):
    """
    Retrieves the data for the given identifiers and writes it to a file named wd.ttl in the target folder.
    Only the data for the identifiers that are not already in the file is retrieved.
    The data is retrieved from the Wikidata SPARQL Endpoint.
    :param identifiers: The list of identifiers to retrieve.
    :param targetFolder: The folder where the data is stored.
    :return: A dictionary with the status and a message.
    """

    def chunker(seq, size):
        """
        Function to loop through list in chunks
        Yields successive chunks from seq.
        :param seq: The list to loop through.
        :param size: The size of the chunks.
        """
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    # Read the output file and query for existing URIs
    targetFile = path.join(targetFolder, 'wd.ttl')
    existingIdentifiers = queryIdentifiersInFile(targetFile, "?identifier wdt:P31 ?type .")

    
    # Filter out existing identifiers
    identifiersToRetrieve = [d for d in identifiers if d not in existingIdentifiers]

    # Retrieve relevant data from Wikidata and append to ttl file
    wdEndpoint = "https://query.wikidata.org/sparql"
    batchSizeForRetrieval = 100
    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    sparql = SPARQLWrapper(wdEndpoint, agent=agent)    
    with open(targetFile, 'a') as outputFile:
        for batch in tqdm(chunker(identifiersToRetrieve, batchSizeForRetrieval)):
            query = """
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                CONSTRUCT {
                    ?entity wdt:P31 ?type ;
                        wdt:P625 ?coordinates ;
                        wdt:P18 ?image .
                } WHERE {
                    {
                        ?entity wdt:P31 ?type .
                    } UNION {
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
            sleep(3)
            outputFile.write(results.serialize(format='turtle'))
    return {
        "status": "success",
        "message": "Retrieved %d additional Wikidata identifiers (%d present in total)" % (len(identifiersToRetrieve), len(identifiers))
    }

if __name__ == "__main__":
    options = {}

    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("--"):
            if not sys.argv[i + 2].startswith("--"):
                options[arg[2:]] = sys.argv[i + 2]
            else:
                print("Malformed arguments")
                sys.exit(1)

    if not 'sourceFolder' in options:
        print("An input directory that contains the source TTL files must be specified via the --sourceFolder option")
        sys.exit(1)

    if not 'targetFolder' in options:
        print("An output directory must be specified via the --targetFolder option")
        sys.exit(1)
  
    if not 'sources' in options:
        print("A comma-separated list of sources must be specified via the --sources option")
        sys.exit(1)
    
    if 'limit' in options:
        options['limit'] = int(options['limit'])

    options['sources'] = options['sources'].split(',')

    # Check if list of sources only contains supported sources
    supportedSources = ["aat", "gnd", "loc", "wd"]
    for source in options['sources']:
        if source not in supportedSources:
            print("Source {} is not supported".format(source))
            print("Supported sources are: {}".format(", ".join(supportedSources)))
            sys.exit(1)

    retrieveData(options)
