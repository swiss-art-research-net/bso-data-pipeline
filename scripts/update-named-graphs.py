"""
Script to ingest named graphs from a Trig file into a SPARQL endpoint.
An update condition can be specified as an ASK query. Only graphs that match the ASK query will be updated with data from the Trig file.
Graphs that do not match the ASK query will be left unchanged

Arguments:
--inputfile: The Trig file to ingest
--endpoint: The SPARQL endpoint
--updateCondition (optional): An ASK query to determine which graphs should be updated

Example:
python update-named-graphs.py \
    --inputfile ./graphs/data.trig \
    --endpoint http://localhost:8080/blazegraph/sparql \
    --updateCondition "ASK { ?s <http://www.cidoc-crm.org/cidoc-crm/P33_used_specific_technique> <https://github.com/swiss-art-research-net/bso-image-segmentation> .}"
"""

import requests
import sys
from urllib.parse import quote_plus as urlencode
from rdflib import Dataset, Graph, compare
from tqdm import tqdm

def performUpdate(options):
    endpoint = options['endpoint']
    inputFile = options['inputfile']
    updateCondition = options['updateCondition']

    inputData = Dataset()
    devnull = inputData.parse(inputFile, format='trig')

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

    print("Comparing graphs")
    for context in tqdm(inputData.contexts()):
        if context.identifier.startswith("http"):
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
    print("\nGraphs to be updated:")
    print(len(graphs['new']), "new ")
    print(len(graphs['changed']), "updated")
    print(len(graphs['unchanged']), "unchanged")

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
        print("%d graph%s will be overwritten" % (count, "s" if count == 1 else ""))
    else:
        graphsToUpdate += [d[0] for d in graphs['changed']]
            
    # Perform update
    for g in tqdm(graphsToUpdate):
        putGraph(g, endpoint)

def putGraph(context, endpoint):
    # Remove old graph
    requests.get(endpoint, params={"query": "DROP GRAPH <%s>" % context.identifier})
    
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
            options[arg[2:]] = sys.argv[i + 2]
    performUpdate(options)