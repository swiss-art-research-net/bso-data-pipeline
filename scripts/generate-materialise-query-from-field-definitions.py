import re
import sys
import yaml
from string import Template

if len(sys.argv) < 2:
    exit("Please provide path to field definition YAML file")

fieldDefinitionsFile = sys.argv[1]
namedGraph = sys.argv[2] if len(sys.argv) > 2 else False
output = ''

with open(fieldDefinitionsFile, 'r') as f:
    model = yaml.safe_load(f.read())

for prefix in model['namespaces'].keys():
    output += "PREFIX %s: <%s>\n" % (prefix, model['namespaces'][prefix])

if namedGraph:
    output += "DROP GRAPH <%s> ;" % namedGraph
    template = Template("""
        INSERT {
            GRAPH <$graph> {
                ?subject <$uri> ?value .
            }
        } WHERE {
            $query
        };
    """)
else:
    template = Template("""
        INSERT {
            ?subject <$uri> ?value
        } WHERE {
            $query
        };
    """)

for field in model['fields']:
    if 'materialise' in field and field['materialise'] == True:
        uri = model['prefix'] + field['id']
        selectQuery = [d for d in field['queries'] if 'select' in d.keys()][0]['select']
        try:
            selectQueryPart = re.findall(r'{(.*)}\s*$', selectQuery)[0]
        except:
            print("No query found for " + field['id'])
        selectQueryPart = selectQueryPart.replace('$','?').replace('"',"'")
        if namedGraph:
            query = template.substitute(uri=uri, query=selectQueryPart, graph=namedGraph)
        else:
            query = template.substitute(uri=uri, query=selectQueryPart)
        output += query

print(output)