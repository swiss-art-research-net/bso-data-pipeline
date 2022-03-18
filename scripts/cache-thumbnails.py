import re
import requests
import sys
import time
from PIL import Image
from urllib import request
from os import path
from configparser import ConfigParser
from hashlib import blake2b
from string import Template
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm

USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"

def performCaching(options):
    propsFile = options['propsFile']
    outputDir = options['outputDir']
    endpoint = options['endpoint']
    namedGraph = options['namedGraph']
    propsFile = options['propsFile']
    thumbnailLocation = options['thumbnailLocation']
    thumbnailPrefix = options['thumbnailPrefix']
    thumbnailPredicate = options['thumbnailPredicate']
    filterCondition = options['filterCondition'] if 'filterCondition' in options else None
    
    queries = getThumbnailQueries(propsFile, filterCondition=filterCondition)
    thumbnails = queryThumbnails(endpoint=endpoint, queries=queries)
    downloadAll(data=thumbnails,
                prefix=thumbnailPrefix,
                directory=outputDir)
    r = ingestToTriplestore(endpoint=endpoint,
                        prefix=thumbnailPrefix,
                        data=thumbnails, 
                        graph=namedGraph,
                        location=thumbnailLocation, 
                        predicate=thumbnailPredicate
    )
    print(r.text)

def downloadAsThumbnail(*, url, directory, prefix, targetWidth=400):
    """
    Downloads the thumbnail from a given URL into a direcory.
    Thumbnails are resized to a specified maximum width.
    The filename is generated from the URL (hashed) and prefixed with the given prefix.
    :param url: The URL of the thumbnail
    :param directory: The directory to store the thumbnail
    :param prefix: The prefix to use for the filename
    :param targetWidth: The width to resize the thumbnail to
    """
    filepath = path.join(directory, generateFilename(url, prefix))
    urllib.URLOpener.version = USER_AGENT
    if not path.exists(filepath):
        request.urlretrieve(url, filepath)
        img = Image.open(filepath, 'r')
        (width, height) = (img.width, img.height)
        if width > targetWidth:
            img = img.resize((targetWidth, int(height/width*targetWidth)))
        img.save(filepath, 'jpeg', quality=75, optimize=True)
        
            
    return filepath

def downloadAll(*,data,directory,prefix):
    """
    Given a list of dictionaries with keys 'subject' and 'thumbnail',
    download all thumbnails to the given directory with the given prefix for the filenames.
    :param data: The list of dictionaries
    :param directory: The directory to store the thumbnails
    :param prefix: The prefix to use for the filenames
    """
    for row in tqdm(data):
        downloadAsThumbnail(url=row['thumbnail'], directory=directory, prefix=prefix)
        time.sleep(1) # 1 second delay to avoid rate limiting

def generateFilename(url, prefix):   
    def filenameHash(name, extension='.jpg'):
        h = blake2b(digest_size=20)
        h.update(name.encode())
        return h.hexdigest() + extension
    
    return prefix + filenameHash(url)

def generateTTLdata(data, filenamePrefix, location, predicate):
    ttlTemplate = Template("""
        <$subject> <$predicate> <$location/$filename> .
    """)
    return ttlTemplate.substitute(
        subject=data['subject'],
        filename=generateFilename(data['thumbnail'], filenamePrefix),
        predicate=predicate,
        location=location
    )

def getThumbnailQueries(propsFile,*, filterCondition=None):
    with open(propsFile, 'r') as f:
        rawConfig = f.read()
    configString = "[ui]\n" + rawConfig
    config = ConfigParser()
    config.read_string(configString)
    queries = re.split(r'(?<!\\),', config['ui']['preferredThumbnails'])
    queries = [re.sub(r'\\n|\\\\,', '', d) for d in queries]
    if filterCondition:
        filteredQueries = [d for d in queries if filterCondition in d]
        return filteredQueries
    return queries
        

def ingestToTriplestore(*, endpoint, data, graph, prefix, location, predicate):
    output = ''
    for row in data:
        output += generateTTLdata(row, prefix, location, predicate)
    r = requests.post(
        url=endpoint, 
        data=output,
        params={"context-uri": graph},
        headers={"Content-Type": "application/x-turtle"})
    return r
    
def queryThumbnails(*,endpoint, queries, limit=None):
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    queryTemplate = Template("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX search: <https://platform.swissartresearch.net/search/>
        SELECT $select WHERE {
            $queryParts
        }
    """)
    select = ['?subject']
    queryParts = []
    for i, query in enumerate(queries):
        variable = "?p%d" % i
        queryParts.append(query.replace("?value", variable))
        select.append(variable)
    query = queryTemplate.substitute(select=' '.join(select), queryParts=' UNION '.join(queryParts))
    if limit:
        query += " LIMIT %d" % limit
    sparql.setQuery(query)
    ret = sparqlResultToDict(sparql.queryAndConvert())
    thumbnails = []
    for row in ret:
        for i in range(len(queries)):
            variable = "p%d" % i
            if variable in row:
                thumbnails.append({
                    'subject': row['subject'],
                    'thumbnail': row[variable]
                })
                continue
    return thumbnails

def sparqlResultToDict(results):
    rows = []
    for result in results["results"]["bindings"]:
        row = {}
        for key in list(result.keys()):
            row[key] = result[key]["value"]
        rows.append(row)
    return rows


if __name__ == "__main__":
    options = {}

    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("--"):
            if not sys.argv[i + 2].startswith("--"):
                options[arg[2:]] = sys.argv[i + 2]
            else:
                print("Malformed arguments")
                sys.exit(1)

    if not 'endpoint' in options:
        print("A SPARQL endpoint needs to be specified via the --endpoint argument")
        sys.exit(1)
    if not 'propsFile' in options:
        print("A ui.props file containing the thumbnail queries needs to be specified via the --propsFile argument")
        sys.exit(1)
    if not 'outputDir' in options:
        print("An output directory needs to be specified via the --outputDir argument")
        sys.exit(1)
    if not 'namedGraph' in options:
        print("A named graph where the thumbnail data is ingested needs to be specified via the --namedGraph argument")
        sys.exit(1)
    if not 'thumbnailLocation' in options:
        print("A base URL where the thumbnails will be reachable the --thumbnailLocation argument")
        sys.exit(1)

    if not 'thumbnailPrefix' in options:
        options['thumbnailPrefix'] = "thumbnail-"
    if not 'thumbnailPredicate' in options:
        options['thumbnailPredicate'] = "http://schema.org/thumbnail"

    performCaching(options)