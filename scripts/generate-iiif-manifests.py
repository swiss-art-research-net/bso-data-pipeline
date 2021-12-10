import json
import sys
from os.path import join
from sariFieldDefinitionsGenerator import generator
from SPARQLWrapper import SPARQLWrapper, JSON
from string import Template
from tqdm import tqdm

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 99999
offset=int(sys.argv[2]) if len(sys.argv) > 2 else 0
outputFolder = str(sys.argv[3]) if len(sys.argv) > 3 else "../static/iiif/"
fieldDefinitionsFile = str(sys.argv[4]) if len(sys.argv) > 4 else "/bso-app-src/fieldDefinitions.yml"

endpoint = "http://blazegraph:8080/blazegraph/sparql"


def sparqlResultToDict(results):
    rows = []
    for result in results["results"]["bindings"]:
        row = {}
        for key in list(result.keys()):
            row[key] = result[key]["value"]
        rows.append(row)
    return rows

def getMetadataForObject(obj):
    metadata = []
    
    labelQueryTemplate = Template("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {
        <$uri> rdfs:label ?label .
    }
    """)

    namespaces = ""
    for key in model['namespaces'].keys():
        namespaces += "PREFIX " + key + ": <" + model['namespaces'][key] + ">\n"
    
    subject = obj['subject']
    for field in fieldsToAdd:
        if 'selectPattern' in field:
            query = namespaces + field['selectPattern'].replace("$subject", "<%s>" % subject)
            sparql.setQuery(query)
            result = sparqlResultToDict(sparql.query().convert())
            if result:
                # might be several values
                valueLabels = []
                for row in result:
                    value = row['value']
                    if not 'label' in result and field['xsdDatatype'] == 'xsd:anyURI':
                        sparql.setQuery(labelQueryTemplate.substitute(uri=value))
                        labelResult = sparqlResultToDict(sparql.query().convert())
                        try:
                            label = labelResult[0]['label']
                        except:
                            label = False
                    else:
                        label = result[0]['value']
                    valueLabels.append(label)
                    if len(valueLabels) > 0:
                        metadata.append({
                            "label": {
                                "none": [field['label']]
                            },
                            "value": {
                                "none": [', '.join(valueLabels)]
                            }
                        })
    return metadata

model = generator.loadSourceFromFile(fieldDefinitionsFile)
fieldQueriesRaw = generator.generate(model, generator.JSON)
fields = json.loads(fieldQueriesRaw)
fieldsToAdd = [d for d in fields if 'display' not in d or d['display'] != 'hidden']

sparql = SPARQLWrapper(endpoint)
sparql.setReturnFormat(JSON)

objectsQuery = """
PREFIX search: <https://platform.swissartresearch.net/search/>
SELECT ?subject ?label WHERE {
    ?subject a search:Object ;
        rdfs:label ?label .
}
"""

imageQueryTemplate = Template("""
PREFIX aat: <http://vocab.getty.edu/aat/>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX la: <https://linked.art/ns/terms/>
SELECT ?image ?width ?height WHERE {
    <$uri> crm:P128_carries/la:digitally_shown_by ?imageObject .
    ?imageObject la:digitally_available_via/la:access_point ?image ;
        crm:P43_has_dimension ?dimWidth ;
        crm:P43_has_dimension ?dimHeight .
    ?dimWidth crm:P2_has_type aat:300055647 ;
        crm:P90_has_value ?width .
    ?dimHeight crm:P2_has_type aat:300055644 ;
        crm:P90_has_value ?height .
}
""")

sparql.setQuery(objectsQuery)
objects = sparqlResultToDict(sparql.query().convert())

manifests = []

for obj in tqdm(objects[offset:offset + limit]):
    baseUri = obj['subject'].replace('artwork', 'manifest')
    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": baseUri,
        "items": [],
        "type": "Manifest",
        "label": {
            "none": [obj['label']]
        },
        "metadata": getMetadataForObject(obj)
    }
    
    imageQuery = imageQueryTemplate.substitute(uri=obj['subject'])
    sparql.setQuery(imageQuery)
    images = sparqlResultToDict(sparql.query().convert())
    
    for i, image in enumerate(images):
        canvas = {
            "id": "%s/image/%d/canvas" % (baseUri, i),
            "type": "Canvas",
            "width": int(image['width']),
            "height": int(image['height']),
            "items": [{
                    "id": "%s/image/%d/canvas/page" % (baseUri, i),
                    "type": "AnnotationPage",
                    "items": [{
                        "id": "%s/image/%d/canvas/page/annotation" % (baseUri, i),
                        "type": "Annotation",
                        "motivation": "painting",
                        "body": {
                            "id": "%s/full/max/0/default.jpg" % image['image'],
                            "type": "Image",
                            "format": "image/jpeg",
                            "width": int(image['width']),
                            "height": int(image['height']),
                            "service": [{
                                "id": image['image'],
                                "profile": "level1",
                                "type": "ImageService3"
                            }]
                        },
                        "target": "%s/image/%d/canvas" % (baseUri, i)
                    }]
                }]
        }
        manifest['items'].append(canvas)
    manifests.append(manifest)
    
    filename = join(outputFolder, manifest['id'][len("https://resource.swissartresearch.net/manifest/"):] + ".json")
    with open(filename, 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)