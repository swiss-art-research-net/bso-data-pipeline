import copy
import csv
import re
import unicodedata
import sys
from lxml import etree
from tqdm import tqdm

limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0
idsToOutput=str(sys.argv[3]) if len(sys.argv) >3 else False

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
externalDescriptorsFile = "../data/source/nb-external-descriptors.csv"

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

# Extract all Record elements. We will further work with this representation of the data
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

# Some fields that contain the URL to the image on wikimedia (Element ID 11040) contain the same link twice 
# (often url encoded and not url encoded), separated by a newline. Here we remove the second value
for record in records:
    imageElement = record.find('.//DataElement[@ElementId="11040"]')
    if imageElement is not None and "\n" in imageElement.find('./ElementValue/TextValue').text:
        values = imageElement.find('./ElementValue/TextValue').text.split("\n")
        imageElement.find('./ElementValue/TextValue').text = values[0]
    

# Process DataElements that have several values in one ElementValue by splitting the TextValue and adding extra ElementValues
#
# For example in ID 476941 the Element 10927 contains a TextValue that refers to two artists:
#
#            <DataElement ElementName="KünstlerIn" ElementId="10927" ElementType="Memo (max. 4000 Z.)" ElementTypeId="7">
#              <ElementValue Sequence="1">
#                <TextValue>Aberli, Johann Ludwig [MalerIn/ZeichnerIn];
#Zingg, Adrian [StecherIn]</TextValue>
#               </ElementValue>
#            </DataElement>
#            
# This should become:
#
#            <DataElement ElementName="KünstlerIn" ElementId="10927" ElementType="Memo (max. 4000 Z.)" ElementTypeId="7">
#              <ElementValue Sequence="1-0">
#                <TextValue>Aberli, Johann Ludwig [MalerIn/ZeichnerIn]</TextValue>
#              </ElementValue>
#              <ElementValue Sequence="1-1">
#                <TextValue>Zingg, Adrian [StecherIn]</TextValue>
#              </ElementValue>
#            </DataElement>

elementIdsWithMultipleNames = ['10817', '10927']
dataElementXPath = '|'.join(["DetailData/DataElement[@ElementId='%s']" % d for d in elementIdsWithMultipleNames])

for record in records:
    dataElementsContainingNames = record.xpath(dataElementXPath)
    if len(dataElementsContainingNames):
        for dataElement in dataElementsContainingNames:
            elementValues = dataElement.findall('./ElementValue')
            for elementValue in elementValues:
                text = elementValue.find("./TextValue").text
                if ";" in text:
                    # Extract data
                    values = text.split(";\n")
                    sequence = elementValue.get("Sequence")
                    # Remove ElementValue
                    dataElement.remove(elementValue)
                    # Create new ElementValue elements for each value
                    for i, value in enumerate(values):
                        newElementValue = etree.SubElement(dataElement, "ElementValue")
                        newElementValue.set("Sequence", "%s-%d" % (sequence, i))
                        newTextValue = etree.SubElement(newElementValue, "TextValue")
                        newTextValue.text = value

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

# Helper functions for matching the names and roles
def cleanName(name):
    return re.sub(r'[^A-Za-z]+', '', name)

def matchNameWithCuratedNames(name, curatedNames):

    def NFD(s):
        return unicodedata.normalize('NFD', s)

    for curatedName in curatedNames:
        if NFD(name) in NFD(curatedName['Raw']):
            return curatedName['normalised name']
            
    print("Not found ", name)
    return False

def matchRoleWithCuratedNames(name, curatedNames):
    # We use the name list to match roles as well. Eventually one could use a smaller list of only the roles as well
    for curatedName in curatedNames:
        if curatedName['normalised role'] and curatedName['Role'] in name:
            roles = curatedName['normalised role'].split("/") 
            gndRoles = curatedName['gnd role'].split(";")
            returnRoles = []
            for i in range(min(len(roles), len(gndRoles))):
                returnRoles.append({"label": roles[i], "gnd": gndRoles[i]})
            return returnRoles
    return False

elementIdsWithCuratedNames = ['10817', '10927']
dataElementXPath = '|'.join(["DetailData/DataElement[@ElementId='%s']" % d for d in elementIdsWithCuratedNames])

# Create a helper class to identify Person Descriptors among all records if no suitable
# Descriptor is present with the record itself. The Class will suggest a matching and store
# the matching in a CSV file for later retrieval or manual adjustment

class NBExternalDescriptors:
    import csv
    
    allPersonDescriptors = []
    personDescriptorIdNameHash = {}
    externalDescriptors = []
    externalDescriptorFilename = ""
    
    def __init__(self, records, filename):
        from os import path
        # Read all Person descriptors
        for record in records:
            recordDescriptors = record.xpath("Descriptors/Descriptor[Thesaurus/text()='Personen']")
            for descriptor in recordDescriptors:
                idName = descriptor.find("IdName").text
                if idName not in self.personDescriptorIdNameHash:
                    self.personDescriptorIdNameHash[idName] = len(self.allPersonDescriptors)
                    self.allPersonDescriptors.append(descriptor)
                    
        # Read external descriptors
        self.externalDescriptorFilename = filename
        if path.isfile(filename):
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.externalDescriptors.append(row)
    
    def cleanName(name):
        return re.sub(r'[^A-Za-z]+', '', name)

    def getDescriptorForRecordAndName(self, recordId, name):
        for externalDescriptor in self.externalDescriptors:
            if externalDescriptor['recordId'] == recordId and externalDescriptor['matchedName'] == name:
                return self.allPersonDescriptors[self.personDescriptorIdNameHash[externalDescriptor['idName']]]
        return False
    
    def getPersonDescriptorByName(self, recordId, name):
        for descriptor in self.allPersonDescriptors:
            idName = descriptor.find("IdName").text
            if cleanName(name) in cleanName(idName):
                if not self.getDescriptorForRecordAndName(recordId, name):
                    self.addExternalDescriptor(recordId, matchedName, idName)
                return descriptor
        return False
    
    def addExternalDescriptor(self, recordId, matchedName, idName):
        self.externalDescriptors.append({
            "recordId": recordId,
            "matchedName": matchedName,
            "idName": idName
        })
        self.writeExternalDescriptors()
    
    def writeExternalDescriptors(self):
        externalDescriptors = sorted(self.externalDescriptors, key=lambda k: k['recordId']) 
        with open(self.externalDescriptorFilename, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=externalDescriptors[0].keys())
            writer.writeheader()
            for row in externalDescriptors:
                writer.writerow(row)


externalDescriptors = NBExternalDescriptors(records, externalDescriptorsFile)

# Find a match for each person and add curate data on role
print("Processing Descriptors")
for record in tqdm(records):
    
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
                            break
                    else:
                        # Sometimes no descriptor is present together with the record
                        # but there are matching descriptors elswehere in the dataset.
                        # Here we look for a suitable descriptors among all of them
                        descriptor = externalDescriptors.getDescriptorForRecordAndName(record.get('Id'), matchedName)
                        if descriptor == False:
                            descriptor = externalDescriptors.getPersonDescriptorByName(record.get('Id'), matchedName)
                        if descriptor != False:
                            value.append(copy.deepcopy(descriptor))

                    # Add a normalised name so we can create a single entity for
                    # persons that lack a GND identifier
                    normalisedName = etree.SubElement(value, "NormalisedName")
                    normalisedName.text = matchedName
                else:
                    print("Unmatched name in Record", record.get('Id'))

                matchedRoles = matchRoleWithCuratedNames(name, curatedNames)
                if matchedRoles:
                    for role in matchedRoles:
                        roleElement = etree.SubElement(value, "Role")
                        roleElement.set("gnd", role['gnd'])
                        roleElement.text = role['label']

# Records contain date description as date ranges
#
# Date ranges are specified using different Date Operators, for example
# whether a date range specifes an exact date, or a period, before or after a date.
# However, if the date is not a range, but a single date, only the FromDate
# tag is filled, whether or not the date refers to a beginnig or end of an (unknown)
# range. For easier mapping, we move some of the dates to the ToDate tag, for example
# when a date Range is specified as "before", we want the date to be in ToDate, but not
# in FromDate
#
# We also add the full date information for easier representation as xsd:date later

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

# Switch from/to dates for "before" and "To" date ranges
dateRanges = root.xpath("//DateRange")
for dateRange in dateRanges:
    operator = dateRange.get("DateOperator")
    if operator == "before" or operator == "To":
        fromDate = dateRange.find("FromDate")
        toDate = dateRange.find("ToDate")
        toDate.text = fromDate.text
        fromDate.text = ""

# For each date element add full date information
dates = root.xpath("//FromDate|//ToDate")
for date in dates:
    fullDate = getDateForDateElement(date)
    if fullDate:
        date.set("fullDate", fullDate)

collection = root

# Add an additional tag to Descriptors which is used for generating the URIs.
# If no GND is present, the IdName can be used. However, the IdName sometimes
# contains additional whitespace, which can cause same entities to produce
# different URIs. Therefore, we add an additional tag here with a cleaned
# version of the IdName
for record in records:
    recordDescriptors = record.findall("Descriptors/Descriptor")
    for d in recordDescriptors:
        idName = d.find("IdName").text
        cleandIdName = idName.replace(" ","")
        mappingIdNameElement = etree.SubElement(d, "IdNameForMapping")
        mappingIdNameElement.text = cleandIdName

# Filter ids to output if argument is set
if idsToOutput:
    listOfIds = idsToOutput.split(',')
    records = [d for d in records if d.get("Id") in listOfIds]

# Output each record individually
print("Outputting Files")
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