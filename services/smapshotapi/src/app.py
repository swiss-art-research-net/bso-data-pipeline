import json
import os
import requests
import sys
from flask import Flask, Response, request
from lib.SmapshotConnector import SmapshotConnector
from sariSparqlParser import parser
from string import Template
from rdflib.term import Variable, URIRef, Literal

try:
  token = os.environ['SMAPSHOT_TOKEN']
except:
  print("SMAPSHOT_TOKEN environment variable not set.")
  sys.exit(1)

try:
  smapshotEndpoint = os.environ['SMAPSHOT_ENDPOINT']
except:
  print("SMAPSHOT_ENDPOINT environment variable not set.")
  sys.exit(1)

try:
  sparqlEndpoint = os.environ['SPARQL_ENDPOINT']
except:
  print("SPARQL_ENDPOINT environment variable not set.")
  sys.exit(1)

try:
  namedGraph = os.environ['SMAPSHOT_NAMEDGRAPH']
except:
  print("SMAPSHOT_NAMEDGRAPH environment variable not set.")
  sys.exit(1)

app = Flask(__name__)

smapshot = SmapshotConnector(url = smapshotEndpoint, token = token)

def error(message):
  """
  Generate a JSON error object
  """
  return {"error": message}

def addImage(data):
  """
  Adds a new image
  """
  r = smapshot.addImage(
    regionByPx=[int(d) for d in data['regionByPx'].split(",")], 
    iiif_url=data['iiif_url'], 
    is_published=True if data['is_published'] else False, 
    original_id=data['original_id'], 
    title=data['title'], 
    collection_id=int(data['collection_id']), 
    view_type=data['view_type'], 
    license=data['license'], 
    observation_enabled=True if data['observation_enabled'] else False, 
    correction_enabled=True if data['correction_enabled'] else False,
    height=int(data['height']),
    width=int(data['width']),
    date_orig=data['date_shot'],
    date_shot_min=data['date_min'][:10] if 'date_min' in data else None,
    date_shot_max=data['date_max'][:10] if 'date_max' in data else None,
    longitude=float(data['longitude']),
    latitude=float(data['latitude']),
    photographer_ids=[int(d) for d in data['photographer_ids'].split(",")]
  )
  if 'id' in r:
    # Add smapshot ID to Platform
    response = addSmapshotIdentifierForObject(r['id'], data['original_id'])
    r['backendResponse'] = json.dumps(response)
    if response['status_code'] != 200:
      r['status'] = response['status_code']
  return r

def addPhotographer(data):
  """
  Adds a new photograoher
  """
  r = smapshot.addPhotographer(firstname=data['firstname'] if 'firstname' in data else '', lastname=data['lastname'], company='SARI', link=data['link'])
  return r

def addSmapshotIdentifierForObject(smapshotId, originalId):
  uri = "https://resource.swissartresearch.net/artwork/" + originalId
  graphTemplate = Template("""
  @prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
  <$objectIri> crm:P1_is_identified_by <$objectIri/id/smapshot> .
  <$objectIri/id/smapshot> a crm:E42_Identifier ;
    crm:P2_has_type <https://smapshot.heig-vd.ch> ;
    rdfs:label "$smapshotId" .
  """)
  data = graphTemplate.substitute(objectIri=uri, smapshotId=smapshotId)
  response = requests.post(data=data, url=sparqlEndpoint, params={'context-uri': namedGraph}, headers={'Content-Type': 'application/x-turtle'})
  return { 
    'url': response.request.url,
    'status_code': response.status_code,
    'data': data
    }

def createSparqlResponse(parsedQuery, processedRequests):
  """
  Accepts a parsed SPARQL select query and the results of processing the requests. 
  Returns a SPARQL response.

  Processed requests can look like this:

    [
      {
        "smapshot_id": "1839",
        "uri": "https://resource.swissartresearch.net/actor/DEF6590A-1AAF-39C6-9581-91C315E78BCB",
        "name": "Tanner, Johann Jakob [MalerIn/ZeichnerIn]"
      },
      {
        "smapshot_id": "1615",
        "uri": "https://resource.swissartresearch.net/actor/0E131DCC-CA73-3A11-9700-E7E40EB9D256/and/DEF6590A-1AAF-39C6-9581-91C315E78BCB",
        "name": "Winterlin, Anton [MalerIn/ZeichnerIn] and Tanner, Johann Jakob [MalerIn/ZeichnerIn]"
      },
      ...
    ]

  In response to a SPARQL query that looked like this:
  PREFIX  smapshotapi: <https://smapshot.heig-vd.ch/api/v1/>
    SELECT  ?smapshot_id ?name ?uri WHERE { 
      ?smapshotArtist a smapshotapi:Photographer ;
        smapshotapi:attribute_id ?smapshot_id ;
        smapshotapi:attribute_link ?uri ;
        smapshotapi:attribute_last_name "Tanner" , ?name .
    }
    
  The function creates a list (bindings) with an entry for each row in the request object.
  If a limit and offset is provided, the list is truncated as appropriate.

  The function looks in the select part of the parsed query and returns from the processed
  request the variables that are asked for.

  In addition, information on the type of the returned data is added.
  """
  def getDataTypeForValue(value):
      if isinstance(value, int):
          return "http://www.w3.org/2001/XMLSchema#integer"
      return "http://www.w3.org/2001/XMLSchema#string"

  response = {}
  response['head'] = {
      "vars": parsedQuery['select']
  }
  bindings = []
  for request in processedRequests:
    if parsedQuery['limitOffset']:
      offset = parsedQuery['limitOffset']['offset'] if 'offset' in parsedQuery['limitOffset'] else 0
      limit = parsedQuery['limitOffset']['limit'] if  'limit' in parsedQuery['limitOffset'] else len(request)
    else:
      offset = 0
      limit = len(request)
    for entry in request[offset:offset+limit]:
      row = {}
      for variable in parsedQuery['select']:
        if variable in entry:
          row[variable] = {
            "value": entry[variable],
            "type": "literal",
            "datatype": getDataTypeForValue(entry[variable])
          }
      bindings.append(row)
  response['results'] = {'bindings': bindings}
  return response

def extractRequestFromQueryData(data):
  """
  Given an interpreted SPARQL query this function extracts the request.
  It does so by looking at the triples contained in the WHERE clause.
  
  Consider the following SPARQL query:

    PREFIX  smapshotapi: <https://smapshot.heig-vd.ch/api/v1/>
    SELECT  ?smapshot_id ?name ?uri WHERE { 
      ?smapshotArtist a smapshotapi:Photographer ;
        smapshotapi:attribute_id ?smapshot_id ;
        smapshotapi:attribute_link ?uri ;
        smapshotapi:attribute_last_name "Tanner" , ?name .
    }
    
  The type of a subject determines the type of the request. In this case,
  the request is for a Photographer. The predicates that begin with attribute_
  refer to the attributes available through the sMapshot API. Objects that 
  are variables will be returned. Objects that are Literals will be passed to 
  the sMapshot API.

  The example request is interpreted into a request object. In this case:

    {
      "variable": "smapshotArtist",
      "retrieve": {
        "id": "smapshot_id",
        "link": "uri",
        "last_name": "name"
      },
      "send" : {
        "last_name": "Tanner"
      },
      "requestType": "Photographer"
    }

  A single SPARQL query can contain several requests. All request objects are returned
  as a list.
  """
  smapshotPrefix = 'https://smapshot.heig-vd.ch/api/v1/'
  def getAttribute(value):
      v = getValueWithoutPrefix(value, smapshotPrefix)
      return v[len("attribute_"):]
  
  def getValueWithoutPrefix(value, prefix):
      return value[len(prefix):]
  
  requests = []
  # Find variables with type:
  for triple in data['where']:
      if triple['s']['type'] == Variable and triple['p']['value'] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
          requests.append({
              "variable": triple['s']['value'],
              "retrieve": {},
              "send": {},
              "requestType": getValueWithoutPrefix(triple['o']['value'], smapshotPrefix)})
  for request in requests:
      for triple in data['where']:
          if triple['s']['type'] == Variable and triple['s']['value'] == request['variable']:
              if getValueWithoutPrefix(triple['p']['value'], smapshotPrefix).startswith('attribute_'):
                  if triple['o']['type'] == Variable:
                      request['retrieve'][getAttribute(triple['p']['value'])] = triple['o']['value']
                  if triple['o']['type'] == Literal:
                      request['send'][getAttribute(triple['p']['value'])] = triple['o']['value']

  return requests

def processUpdate(data):
  """
  Routes a update request based on its type and calls the appropriate function.
  """
  for row in data:
    if 'type' in row:
      if row['type'] == "updateImageRegion":
        if not 'iiif_url' in row or not 'regionByPx' in row or not 'image_id' in row:
          return error("Missing parameter for request type " + row['type'])
        return updateImageRegion(row)
      elif row['type'] == "submitImage":
        if not 'iiif_url' in row or not 'photographer_ids' in row or not 'is_published' in row or not 'original_id' in row or not 'title' in row or not 'collection_id' in row or not 'view_type' in row or not 'license' in row or not 'observation_enabled' in row or not 'correction_enabled' in row or not 'height' in row or not 'width' in row or not 'name' in row or not 'date_shot' in row or not 'longitude' in row or not 'latitude' in row or not 'regionByPx' in row:
          return error("Missing parameter for request type " + row['type'])
        return addImage(row)
      elif row['type'] == "addPhotographer":
        if not 'link' in row or not 'lastname' in row:
          return error("Missing parameter for request type " + row['type'])
        return addPhotographer(row)
      else:
        return error("Unknown request type: " + row['type'])
    else:
      return error("No type specified")

def processSmapshotApiRequests(requests):
    """
    Accepts a list of request objects, passes each request to the relevant function
    for processing and returns a list of results for each request.
    """
    ret = []
    for request in requests:
        if request['requestType'] == 'Photographer':
            ret.append(requestPhotographer(request))
    return ret

def processQuery(data):
  """
  Accepts a parsed SPARQL query, extracts and processes the requests and returns a SPARQL response.
  """
  requests = extractRequestFromQueryData(data)
  processedRequests = processSmapshotApiRequests(requests)
  response = createSparqlResponse(data, processedRequests)
  return response

def requestPhotographer(request):
    """
    Accepts a request oject for a photographer and queries the sMapshot API using the given parameters.
    Consider the following request object:
      {
        "variable": "smapshotArtist",
        "retrieve": {
          "id": "smapshot_id",
          "link": "uri",
          "last_name": "name"
        },
        "send" : {
          "last_name": "Tanner"
        },
        "requestType": "Photographer"
      }

    The attributes and values to be sent are extracted from the "send" dictionary and used
    to query the sMapshot API. If the returned status is not 200, the response from the
    sMapshot API is returned. If the response is successful the queried attributes are
    determined based on the "retrieve" dictionary. The function returns, for each row in the
    response, an object with the queried variables as keys and the returned values as values.
    For the above request object, for example:
    [
      {
        "smapshot_id": "1839",
        "uri": "https://resource.swissartresearch.net/actor/DEF6590A-1AAF-39C6-9581-91C315E78BCB",
        "name": "Tanner, Johann Jakob [MalerIn/ZeichnerIn]"
      },
      {
        "smapshot_id": "1615",
        "uri": "https://resource.swissartresearch.net/actor/0E131DCC-CA73-3A11-9700-E7E40EB9D256/and/DEF6590A-1AAF-39C6-9581-91C315E78BCB",
        "name": "Winterlin, Anton [MalerIn/ZeichnerIn] and Tanner, Johann Jakob [MalerIn/ZeichnerIn]"
      },
      ...
    ]

    """
    params = {}
    data = []
    for name, value in request['send'].items():
        params[name] = value
    photographers = smapshot.listPhotographers(params)
    if 'status' in photographers and photographers['status'] != 200:
      return photographers
    for photographer in photographers:
        row = {}
        for key, variable in request['retrieve'].items():
            row[variable] = photographer[key]
        data.append(row)

    return data

def updateImageRegion(data):
  """
  Updates the region of an image.
  """
  r = smapshot.setImageRegion(data['image_id'], data['iiif_url'], [int(d) for d in data['regionByPx'].split(",")])
  return r

@app.route('/')
def index():
  return 'Server Works!'

@app.route('/sparql', methods=['GET', 'POST'])
def sparql():
  """
  Listens for SPARQL Update requests and processes them.
  """
  if request.values:
    p = parser()
    if 'query' in request.values: 
      data = p.parseQuery(request.values['query'])
      response = processQuery(data)
      return Response(json.dumps(response), mimetype='application/json', status=response['status'] if 'status' in response else 200)
    if 'update' in request.values:
      data = p.parseUpdate(request.values['update'])
      # Update queries are interpreted based on the data passed through the VALUES keyword
      values = []
      for d in data['values']:
        row = {}
        for key in d.keys():
          row[key] = d[key]['value']
        values.append(row)
      response = processUpdate(values)
      if 'error' in response:
        return response, 500
      return Response(json.dumps(response), mimetype='application/json', status=response['status'] if 'status' in response else 200)
  return Response("OK", mimetype='application/json')

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)