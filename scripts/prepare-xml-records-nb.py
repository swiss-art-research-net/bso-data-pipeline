import re
import sys
from lxml import etree
from tqdm import tqdm

limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0

inputFile = '/data/source/nb-allRecords.xml'
outputDir = '/data/xml/nb'

root = etree.parse(inputFile)

def getDateForDateElement(date):
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

dates = root.xpath("//FromDate|//ToDate")
for date in dates:
    fullDate = getDateForDateElement(date)
    if fullDate:
        date.set("fullDate", fullDate)

collection = root.getroot()
records = root.findall("Record")

def convertSwissGridToLatLong(x, y):
    # https://www.swisstopo.admin.ch/en/maps-data-online/calculation-services/navref.html
    # Example: https://geodesy.geo.admin.ch/reframe/navref?format=json&easting=683195&northing=248031&altitude=NaN&input=lv03&output=etrf93-ed
    import requests
    from string import Template
    urlTemplate = Template("https://geodesy.geo.admin.ch/reframe/navref?format=json&easting=$x&northing=$y&altitude=NaN&input=lv03&output=etrf93-ed")
    url = urlTemplate.substitute(x=x, y=y)
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except:
        print("No connection")
    return False

for record in tqdm(records[offset:limit+offset]):
    xCoord = record.xpath("DetailData/DataElement[@ElementId='10161']/ElementValue/TextValue")
    yCoord = record.xpath("DetailData/DataElement[@ElementId='10162']/ElementValue/TextValue")
    if len(xCoord) and len(yCoord):
        x = xCoord[0].text
        y = yCoord[0].text
        coordinates = convertSwissGridToLatLong(x, y)
        elemCoord = etree.SubElement(record, "Coordinates")
        elemCoord.set("longitude", coordinates['easting'])
        elemCoord.set("latitude", coordinates['northing'])

for record in tqdm(records[offset:limit+offset]):
    collection.clear()
    id = record.get("Id")
    collection.append(record)
    outputFile = "%s/nb-record-%s.xml" % (outputDir, id)
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, pretty_print=True, encoding="UTF-8"))