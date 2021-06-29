from edtf import parse_edtf
from sariDateParser.dateParser import parse
from lxml import etree
from tqdm import tqdm
import copy
import csv
import json
import os
import requests
import urllib
import unicodedata
import time
import sys

sys.path.append("./helpers")
import dateOverrides

inputFiles = [
    '../data/source/BIBLIOGRAPHIC_8971984070005508_1.xml',
    '../data/source/BIBLIOGRAPHIC_8971984070005508_2.xml',
    '../data/source/BIBLIOGRAPHIC_8971984070005508_3.xml',
    '../data/source/BIBLIOGRAPHIC_8971984070005508_4.xml'
]

curatedFilesPre = '../data/source/zbz-curation-'
manifestDirectory = "../data/manifests/"
doisFile = '../data/source/zbz-dois.csv'
outputDirectory = "../data/xml/zbz/"
outputPrefix = "zbz-record-"

# List fields that contain dates. Those will be passed to the parser
fieldsContainingDates = ['100$d', '260$c', '260$g', '264$c', '533$d', '600$d', '611$d', '700$d']

# List fields that are loaded from separate files (e.g. curated fields)
curatedFields = {
    '100': [['a', 'd']],
    '110': [['a']],
    '264': [['a'], ['b']],
    '600': [['a', 'b']],
    '610': [['a', 'g']],
    '611': [['a', 'c', 'd']],
    '650': [['a', 'g']],
    '651': [['a', 'g']],
    '655': [['a']],
    '700': [['a', 'd']],
    '710': [['a']],
    '751': [['a', 'g']]
}
limit=int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset=int(sys.argv[2]) if len(sys.argv) >2 else 0

# Define functions
   
def addCuratedData(record):
    datafields = record.findall("datafield")
    # Look through every datafield
    for datafield in datafields:
        tag = datafield.get("tag")
        # Check if datafield has been curated
        if tag in curatedFields.keys():
            # Look at subfields to match
            for subfieldList in curatedFields[tag]:
                curatedFileId = tag + "-" + '_'.join(subfieldList)
                # Establish conditions for subfields to match
                conditions = {}
                for subfield in subfieldList:
                    value = datafield.find("subfield[@code='%s']" % subfield)
                    value = value.text if value is not None else None
                    conditions[tag + "_" + subfield] = value
                    
                # Find rows that match all subfield
                matches = []
                for row in curatedFiles[curatedFileId]['content']:
                    isMatch = True
                    for column in conditions.keys():
                        if not compare_strs(row[column],conditions[column]):
                            isMatch = False
                            break
                    if isMatch:
                        matches.append(row)
                
                if len(matches) > 1:
                    print("Found several candidates")
                    print(matches)
                    
                if len(matches) >= 1:
                    for column in matches[0]: 
                        if column not in conditions:
                            newSubfield = etree.SubElement(datafield, "subfield")
                            newSubfield.set("code", column)
                            newSubfield.text = matches[0][column]
    
    return record

def addImages(record):
    if record.find("datafield[@tag='manifest']") is not None:
        images = getImagesFromCachedManifest(record.find("datafield[@tag='manifest']").text)
        if images:
            record.append(imageListToXml(images))
    return record

def addRecordIdentifier(record):
    identifier = record.find("controlfield[@tag='001']").text
    field = etree.SubElement(record, "record-identifier")
    field.text = "zbz-" + identifier
    return record

def addManifest(record):
    identifier = record.find("controlfield[@tag='001']").text
    try:
        manifestURL = manifests[identifier]
    except:
        print("Could not find IIIF manifest for", identifier)
        return record
    
    manifestDatafield = etree.SubElement(record, "datafield")
    manifestDatafield.set("tag", "manifest")
    manifestDatafield.text = manifestURL
    return record

def compare_strs(s1, s2):
    def NFD(s):
        return unicodedata.normalize('NFD', s)
    if s1 is None:
        s1 = ''
    if s2 is None:
        s2 = ''

    return NFD(s1) == NFD(s2)

def convertEDTFdate(date):
    try:
        d = parse_edtf(downgradeEDTF(date))
    except:
        raise ValueError('Invalid date', date)
    
    if 'Interval' in str(type(d)):
        if type(d.lower) is list:
            lower = d.lower[0].lower_strict()
        else:
            lower = d.lower.lower_strict()
        if type(d.upper) is list:
            upper = d.upper[0].upper_strict()
        else:
            upper = d.upper.upper_strict()
    else:
        if type(d) is list:
            lower = d[0].lower_strict()
            upper = d[0].upper_strict()
        else:
            lower = d.lower_strict()
            upper = d.upper_strict()
    return {
        'lower': time.strftime("%Y-%m-%d", lower),
        'upper': time.strftime("%Y-%m-%d", upper)
    }

def downgradeEDTF(date):
    """
    Convert a edtf date string to the previous version supported by the python edtf package
    """
    edtfDate = date.replace('X','u')
    if edtfDate[-1:] == '/':
        edtfDate += 'uuuu-uu'
    if edtfDate[0] == '/':
        edtfDate = 'uuuu-uu' + edtfDate
    return edtfDate

def getImagesFromCachedManifest(manifest):
    manifestFilePath = manifestDirectory + urllib.parse.quote(manifest, safe='') + '.json'
    if os.path.isfile(manifestFilePath):
        with open(manifestFilePath, 'r') as f:
            content = json.load(f)
            if 'sequences' in content and len(content['sequences']) > 0:
                canvases = [d for d in content['sequences'][0]['canvases']]
                images = [{
                    'image': c['images'][0]['resource']['service']['@id'],
                    'width': c['width'],
                    'height': c['height']
                } for c in canvases]
                return images
            else:
                print("No sequences found in manifest %s" % manifest)
    else:
        print("Manifest %s has not been cached" % manifest)
    
def imageListToXml(images):
    imagesNode = etree.Element("images")
    for image in images:
        imageNode = etree.SubElement(imagesNode, "image")
        etree.SubElement(imageNode, "height").text = str(image['height'])
        etree.SubElement(imageNode, "width").text = str(image['width'])
        etree.SubElement(imageNode, "url", type="iiif").text = image['image']
    return imagesNode

def parseDate(date):
    if date in dateOverrides.zbz:
        return dateOverrides.zbz[date]
    else:
        return parse(date)

def processDates(record):
    for dateField in fieldsContainingDates:
        parts = dateField.split('$')
        xpath = "datafield[@tag='%s']/subfield[@code='%s']" % (parts[0], parts[1])
        subfields = record.findall(xpath)
        if subfields is not None:
            for subfield in subfields:
                try:
                    parsedDate = parseDate(subfield.text)
                except:
                    print("Could not parse date")
                if parsedDate:
                    subfield.set("parsedDate", parsedDate)
                    daterange = convertEDTFdate(parsedDate)
                    subfield.set("upperDate", daterange['upper'])
                    subfield.set("lowerDate", daterange['lower'])
    return record

def splitMultiValueFields(record):
    # Adds separate datafields for datafields that contain multiple values
    # e.g. 264 sometimes contains several subfields with code a and b
    # Find subfields that have at least 2 code a's
    subfieldAInSecondPlace = record.xpath("datafield/subfield[@code='a'][2]")
    for subfield in subfieldAInSecondPlace:
        datafield = subfield.getparent()
        tag = datafield.get("tag")
        # Determine the number of subfields by looking at the number of subfields with code a
        numSubfields = len(datafield.findall("subfield[@code='a']"))
        # Determine the codes that are used
        codes = sorted(list(set([d.get('code') for d in datafield.findall("subfield")])))
        # For every subfield
        for i in range(numSubfields):
            index = i+1
            # Add a new subfield
            newDatafield = etree.SubElement(record, "datafield")
            newDatafield.set("tag", tag)
            # Mark the index of the subfield
            indexSubfield = etree.SubElement(newDatafield, "subfield")
            indexSubfield.set("code", "index")
            indexSubfield.text = str(i)
            # Iterate through the subfield codes and if there is a subfield at the
            # respective index, add it
            for code in codes:
                value = datafield.xpath("subfield[@code='%s'][%d]" % (code, index))
                if value is not None and len(value):
                    newSubfield = etree.SubElement(newDatafield, "subfield")
                    newSubfield.set("code", code)
                    newSubfield.text = value[0].text
        # Remove the parent
        record.remove(datafield)
    
    return record


# Read main data files
root = etree.XML("<collection/>")
for inputFile in inputFiles:
    collection = etree.parse(inputFile)
    for record in collection.findall("//record"):
        root.append(record)
records = root.findall(".//record")

# Read fields from external files
curatedFiles = {}
for tag in curatedFields.keys():
    for subfieldList in curatedFields[tag]:
        subfieldListId = '_'.join(subfieldList)
        
        filename = curatedFilesPre + tag + '-' + subfieldListId + '.csv'
        try:
            content = []
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    content.append(row)
                    
            curatedFiles[tag + "-" + subfieldListId] = {
                "tag": tag,
                "content": content,
                "subfields" : subfieldList,
                "filename" : filename
            }
        except:
            print("Could not process", filename)

# Read manifest data
manifests = {}
with open(doisFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        manifests[row['id']] = row['manifest']

# Output individual files
collection = root

for record in tqdm(records[offset:offset + limit]):
    record = addRecordIdentifier(record)
    record = splitMultiValueFields(record)
    record = addCuratedData(record)
    record = addManifest(record)
    record = addImages(record)
    record = processDates(record)

    collection.clear()
    collection.append(record)
    outputFile = outputDirectory + outputPrefix + record.find("controlfield[@tag='001']").text + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, encoding='UTF-8', pretty_print=True))
        f.close()