import csv
import json
import re
import sys
import unicodedata
from lxml import etree
from tqdm import tqdm

# Database export provided by SFF
inputFile = '../data/source/SFF-Datenbank-Export.csv'

# Prefix for curated fields
curatedFilesPre = '../data/source/sff-curation-'

# Manually curated list of artists and roles
artistsFile = '../data/source/sff-curation-artists.csv'

# Correspondence between record IDs and image files
imagesFile = '../data/source/sff-images.csv'

# Define output directory and prefix for naming xml files
outputDirectory = '../data/xml/sff/'
outputPrefix = 'sff-record-'

# Fields that have been curated
curatedFields = ['Keywords', 'Ortsbezug']

# Read arguments from command line input
limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0
idsToOutput=str(sys.argv[3]) if len(sys.argv) >3 else False

# Define functions:
def addArtistsData(record):
    artistTagName = "KünsterIn"
    artistValues = record.findall(artistTagName + '/values/value')
    
    # Curated data is added as is, except if the fields are specified here
    fieldsToTreatSeparately = ['role', 'role_gnd']
    
    # Context is set as 'production' per default, except for
    # roles specified here, where it is set to 'creation'
    creationContext = ['Zeichner', 'Autor', 'Maler', 'Zeichnerin', 'Kartograph']
    
    for value in artistValues:
        artistIdName = value.find('text').text
        if not artistIdName:
            return record
        artistData = False
        try:
            artistData = [d for d in artistsData if d['id'] == artistIdName][0]
        except:
            print("Could not find artist data for", artistIdName)
            
        if artistData:
            for key in artistData.keys():
                if key not in fieldsToTreatSeparately:
                    newElement = etree.SubElement(value, key)
                    newElement.text = artistData[key]
            if artistData['role']:
                roles = artistData['role'].split(', ')
                roles_gnd = artistData['role_gnd'].split(', ')
                rolesElement = etree.SubElement(value, 'roles')
                for i, role in enumerate(roles):
                    roleElement = etree.SubElement(rolesElement, 'roleValue')
                    roleElement.set('gnd', roles_gnd[i])
                    roleElement.text = role
                    if role in creationContext:
                        value.set('creation', 'true')
                    else:
                        value.set('production', 'true')
                        
    return record

def addCuratedData(record):
    for curatedField in curatedFields:
        tag = cleanKeyForTags(curatedField)
        valueTags = record.findall(tag + '/values/value')
        for valueTag in valueTags:
            text = valueTag.find('text').text
            lookupHash = customHash(text)
            
            if text:
                try:
                    index = curatedFiles[curatedField]['lookup'][lookupHash]
                    match = curatedFiles[curatedField]['content'][index]

                    for column in match: 
                        if column != 'id':
                            newSubfield = etree.SubElement(valueTag, column)
                            newSubfield.text = match[column]
                except:
                    print("Could not find matching data for", valueTag.find('text').text)
    return record

def addImageData(record):
    recordIdentifier = record.find('record-identifier').text
    try:
        imageData = imagesData[recordIdentifier]
    except:
        print("Could not find an image for", recordIdentifier)
        return record
    
    imageTag = etree.SubElement(record, 'image')
    imageTag.set('filename', imageData['filename'])
    imageTag.text = imageData['image_id']
    return record

def addRecordIdentifier(record):
    identifier = record.find("InvNr").text
    field = etree.SubElement(record, "record-identifier")
    field.text = identifier
    return record

def cleanKeyForTags(key):
    cleanedKey = re.sub(r'[\s.*_]', '', key)
    cleanedKey = re.sub(r'[()]', '-', cleanedKey)
    cleanedKey = re.sub(r'-$', '', cleanedKey)
    return cleanedKey
    
def customHash(l):
    def NFD(s):
        return unicodedata.normalize('NFD', s)

    return hash(NFD(json.dumps(l, ensure_ascii=False)))

def convertRowToXMLRecord(row):
    record = etree.Element('record')
    for k in row.keys():
        if k:
            tag = cleanKeyForTags(k)
            subElement = etree.SubElement(record, tag)
            subElement.text = row[k]
    return record

def splitMultiValueFields(record):
    multiValueSeparators = {
        "KünsterIn": "/",
        "Bemerkungen": "/",
        "Keywords": ",",
        "Ortsbezug": r"\)[,|;]"
    }
    # Add suffix that may be cut off through regex separator
    multiValueSuffixes = {
        "Ortsbezug": ")"
    }
    for key in multiValueSeparators.keys():
        tag = record.find(cleanKeyForTags(key))
        values = re.split(multiValueSeparators[key], tag.text)
        values = [d.strip() for d in values]
        if key in multiValueSuffixes.keys():
            values = [d + multiValueSuffixes[key] for d in values[:-1]] + values[-1:]
        
        valuesTag = etree.SubElement(tag, 'values')
        for value in values:
            valueTag = etree.SubElement(valuesTag, 'value')
            etree.SubElement(valueTag, 'text').text = value

        tag.text = ''
        
    return record 

# Read input data
inputData = []
with open(inputFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        inputData.append(row)

# Read fields from external files
curatedFiles = {}
for key in curatedFields:
    filename = curatedFilesPre + key.lower() + '.csv'
    try:
        content = []
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                content.append(row)

        lookup = {}
        for i, row in enumerate(content):
            lookupHash = customHash(row['id'])
            lookup[lookupHash] = i

        curatedFiles[key] = {
            "tag": cleanKeyForTags(key),
            "content": content,
            "lookup": lookup,
            "filename" : filename
        }

    except:
        print("Could not process", filename)

artistsData = []
with open(artistsFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        artistsData.append(row)

imagesData = {}
with open(imagesFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        imagesData[row['record_id']] = {
            'image_id': row['image_id'],
            'filename': row['filename']
        }

# Output individual XML files
collection = etree.XML("<collection/>")

# Filter ids to output if argument is set
if idsToOutput:
    listOfIds = idsToOutput.split(',')
    inputData = [d for d in inputData if d["Inv. Nr."] in listOfIds]

for row in tqdm(inputData[offset:offset + limit]):
    record = convertRowToXMLRecord(row)
    
    record = addRecordIdentifier(record)
    record = splitMultiValueFields(record)
    record = addArtistsData(record)
    record = addImageData(record)
    record = addCuratedData(record)
    
    collection.clear()
    collection.append(record)
    outputFile = outputDirectory + outputPrefix + record.find("InvNr").text + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, encoding='UTF-8', pretty_print=True))
        f.close()