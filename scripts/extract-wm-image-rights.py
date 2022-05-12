import json
import re
import requests
import time

from rdflib import Graph
from string import Template
from tqdm import tqdm

inputFile = '../data/ttl/additional/wd.ttl'
outputFile = '../data/ttl/additional/wdRights.ttl'

# Read input graph
g = Graph()
g.parse(inputFile, format="ttl")

# Extract all image URIs
imagesQuery = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?image WHERE {
    ?s wdt:P18 ?image .
}
"""
results = g.query(imagesQuery)
images = []
for row in results:
    images.append(str(row['image']))

print('Found ' + str(len(images)) + ' images')

# Retrieve image metadata from Wikimedia Commons
imageData = {}
for image in tqdm(images):
    if image not in imageData:
        title = image.replace("http://commons.wikimedia.org/wiki/Special:FilePath/", "File:")
        url = "https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&&format=json&titles=" + title
        r = requests.get(url)
        imageData[image] = r.json()['query']['pages']['-1']['imageinfo'][0]['extmetadata']
        time.sleep(0.5)

# Convert image metadata to CIDOC/RDF
imageTtlNamespaces = """
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
"""
imageTtlTemplate = Template('''
    <$image> rdfs:label """$imageLabel""" ;
        crm:P104_is_subject_to <$image/right> .
    
    <$image/right> a crm:E30_Right ;
        crm:P105_right_held_by <$rightsHolder> ;
        crm:P2_has_type <$license> .
        
    <$license> rdfs:label """$licenseName""" ;
        crm:P3_has_note """$usageTerms""" .
        
    <$rightsHolder> a crm:E39_Actor ;
        rdfs:label """$rightsHolderLabel""" .
''')

imageTtlOutput = imageTtlNamespaces
for imageUri, data in imageData.items():
    if 'Artist' in data:
        artistSearch = re.search(r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1', data['Artist']['value'])
        if artistSearch:
            artist = artistSearch.group(2)
        else:
            artist = imageUri + '/creator'
        artistLabel = data['Artist']['value']
    elif 'Credit' in data:
        creditSearch = re.search(r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1', data['Credit']['value'])
        if creditSearch:
            artist = creditSearch.group(2)
        else:
            artist = imageUri + '/creator'
        artistLabel = data['Credit']['value']
    else:
        artist = "https://commons.wikimedia.org"
        artistLabel = "Wikimedia Commons"
        
    if artist.startswith('//'):
        artist = "https:" + artist

    artistLabel = re.sub(r'(<.*?>)|(\n)', '', artistLabel)
        
    imageLabel = re.sub(r'(<.*?>)|(\n)', '', data['ImageDescription']['value']) if 'ImageDescription' in data else '',

    
    if 'LicenseUrl' in data:
        license = data['LicenseUrl']['value']
    else:
        license = 'https://resource.swissartresearch.net/license/' + data['LicenseShortName']['value'].replace(" ", "%20")
        
    imageTtlOutput += imageTtlTemplate.substitute(
        image=imageUri,
        imageLabel=imageLabel,
        rightsHolder=artist,
        rightsHolderLabel=artistLabel,
        license=license,
        licenseName=data['LicenseShortName']['value'],
        usageTerms=data['UsageTerms']['value']
    )

# Write output
with open(outputFile, 'w') as f:
    f.write(imageTtlOutput)