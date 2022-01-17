"""
Script to ingest named graphs from a Trig file into a SPARQL endpoint.
An update condition can be specified as an ASK query. Only graphs at the endpoint that match the ASK query will be updated with data from the Trig file.
Graphs that do not match the ASK query will be left unchanged.

Arguments:
--inputfile: The Trig file to ingest
--endpoint: The SPARQL endpoint
--updatecondition (optional): An ASK query to determine which graphs should be updated.
--preprocessupdate (optional): A SPARQL update query which will be executed before comparing the graphs.

--limit (optional, for debugging): The maximum number of graphs to process
--offset (optional, for debugging): The offset to start processing at

Example:
python update-named-graphs.py \
    --inputfile ./graphs/data.trig \
    --endpoint http://localhost:8080/blazegraph/sparql \
    --updatecondition "ASK { ?s <http://www.cidoc-crm.org/cidoc-crm/P33_used_specific_technique> <https://github.com/swiss-art-research-net/bso-image-segmentation> .}"
    --preprocessupdate "DELETE { ?container <http://www.w3.org/ns/prov#generatedAtTime> ?dateTime } WHERE { ?container a <http://www.w3.org/ns/ldp#Resource>; <http://www.w3.org/ns/prov#generatedAtTime> ?dateTime .}
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
    preprocessupdate = options['preprocessupdate']
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
            elif graphsAreTheSame(context, remoteGraph, preprocessupdate):
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

def clone_graph(source_graph, target_graph=None, identifier=None):
    """
    Make a clone of the source_graph by directly copying triples from source_graph to target_graph
    :param source_graph:
    :type source_graph: rdflib.Graph
    :param target_graph:
    :type target_graph: rdflib.Graph|None
    :param identifier:
    :type identifier: str | None
    :return: The cloned graph
    :rtype: rdflib.Graph
    """
    import rdflib
    if isinstance(source_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
        return clone_dataset(source_graph, target_ds=target_graph)
    if target_graph is None:
        g = rdflib.Graph(identifier=identifier)
        for p, n in source_graph.namespace_manager.namespaces():
            g.namespace_manager.bind(p, n, override=True, replace=True)
    else:
        g = target_graph
        for p, n in source_graph.namespace_manager.namespaces():
            g.namespace_manager.bind(p, n, override=False, replace=False)
    for t in iter(source_graph):
        g.add(t)
    return g 

def graphsAreTheSame(g1, g2, preprocessupdate=None):
    g1Copy = clone_graph(g1)
    g2Copy = clone_graph(g2)
    if preprocessupdate:
        g1Copy.update(preprocessupdate)
        g2Copy.update(preprocessupdate)
    return compare.to_isomorphic(g1Copy) == compare.to_isomorphic(g2Copy)

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
    if not 'preprocessupdate' in options:
        options['preprocessupdate'] = False
    if not 'limit' in options:
        options['limit'] = 999999
    if not 'offset' in options:
        options['offset'] = 0
    performUpdate(options)