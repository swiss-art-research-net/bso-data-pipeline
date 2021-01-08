import sys
from lxml import etree
from tqdm import tqdm

limit = int(sys.argv[1]) if len(sys.argv) >1 else 999999
offset = int(sys.argv[2]) if len(sys.argv) >2 else 0

inputFile = '/data/source/nb-allRecords.xml'
outputDir = '/data/xml/nb'

root = etree.parse(inputFile)
collection = root.getroot()
records = root.findall("Record")

for record in tqdm(records[offset:limit]):
    collection.clear()
    id = record.get("Id")
    collection.append(record)
    outputFile = "%s/nb-record-%s.xml" % (outputDir, id)
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(collection, xml_declaration=True, pretty_print=True, encoding="UTF-8"))