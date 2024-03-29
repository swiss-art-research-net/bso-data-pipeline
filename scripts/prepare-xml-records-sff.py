import csv
import json
import re
import sys
import unicodedata
from lxml import etree
from tqdm import tqdm

# Database export provided by SFF
inputFile = '../data/source/sff-werke.csv'

# Prefix for curated fields
curatedFilesPre = '../data/source/sff-curation-'
curatedFilesLiteraturePre = '../data/source/sff-curation-literature-'

# Manually curated list of artists and roles
artistsFile = '../data/source/sff-artists.csv'

# Correspondence between record IDs and image files
imagesFile = '../data/source/sff-images.csv'

# Export of dimensions table
dimensionsFile = '../data/source/sff-werk-masse.csv'

# Generated series table
seriesFile = '../data/source/sff-series.csv'

# Export of literature and literature links table
literatureFile = '../data/source/sff-literatur.csv'
literatureLinksFile = '../data/source/sff-literatur-links.csv'

# Define output directory and prefix for naming xml files
outputDirectory = '../data/xml/sff/'
outputPrefix = 'sff-record-'

# Fields that have been curated
curatedFields = ['Keywords', 'Ortsbezug', 'Material', 'Technik']
curatedFieldsInLiterature = ['in Zeitschrift', 'Ort', 'Autor, Hsg.', 'Verlag']

# Read arguments from command line input
limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0
idsToOutput=str(sys.argv[3]) if len(sys.argv) >3 else False

# Define functions:
def addArtistsData(record):
    artistTagName = "KünsterIn"
    artistKey = record.find(artistTagName).text
    
    try:
        curatedArtistData = [d for d in artistsData if d['link'] == artistKey]
    except:
        print("Could not find data for", artistKey)
        return record

    # Curated data is added as is, except if the fields are specified here
    fieldsToTreatSeparately = ['role', 'role_uri']
    
    # Context is set as 'production' per default, except for
    # roles specified here, where it is set to 'creation'
    creationContext = ['Zeichner', 'Autor', 'Maler', 'Zeichnerin', 'Kartograph']
    
    newArtistsTag = etree.SubElement(record, "artists")
    for curatedArtistRow in curatedArtistData:
        newArtistTag = etree.SubElement(newArtistsTag, "artist")
        for key in curatedArtistRow.keys():
            if key and curatedArtistRow[key]:
                if key not in fieldsToTreatSeparately:
                    newTag = etree.SubElement(newArtistTag, cleanKeyForTags(key))
                    newTag.text = curatedArtistRow[key]
        if curatedArtistRow['role']:
            roles = curatedArtistRow['role'].split(', ')
            role_uris = curatedArtistRow['role_uri'].split(', ')
            rolesElement = etree.SubElement(newArtistTag, 'roles')
            for i, role in enumerate(roles):
                roleElement = etree.SubElement(rolesElement, 'roleValue')
                roleElement.set('role_uri', role_uris[i])
                roleElement.text = role
                if role in creationContext:
                    newArtistTag.set('creation', 'true')
                    roleElement.set('creation', 'true')
                else:
                    newArtistTag.set('production', 'true')
                    roleElement.set('production', 'true')
                        
    return record

def addCuratedData(record):
    for curatedField in curatedFields:
        tag = cleanKeyForTags(curatedField)
        valueTags = record.findall(tag + '/values/value')
        if len(valueTags):
            for valueTag in valueTags:
                text = valueTag.find('text').text
                lookupHash = customHash(text)
                
                if text:
                    try:
                        index = curatedFiles[curatedField]['lookup'][lookupHash]
                        match = curatedFiles[curatedField]['content'][index]
                    except:
                        print("Could not find matching data for", valueTag.find('text').text)

                    if match:
                        for column in match: 
                            if column != 'id':
                                newSubfield = etree.SubElement(valueTag, column)
                                newSubfield.text = match[column]
        else:
            # Single value field
            singleValueTags = record.findall(tag)
            for singleValueTag in singleValueTags:
                text = singleValueTag.text
                lookupHash = customHash(text)
                
                if text:
                    try:
                        index = curatedFiles[curatedField]['lookup'][lookupHash]
                        match = curatedFiles[curatedField]['content'][index]

                        for column in match: 
                            if column != 'id':
                                if column in match and ';' in match[column]:
                                    for i, value in enumerate(match[column].split(';')):
                                        el = etree.SubElement(singleValueTag, column)
                                        el.set('index', str(i))
                                        el.text = value
                                else:
                                    singleValueTag.set(column, match[column])
                    except:
                        print("Could not find matching data for", singleValueTag.text)
            # Consolidate indexed fields
            maxIndex = 0
            for indexedField in singleValueTag.findall('./*[@index]'):
                index = int(indexedField.get('index'))
                if singleValueTag.find('alignments[@index="%d"]' % index) is not None:
                    alignments = singleValueTag.find('alignments[@index="%d"]' % index)
                else:
                    alignments = etree.SubElement(singleValueTag, 'alignments')
                    alignments.set('index', str(index))
                alignments.append(indexedField)
                del indexedField.attrib['index']
                if index > maxIndex:
                    maxIndex = index
            # Keep only first field if there is only one
            if maxIndex == 0:
                for element in singleValueTag.findall('./alignments/*'):
                    singleValueTag.append(element)
                for toRemove in singleValueTag.xpath('./alignments'):
                    singleValueTag.remove(toRemove)
    return record

def addCuratedDataForLiterature(record):
    for curatedField in curatedFieldsInLiterature:
        tag = cleanKeyForTags(curatedField)
        valueTags = record.findall('literatureList/literature/details/' + tag + '/values/value')
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
                    print("Could not find matching data for", tag.text)
    return record

def addDimensionData(record):
    recordId = record.find('InvNrIntern').text
    dimensionsRows  = [d for d in dimensionsData if d['Werk Inv. Nr.'] == recordId]
    if len(dimensionsRows) == 0:
        return record

    dimensionsTag = etree.SubElement(record, "dimensions")
    for dimensionsRow in dimensionsRows:
        dimensionTag = etree.SubElement(dimensionsTag, "dimension")
        for key in dimensionsRow.keys():
            if key and dimensionsRow[key]:
                newTag = etree.SubElement(dimensionTag, cleanKeyForTags(key))
                newTag.text = dimensionsRow[key]
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
    imageTag.set('width', imageData['width'])
    imageTag.set('height', imageData['height'])
    imageTag.text = imageData['image_id']
    return record

def addLiteratureData(record):
    recordId = record.find('InvNrIntern').text
    literatureLinks  = [d for d in literatureLinksData if d['WerkInv. Nr.'] == recordId]
    if len(literatureLinks) == 0:
        return record

    literatureListTag = etree.SubElement(record, "literatureList")
    for literatureLink in literatureLinks:
        literatureTag = etree.SubElement(literatureListTag, "literature")
        for key in literatureLink.keys():
            if key and literatureLink[key]:
                newTag = etree.SubElement(literatureTag, cleanKeyForTags(key))
                newTag.text = literatureLink[key]
    
        literatureDetails = [d for d in literatureData if d['Lit. Nr.'] == literatureLink['Lit. Nr.']]
        if len(literatureDetails) == 0:
            raise Exception("Could not find corresponding entry in literature list for " + literatureLink['Lit. Nr.'])
        elif len(literatureDetails) > 1:
            print(literatureDetails)
            raise Exception("Found several matching entries for " + literatureLink['Lit. Nr.'])
        else:
            detailsTag = etree.Element("details")
            for key in literatureDetails[0].keys():
                if key and literatureDetails[0][key]:
                    newTag = etree.SubElement(detailsTag, cleanKeyForTags(key))
                    newTag.text = literatureDetails[0][key]
            detailsTag = splitMultiValueFields(detailsTag)
            literatureTag.append(detailsTag)


    return record

def addSeriesData(record):
    recordId = record.find('InvNrIntern').text
    seriesRows  = [d for d in seriesData if d['id'] == recordId]
    if len(seriesRows) == 0:
        return record
    elif len(seriesRows) > 1:
        print ("Found several matching entries for", recordId)
        return record

    for seriesRow in seriesRows:
        seriesTag = etree.SubElement(record, "series")
        for key in seriesRow.keys():
            if key and seriesRow[key]:
                newTag = etree.SubElement(seriesTag, cleanKeyForTags(key))
                newTag.text = seriesRow[key]
    return record

def addRecordIdentifier(record):
    identifier = record.find("InvNr").text
    field = etree.SubElement(record, "record-identifier")
    field.text = identifier
    return record

def cleanKeyForTags(key):
    cleanedKey = re.sub(r'[\s.*_,]', '', key)
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
        "Keywords": ",",
        "Ortsbezug": r"\)[,|;]",
        "Ort": "/",
        "Autor, Hsg.": r";|/",
        "Verlag": "\|"
    }
    # Add suffix that may be cut off through regex separator
    multiValueSuffixes = {
        "Ortsbezug": ")"
    }
    for key in multiValueSeparators.keys():
        tag = record.find(cleanKeyForTags(key))
        if tag is not None:
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
for key in curatedFields + curatedFieldsInLiterature:
    filePre = curatedFilesPre if key not in curatedFieldsInLiterature else curatedFilesLiteraturePre
    filename = filePre + key.lower().replace(' ', '-').replace(',','').replace('.','') + '.csv'
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
            'filename': row['filename'],
            'width': row['width'],
            'height': row['height']
        }

dimensionsData = []
with open(dimensionsFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dimensionsData.append(row)

literatureData = []
with open(literatureFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        literatureData.append(row)

literatureLinksData = []
with open(literatureLinksFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        literatureLinksData.append(row)

seriesData = []
with open(seriesFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        seriesData.append(row)

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
    record = addDimensionData(record)
    record = addLiteratureData(record)
    record = addCuratedDataForLiterature(record)
    record = addSeriesData(record)
    
    collection.clear()
    collection.append(record)
    outputFile = outputDirectory + outputPrefix + record.find("InvNr").text + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, encoding='UTF-8', pretty_print=True))
        f.close()