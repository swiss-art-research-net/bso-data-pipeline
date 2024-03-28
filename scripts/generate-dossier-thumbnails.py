import math
import requests
import os
import sys
from PIL import Image, ImageOps
from hashlib import blake2b
from io import BytesIO
from string import Template
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm

dossierType = "https://resource.swissartresearch.net/type/1525E0B2-4816-3D3F-AEC8-94BDE16CF0EC"

queries = {
    "dossiers": Template("""
        PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
        SELECT DISTINCT ?subject WHERE {
            BIND(<$dossierType> as ?dossierType)
            ?subject crm:P2_has_type ?dossierType .
        }"""),
    "items": Template("""
        PREFIX rso: <http://www.researchspace.org/ontology/>
        PREFIX crmdig: <http://www.ics.forth.gr/isl/CRMdig/>
        PREFIX la: <https://linked.art/ns/terms/>
        PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
        SELECT ?subject ?image WHERE {
            BIND(<$parent> as ?parent)
            BIND("500," as ?size)
            ?subject crm:P46i_forms_part_of ?parent ;
                crm:P128_carries/la:digitally_shown_by/la:digitally_available_via/la:access_point ?iiif .
        OPTIONAL {
            ?region crmdig:L49_is_primary_area_of ?iiif ;
                    rso:boundingBox ?bbox .
        }
        BIND(IF(BOUND(?region), URI(CONCAT(STR(?iiif), "/", STRAFTER(?bbox, "xywh="), "/", ?size, "/0/default.jpg")), URI(CONCAT(STR(?iiif), "/full/", ?size, "/0/default.jpg"))) as ?image)
        } LIMIT $limit
        """)
}

def performThumbnailGeneration(options):
    """
    Generate thumbnails for all dossiers in the collection.
    """
    outputDir = options['outputDir']
    endpoint = options['endpoint']
    maxImagesPerThumbnail = options['maxImagesPerThumbnail']
    namedGraph = options['namedGraph']
    thumbnailLocation = options['thumbnailLocation']
    thumbnailPrefix = options['thumbnailPrefix']
    thumbnailPredicate = options['thumbnailPredicate']

    # Get all dossiers
    dossiers = retrieveDossiers(endpoint)
    
    # Retrieve images in dossier
    data = retrieveImagesInDossier(dossiers=dossiers, endpoint=endpoint)

    # Generate contact sheets
    data = [d for d in generateContactSheets(data) if 'sheet' in d] # Only keep dossiers with a sheet
    
    # Save contact sheets
    data = saveContactSheets(data, directory=outputDir, prefix=thumbnailPrefix)

    # Ingest to Triplestore
    r = ingestToTriplestore(endpoint=endpoint,
                        prefix=thumbnailPrefix,
                        data=data, 
                        graph=namedGraph,
                        location=thumbnailLocation, 
                        predicate=thumbnailPredicate
    )
    print(r.text)

def generateContactSheets(data):
    for row in tqdm(data):
        urls = row['images']
        if len(urls) > 0:
            numRows = math.floor(math.sqrt(len(row['images'])))
            numCols = math.ceil(math.sqrt(len(row['images'])))
            row['sheet'] = makeContactSheet(urls, cols=numCols, rows=numRows, margin=2)
    return data

def generateFilename(url, prefix):
    """
    Generate a filename from a URL and a prefix.
    The filename is generated from the URL (hashed) and prefixed with the given prefix.
    :param url: The URL (of the thumbnail)
    :param prefix: The prefix to use for the filename
    """
    def filenameHash(name, extension='.jpg'):
        h = blake2b(digest_size=20)
        h.update(name.encode())
        return h.hexdigest() + extension
    
    return prefix + filenameHash(url)

def generateTTLdata(data, filenamePrefix, location, predicate):
    """
    Generate the TTL data for a given row of data.
    Data is a dictionary with keys 'subject' and 'thumbnail'.
    The function outputs a statements that links the subject to a file in the given location.
    The filename is generated from the URL (hashed) and prefixed with the given prefix.
    The location is the web location where the file is stored.
    :param data: The dictionary containing the dossier URI in 'dossier'
    :param filenamePrefix: The prefix to use for the filename
    :param location: The web location where the file is stored
    :param predicate: The predicate to use for the statement
    """
    ttlTemplate = Template("""
        <$subject> <$predicate> <$location/$filename> .
        <$location/$filename> a <http://www.cidoc-crm.org/cidoc-crm/E36_Visual_Item> .
    """)
    if not location.startswith("http"):
        location = "https://" + location
    return ttlTemplate.substitute(
        subject=data['dossier'],
        filename=generateFilename(data['dossier'], filenamePrefix),
        predicate=predicate,
        location=location
    )


def ingestToTriplestore(*, endpoint, data, graph, prefix, location, predicate):
    """
    Generates TTL data for all the given image thumbnails and ingests it to the triple store
    :param endpoint: The SPARQL endpoint to use
    :param data: The list of dictionaries with keys 'dossier' and 'sheetFilepath'
    :param graph: The named graph to ingest the data to
    :param prefix: The prefix to use for the filenames
    :param location: The web location where the files are stored
    :param predicate: The predicate to use for the statements
    """
    output = ''
    for row in data:
        output += generateTTLdata(row, prefix, location, predicate)
    r = requests.post(
        url=endpoint, 
        data=output,
        params={"context-uri": graph},
        headers={"Content-Type": "application/x-turtle"})
    return r

def retrieveDossiers(endpoint):
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(queries["dossiers"].substitute(dossierType=dossierType))
    dossiers = sparqlResultToDict(sparql.queryAndConvert())
    return dossiers

def retrieveImagesInDossier(*, dossiers, endpoint):
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    data = []
    for dossier in dossiers:
        row = {
            'dossier': dossier['subject'],
            'images': []
        }
        query = queries["items"].substitute(parent=dossier['subject'], limit=options['maxImagesPerThumbnail'])
        sparql.setQuery(query)
        images = sparqlResultToDict(sparql.queryAndConvert())
        row['images'] = [d['image'] for d in images]
        data.append(row)
    return data

def saveContactSheets(data, *, directory, prefix):
    for row in data:
        filename = os.path.join(directory, generateFilename(row['dossier'], prefix))
        sheet = row['sheet']
        sheet.save(filename, 'jpeg', quality=75, optimize=True)
        row['sheetFilepath'] = filename
    return data


def makeContactSheet(urls, *, cols=3, rows=3, width=500, height=500, margin=0, bgColor=(0,0,0)):
    """
    Generates a contact sheet from a list of URLs.
    Adapted from https://code.activestate.com/recipes/412982-use-pil-to-make-a-contact-sheet-montage-of-images/
    params:
        urls: list of URLs
        cols: number of columns (optional, default 3)
        rows: number of rows (optional, default 3)
        width: width of the generated thumbnail image (optional, default 500)
        height: height of the generated thumbnail image (optional, default 500)
        margin: margin between images (optional, default 0)
        bgColor: background color of the generated thumbnail image (optional, default (0,0,0))
    """
    maxWidth = int(width / cols - margin * (cols - 1))
    maxHeight = int(height / rows - margin * (rows - 1))
    imgs = []
    for url in urls:
        try:
            response = requests.get(url)
        except Exception as e:
            print("Could not download",url)
            continue
        img = Image.open(BytesIO(response.content))
        img = ImageOps.fit(img, (maxWidth, maxHeight), Image.LANCZOS)
        imgs.append(img)
    
    sheet = Image.new('RGB',(width, height), bgColor)
    for row in range(rows):
        for col in range(cols):
            left = int(col * (maxWidth + margin))
            upper = int(row * (maxHeight + margin))
            try:
                img = imgs.pop(0)
            except:
                break
            sheet.paste(img, (left, upper))
    
    return sheet



def sparqlResultToDict(results):
    """
    Convert a SPARQL query result to a dictionary.
    """
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
    if not 'outputDir' in options:
        print("An output directory needs to be specified via the --outputDir argument")
        sys.exit(1)
    if not 'namedGraph' in options:
        print("A named graph where the thumbnail data is ingested needs to be specified via the --namedGraph argument")
        sys.exit(1)
    if not 'thumbnailLocation' in options:
        print("A base URL where the thumbnails will be reachable the --thumbnailLocation argument")
        sys.exit(1)

    if not 'maxImagesPerThumbnail' in options:
        options['maxImagesPerThumbnail'] = 9
    if not 'thumbnailPrefix' in options:
        options['thumbnailPrefix'] = "dossier-"
    if not 'thumbnailPredicate' in options:
        options['thumbnailPredicate'] = "http://schema.org/thumbnail"

    performThumbnailGeneration(options) 