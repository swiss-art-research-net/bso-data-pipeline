import re
import sys
import yaml
from string import Template

if len(sys.argv) < 2:
    exit("Please provide path to field definition YAML file")

fieldDefinitionsFile = sys.argv[1]
output = ''

with open(fieldDefinitionsFile, 'r') as f:
    model = yaml.safe_load(f.read())

template = Template("""
    INSERT {
        ?subject <$uri> ?value
    } WHERE {
        $query
    };
""")

for field in model['fields']:
    uri = model['prefix'] + field['id']
    selectQuery = [d for d in field['queries'] if 'select' in d.keys()][0]['select']
    matches = re.findall(r'{(.*)}$', selectQuery)
    if matches:
        selectQueryPart = matches[0]
    query = template.substitute(uri=uri, query=selectQueryPart)
    output += query

print(output)