import copy
import csv
import re
import sys
from lxml import etree
from tqdm import tqdm

limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0

# Set paths for input and output files
inputFiles = ['../data/source/nb-records.xml', '../data/source/nb-parentrecords.xml']
outputDir = '/data/xml/nb'

# List externally loaded csv files
# (these files contain data that has been added in open Refine)
curatedDataFiles = [
    "../data/source/nb-curation-personen.csv",
    "../data/source/nb-curation-koerperschaften.csv",
    "../data/source/nb-curation-geografika.csv"
]
curatedNamesFile = "../data/source/nb-curation-names.csv"

# Column in CSV file used to match against IdName
curatedKey = "Raw"

# Columns to add
curatedFieldsToAdd = ["GND-Nummer", "GND-Kennung", "WD"]

# Read input files
root = etree.XML("<Collection/>")
for inputFile in inputFiles:
    collection = etree.parse(inputFile)
    for record in collection.findall("//Record"):
        root.append(record)

records = root.findall("Record")

# Filter records that either don't have an image or don't show up as a parent of another record
parentIDs = []
orphans = []

for record in records:
    parentIDs.append(record.get('ParentId'))

parentIDs = list(set(parentIDs))

for record in records:
    recordID = record.get('Id')
    image = record.find('.//DataElement[@ElementId="11040"]')
    # If record contains no image and is not a parent of another record, mark as orphan
    if image is None and recordID not in parentIDs:
        orphans.append(recordID)

records = [d for d in records if d.get('Id') not in orphans]

# Read all curated data into a list
curatedData = []
for curatedDataFile in curatedDataFiles:
    with open(curatedDataFile, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            curatedData.append(row)

# Read curated names into a list
curatedNames = []
with open(curatedNamesFile, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        curatedNames.append(row)

# For each descriptor add curated data for available Thesaurus
descriptors = root.xpath("//Descriptor")

for descriptor in descriptors:
    thesaurus = descriptor.find("Thesaurus").text
    key = descriptor.find("IdName").text
    try:
        dataToAdd = [d for d in curatedData if d['Thesaurus'] == thesaurus and d[curatedKey] == key][0]
    except:
        continue
    for field in curatedFieldsToAdd:
        if field in dataToAdd:
            el = etree.SubElement(descriptor, field)
            el.text = dataToAdd[field]

# The names in the descriptors do not exactly match the ones used in the DataFields, for example...
#
#   <DataElement ElementName="KünstlerIn" ElementId="10927" ElementType="Memo (max. 4000 Z.)" ElementTypeId="7">
#     <ElementValue Sequence="1">
#       <TextValue>Keller, Hans Heinrich</TextValue>
#     </ElementValue>
#   </DataElement>
#
#  ...has the corresponding Person Element...
#
#   <DataElement ElementName="Personen" ElementId="11053" ElementType="Memo (max. 4000 Z.)" ElementTypeId="7">
#     <ElementValue Sequence="1">
#       <TextValue>BildendeR KünstlerIn  / Personen / K / Keller, Hans Heinrich / 1778 - 1862</TextValue>
#     </ElementValue>
#   </DataElement>
#
#  ...and Descriptor
#
#   <Descriptor>
#     <Name>BildendeR KünstlerIn</Name>
#     <Thesaurus>Personen</Thesaurus>
#     <IdName>BildendeR KünstlerIn  (Personen\K\Keller, Hans Heinrich (1778 - 1862))</IdName>
#     <SeeAlso>Keller, Hans Heinrich (1778 - 1862)</SeeAlso>
#     <GND-Nummer>1018634584</GND-Nummer>
#   </Descriptor>
#
#  Neither the Person Element nor the Descriptor specify the role exactly. They define the person as BilndendeR Künstlerin,
#  but the DataElement can be more specific with regardsd to KünstlerIn or FotografIn (based on current data).
#  
#  Therefore, the Descriptor is added to the relevant DataElement by checking for the occurrence of the TextValue
#  (e.g. Keller, Hans Heinrich) in the Descriptor's IdName (e.g. BildendeR KünstlerIn  (Personen\K\Keller, Hans Heinrich (1778 - 1862)))

# Element IDs in which such names appear
elementIdsWithCuratedNames = ['10817', '10927']

# Helper functions for matching the names and roles
def cleanName(name):
    return re.sub(r'[^A-Za-z]+', '', name)

def matchNameWithCuratedNames(name, curatedNames):
    for curatedName in curatedNames:
        if name in curatedName['Raw']:
            return curatedName['normalised name']
    print("Not found ", name)
    return False

def matchRoleWithCuratedNames(name, curatedNames):
    # We use the name list to match roles as well. Eventually one could use a smaller list of only the roles as well
    for curatedName in curatedNames:
        if curatedName['normalised role'] and curatedName['normalised role'] in name:
            roles = curatedName['normalised role'].split("/") 
            gndRoles = curatedName['gnd role'].split(";")
            returnRoles = []
            for i in range(min(len(roles), len(gndRoles))):
                returnRoles.append({"label": roles[i], "gnd": gndRoles[i]})
            return returnRoles
    return False

dataElementXPath = '|'.join(["DetailData/DataElement[@ElementId='%s']" % d for d in elementIdsWithCuratedNames])

for record in records:
    
    # Extract Elements containing names
    recordElements = record.xpath(dataElementXPath)
    recordDescriptors = record.xpath("Descriptors/Descriptor[Thesaurus/text()='Personen']")
    
    if len(recordElements):
        for recordElement in recordElements:
            # Extract ElementValues (there can be several)
            values = recordElement.xpath("ElementValue")
            for value in values:
                name = value.find("TextValue").text

                matchedName = matchNameWithCuratedNames(name, curatedNames)
                if matchedName:
                    # If a match is found, copy the descriptor directly into the Element
                    for descriptor in recordDescriptors:
                        idName = descriptor.find("IdName").text
                        if cleanName(matchedName) in cleanName(idName):
                            value.append(copy.deepcopy(descriptor))

                matchedRoles = matchRoleWithCuratedNames(name, curatedNames)
                if matchedRoles:
                    for role in matchedRoles:
                        roleElement = etree.SubElement(value, "Role")
                        roleElement.set("gnd", role['gnd'])
                        roleElement.text = role['label']

# Define functions
def getDateForDateElement(date):
    """
        Add day and month information for years
        Jan 1 or Dec 31 depending on whether it is a beginning or end date
    """
    if not date.text:
        return False
        
    patternCeYear = r'\+\d{4}'
    if re.match(patternCeYear, date.text):
        year = date.text[1:].zfill(4)
        if date.tag == 'FromDate':
            return "%s-01-01" % year
        else:
            return "%s-12-31" % year
    return False

# For each date element add full date information
dates = root.xpath("//FromDate|//ToDate")
for date in dates:
    fullDate = getDateForDateElement(date)
    if fullDate:
        date.set("fullDate", fullDate)

# Omit: Coordinates is a deprecated field
#
# 
# def convertSwissGridToLatLong(x, y):
#     # https://www.swisstopo.admin.ch/en/maps-data-online/calculation-services/navref.html
#     # Example: https://geodesy.geo.admin.ch/reframe/navref?format=json&easting=683195&northing=248031&altitude=NaN&input=lv03&output=etrf93-ed
#     import requests
#     from string import Template
#     urlTemplate = Template("https://geodesy.geo.admin.ch/reframe/navref?format=json&easting=$x&northing=$y&altitude=NaN&input=lv03&output=etrf93-ed")
#     url = urlTemplate.substitute(x=x, y=y)
#     try:
#         response = requests.get(url)
#         data = response.json()
#         return data
#     except:
#         print("No connection")
#     return False
# for record in tqdm(records[offset:limit+offset]):
#     xCoord = record.xpath("DetailData/DataElement[@ElementId='10161']/ElementValue/TextValue")
#     yCoord = record.xpath("DetailData/DataElement[@ElementId='10162']/ElementValue/TextValue")
#     if len(xCoord) and len(yCoord):
#         x = xCoord[0].text
#         y = yCoord[0].text
#         coordinates = convertSwissGridToLatLong(x, y)
#         elemCoord = etree.SubElement(record, "Coordinates")
#         elemCoord.set("longitude", coordinates['easting'])
#         elemCoord.set("latitude", coordinates['northing'])

collection = root

# Output each record individually
for record in tqdm(records[offset:limit+offset]):
    collection.clear()
    id = record.get("Id")
    parentId = record.get("ParentId")
    record.set("RecordIdentifier", "nb-" + id)
    record.set("ParentRecordIdentifier", "nb-" + parentId)
    collection.append(record)
    outputFile = "%s/nb-record-%s.xml" % (outputDir, id)
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, pretty_print=True, encoding="UTF-8"))