import json
from flask import Flask, Response, request
from lib.SmapshotConnector import SmapshotConnector

app = Flask(__name__)

with open('token.txt', 'r') as f:
  token = f.read().strip()

smapshot = SmapshotConnector(url = "https://smapshot-beta.heig-vd.ch/api/v1", token = token)

def error(message):
  """
  Generate a JSON error object
  """
  return {"error": message}

def getDataFromSparqlUpdate(payload):
  """
  Extracts the data from the VALUES clause of  a SPARQL update request. All other parts of the query are ignored.
  Consider the following query:
  
    PREFIX : <http://www.example.org/>
    INSERT  {
      :s :p :o .
    } WHERE {
      VALUES(?type ?image_id ?iiif_url ?region_px) {
        ("updateImageRegion" "210758" <https://www.e-rara.ch/zuz/i3f/v20/12581613> "[35,28,2196,1445]")
      }
    }

  Given this query the function will return the following data:   

  [{
    "type": "updateImageRegion",
    "image_id": "210758",
    "iiif_url": "https://www.e-rara.ch/zuz/i3f/v20/12581613",
    "region_px": "[35,28,2196,1445]"
  }]

  Each row in the VALUES clause is returned as a JSON object in the list.
  """
  from rdflib.plugins.sparql.parser import parseUpdate
  q = parseUpdate(payload)
  keys = {}
  for i, var in enumerate(q['request'][0]['where']['part'][0]['var']):
      keys[i] = str(var)
  data = []
  for values in q['request'][0]['where']['part'][0]['value']:
      row = {}
      for i, value in enumerate(values):
          if 'string' in value:
              row[keys[i]] = str(value['string'])
          else:
              row[keys[i]] = str(value)
      data.append(row)
  return data

def processRequest(data):
  """
  Routes a request based on its type and calls the appropriate function.
  """
  for row in data:
    if 'type' in row:
      if row['type'] == "updateImageRegion":
        if not 'iiif_url' in row or not 'region_px' in row or not 'image_id' in row:
          return error("Missing parameter for request type " + row['type'])
        return updateImageRegion(row)
      else:
        return error("Unknown request type: " + row['type'])
    else:
      return error("No type specified")

def updateImageRegion(data):
  """
  Updates the region of an image.
  """
  r = smapshot.setImageRegion(int(data['image_id']), data['iiif_url'], data['region_px'])
  app.logger.info(r)
  return r

@app.route('/')
def index():
  return 'Server Works!'
  
@app.route('/sparql', methods=['GET', 'POST'])
def sparql():
  """
  Listens for SPARQL Update requests and processes them.
  """
  if request.form:
    data = getDataFromSparqlUpdate(request.form['update'])
    response = processRequest(data)
    if 'error' in response:
      return response, 500
    return Response(json.dumps(response), mimetype='application/json')
  return Response("OK", mimetype='application/json')