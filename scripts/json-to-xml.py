from lxml import etree
import json
import os
import requests
import urllib

inputFile = "../input/sari_abzug-utf-8_23_04-tsv.txt"
manifestDirectory = "../manifests/"
outputDirectory = "../input/"
outputPrefix = "sari-"

def convertRowToXml(row, keys):
    record = etree.Element("record")
    etree.SubElement(record, "uuid").text = row['UUID']
    datafield = False
    for key in keys:
        if key in row and row[key] is not None:
            if '$' in key:
                code = key[4:]
                etree.SubElement(datafield, "subfield", code=code).text = str(row[key])
                # Remove non-separated field content
                datafield.text = None
            else:
                datafield = etree.SubElement(record, "datafield", tag=key)
                datafield.text = str(row[key])
    return record

def getImagesFromCachedManifest(manifest):
    manifestFilePath = manifestDirectory + urllib.parse.quote(manifest, safe='') + '.json'
    if os.path.isfile(manifestFilePath):
        with open(manifestFilePath, 'r') as f:
            content = json.load(f)
            canvases = [d for d in content['sequences'][0]['canvases']]
            images = [{
                'image': c['images'][0]['resource']['service']['@id'],
                'width': c['width'],
                'height': c['height']
            } for c in canvases]
            return images
    else:
        print("Manifest for %s has not been cached" % row['UUID'])
    
def imageListToXml(images):
    imagesNode = etree.Element("images")
    for image in images:
        imageNode = etree.SubElement(imagesNode, "image")
        etree.SubElement(imageNode, "height").text = str(image['height'])
        etree.SubElement(imageNode, "width").text = str(image['width'])
        etree.SubElement(imageNode, "url", type="iiif").text = image['image']
    return imagesNode

with open(inputFile, 'r') as f:
    rawData = json.load(f)

keys = list(rawData['rows'][0].keys())
keys.sort()

# Output individual files
for i, row in enumerate(rawData['rows']):
    
    records = etree.Element("records")
    record = convertRowToXml(row, keys)
    
    images = getImagesFromCachedManifest(row['manifest'])
    if images:
        record.append(imageListToXml(images))
    else:
        print("Aborting due to missing manuscript")
        print("%d out of %d converted" % (i, len(rawData['rows'])))
        exit()
    
    records.append(record)
    
    outputFile = outputDirectory + outputPrefix + row['UUID'] + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(records, pretty_print=True))