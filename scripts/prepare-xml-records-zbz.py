from edtf import parse_edtf
from sariDateParser.dateParser import parse
from lxml import etree
from tqdm import tqdm
import copy
import json
import os
import requests
import urllib
import time
import sys

sys.path.append("./helpers")
import dateOverrides

inputFile = "/data/source/sari_abzug-utf-8_23_04-tsv.json"
externalFieldsDirectory = "/data/source/"
manifestDirectory = "/data/manifests/"
outputDirectory = "/data/xml/zbz/"
outputPrefix = "zbz-record-"

# List fields that contain dates. Those will be passed to the parser
fieldsContainingDates = ['100$d', '260$c', '260$g', '264$c', '533$d', '600$d', '611$d', '700$d']

# List fields that are loaded from separate files (e.g. curated and/or multi-value fields)
externalFields = ['100', '110', '264', '600', '610', '611', '650', '651', '655', '700', '710', '751']

limit=int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset=int(sys.argv[2]) if len(sys.argv) >2 else 0

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

def convertRowToXml(row, keys, externalFields):
    record = etree.Element("record")
    etree.SubElement(record, "uuid").text = row['id']
    etree.SubElement(record, "record-identifier").text = "zbz-" + row['001']
    datafield = False
    for key in keys:
        # Check if key is a field that gets loaded externally (check only part before $ if present)
        if key.split('$')[0] in externalFields.keys():
            # Ignore the subfields as they will be loaded from the external fields
            if not '$' in key:
                # Select the field values based on the ids
                fieldsToInclude = [d for d in externalFields[key] if d['id'] == row['id']]
                for f in fieldsToInclude:
                    # Create a datafield for each set of values
                    datafield = etree.SubElement(record, "datafield", tag=key)
                    for k in [d for d in f.keys()]:
                        if key in k:
                            code = k.split('_')[1].replace(' ','_')
                        else:
                            code = k.replace(' ','_')
                        if f[k]:
                            subfield = etree.SubElement(datafield, "subfield", code=code)
                            subfield.text = str(f[k])
                        # Check if field contains a date
                        if k.replace("_","$") in fieldsContainingDates and f[k]:
                            try:
                                parsedDate = parseDate(f[k])
                            except:
                                print("Could not parse", f[k],k)
                            if parsedDate:
                                subfield.set("parsedDate", parsedDate)
                                daterange = convertEDTFdate(parsedDate)
                                subfield.set("upperDate", daterange['upper'])
                                subfield.set("lowerDate", daterange['lower'])
        else:
            if key in row and row[key] is not None:
                if '$' in key:
                    code = key[4:]
                    subfield = etree.SubElement(datafield, "subfield", code=code)
                    subfield.text = str(row[key])
                    # Check if field contains a date
                    if key in fieldsContainingDates:
                        parsedDate = parseDate(row[key])
                        if parsedDate:
                            subfield.set("parsedDate", parsedDate)
                            daterange = convertEDTFdate(parsedDate)
                            subfield.set("upperDate", daterange['upper'])
                            subfield.set("lowerDate", daterange['lower'])
                    # Remove non-separated field content
                    datafield.text = None
                else:
                    datafield = etree.SubElement(record, "datafield", tag=key)
                    datafield.text = str(row[key])
    return record

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

def postProcess(record):
    """
    Execute additional steps on the XML output
    """

    # Duplicate fields 100, 110, 700 and 710 if there are several roles
    datafieldsWithSeveralRoles = record.findall("./datafield[@tag='100']") + record.findall("./datafield[@tag='110']") + record.findall("./datafield[@tag='700']") + record.findall("./datafield[@tag='710']")
    if len(datafieldsWithSeveralRoles):
        for datafield in datafieldsWithSeveralRoles:
            subfield4 = datafield.find("./subfield[@code='4']")
            subfieldE = datafield.find("./subfield[@code='e']")
            # If subfield 4 contains a comma, there are several roles defined
            if subfield4 is not None and ',' in subfield4.text:
                roleCodes = subfield4.text.split(', ')
                roleNames = subfieldE.text.split(', ')
                # Remove the field
                datafieldTemplate = copy.copy(datafield)
                datafield.getparent().remove(datafield)
                    # Create individual fields per role
                for i, roleCode in enumerate(roleCodes):
                    newDatafield = copy.copy(datafieldTemplate)
                    if newDatafield.find(".subfield[@code='id_person']") is not None:
                        newDatafield.find(".subfield[@code='id_person']").text = newDatafield.find(".subfield[@code='id_person']").text + "-" + str(i)
                    newDatafield.find("./subfield[@code='4']").text = roleCodes[i]
                    if len(roleNames) > i:
                        newDatafield.find("./subfield[@code='e']").text = roleNames[i]
                    record.append(newDatafield)

    return record

# Read main data file
with open(inputFile, 'r') as f:
    rawData = json.load(f)

# Read fields from external files
externalFieldContent = {}
for externalField in externalFields:
    filePath = externalFieldsDirectory + externalField + '.json'
    with open(filePath, 'r') as f:
        try:
            externalFieldContent[externalField] = json.load(f)['rows']
        except:
            exit("Could not read data from " + filePath)

keys = list(rawData['rows'][0].keys())
keys.sort()

# Output individual files
for i, row in enumerate(tqdm(rawData['rows'][offset:limit+offset])):
    
    records = etree.Element("records")
    record = convertRowToXml(row, keys, externalFieldContent)
    
    if row['manifest']:
        images = getImagesFromCachedManifest(row['manifest'])
        if images:
            record.append(imageListToXml(images))
        else:
            #print("Aborting due to missing manuscript")
            print("%d out of %d converted" % (i, len(rawData['rows'])))
            #exit()
    
    record = postProcess(record)
    
    records.append(record)
    
    outputFile = outputDirectory + outputPrefix + row['001'] + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(records, xml_declaration=True, encoding='UTF-8', pretty_print=True))
        f.close()