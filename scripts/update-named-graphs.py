"""
Script to ingest named graphs from a Trig file into a SPARQL endpoint.
An update condition can be specified as an ASK query. Only graphs at the endpoint that match the ASK query will be updated with data from the Trig file.
Graphs that do not match the ASK query will be left unchanged.

Arguments:
--inputfile: The Trig file to ingest
--endpoint: The SPARQL endpoint
--updatecondition (optional): An ASK query to determine which graphs should be updated.

--limit (optional, for debugging): The maximum number of graphs to process
--offset (optional, for debugging): The offset to start processing at

Example:
python update-named-graphs.py \
    --inputfile ./graphs/data.trig \
    --endpoint http://localhost:8080/blazegraph/sparql \
    --updatecondition "ASK { ?s <http://www.cidoc-crm.org/cidoc-crm/P33_used_specific_technique> <https://github.com/swiss-art-research-net/bso-image-segmentation> .}"
"""

import requests
import sys
from urllib.parse import quote_plus as urlencode
from rdflib import Dataset, Graph, compare
from tqdm import tqdm

def performUpdate(options):
    endpoint = options['endpoint']
    inputFile = options['inputfile']
    updateCondition = options['updatecondition']
    limit = int(options['limit'])
    offset = int(options['offset'])

    inputData = Dataset()

    print("Parsing input data...")
    devnull = inputData.parse(inputFile, format='trig')
    print("Found %d named graphs" % len([d for d in list(inputData.contexts()) if d.identifier.startswith("http")]))

    headers = {'Accept': 'text/turtle'}

    # Query the endpoint and determine which graphs are new, changed, or unchanged
    graphs= {
        'new': [],
        'changed': [],
        'unchanged': []
    }

    queryTemplate = """
    CONSTRUCT { ?s ?p ?o } WHERE { GRAPH <%s> { ?s ?p ?o }}
    """

    print("Comparing with named graphs at endpoint %s" % endpoint)
    for context in tqdm([d for d in list(inputData.contexts()) if d.identifier.startswith("http")][offset:offset+limit]):
        r = requests.get(endpoint, headers=headers, params={"query": queryTemplate % context.identifier})
        if r.ok:
            remoteGraph = Graph()
            remoteGraph.parse(data=r.text, format='turtle')
            if not len(remoteGraph):
                graphs['new'].append((context, False))
            elif compare.to_isomorphic(context) == compare.to_isomorphic(remoteGraph):
                graphs['unchanged'].append((context, remoteGraph))
            else:
                graphs['changed'].append((context, remoteGraph))

        else:
            print(r.text)

    # Output statistics:
    print("\nComparison Result:")
    print("%d graph%s %s not exist at the endpoint and will be added" % (len(graphs['new']), "" if len(graphs['new']) == 1 else "s", "does" if len(graphs['new']) == 1 else "do"))
    print("%d graph%s already exist%s but %s different in the input file" % (len(graphs['changed']), "" if len(graphs['changed']) == 1 else "s", "s" if len(graphs['changed']) == 1 else "", "is" if len(graphs['changed']) == 1 else "are"))
    print("%d graph%s %s identical in both the input file and endpoint" % (len(graphs['unchanged']), "" if len(graphs['unchanged']) == 1 else "s", "is" if len(graphs['unchanged']) == 1 else "are"))

    # All new graphs should be included in the update
    graphsToUpdate = [d[0] for d in graphs['new']]

    # Only graphs where the new graph matches the update condition should be updated
    # If no update condition is set, all changed should be updated
    if updateCondition:
        count = 0
        for graphPair in graphs['changed']:
            for result in graphPair[1].query(updateCondition):
                if result:
                    graphsToUpdate.append(graphPair[0])
                    count += 1
        print("\n%d out of %d graph%s will be overwritten based on the update condition" % (count, len(graphs['changed']), "" if len(graphs['changed']) == 1 else "s"))
    else:
        graphsToUpdate += [d[0] for d in graphs['changed']]
            
    # Perform update
    for g in tqdm(graphsToUpdate):
        putGraph(g, endpoint)

def putGraph(context, endpoint):
    # Remove old graph
    r = requests.post(endpoint, params={"update": "DROP GRAPH <%s>" % context.identifier})
    
    # Add new graph
    data = context.serialize(format='turtle')
    params = {
        "context-uri": context.identifier,
    }
    headers = {"Content-Type" : "text/turtle"}
    r = requests.post(endpoint, params=params, data=data, headers=headers)
    return r.ok

if __name__ == "__main__":
    options = {}
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith("--"):
            if not sys.argv[i + 2].startswith("--"):
                options[arg[2:]] = sys.argv[i + 2]
            else:
                print("Malformed arguments")
                sys.exit(1)
    if not 'endpoint' in options:
        print("A SPARQL endpoint needs to be specified via the --endpoint argument")
        sys.exit(1)
    if not 'inputfile' in options:
        print("An input file needs to be specified via the --inputfile argument")
        sys.exit(1)
    if not 'updatecondition' in options:
        options['updatecondition'] = False
    if not 'limit' in options:
        options['limit'] = 999999
    if not 'offset' in options:
        options['offset'] = 0
    performUpdate(options)