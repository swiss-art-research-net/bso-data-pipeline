from lxml import etree
import json

inputFile = "../input/sari_abzug-utf-8_23_04-tsv.txt"
outputDirectory = "../input/"
outputPrefix = "sari-"

with open(inputFile, 'r') as f:
    rawData = json.load(f)

keys = list(rawData['rows'][0].keys())
keys.sort()

for row in rawData['rows']:
    records = etree.Element("records")
    record = etree.SubElement(records, "record")
    etree.SubElement(record, "uuid").text = row['UUID']
    prevKey = ''
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
    outputFile = outputDirectory + outputPrefix + row['UUID'] + ".xml"
    with open(outputFile, 'wb') as f:
        f.write(etree.tostring(records, xml_declaration=True, encoding='UTF-8', pretty_print=True))