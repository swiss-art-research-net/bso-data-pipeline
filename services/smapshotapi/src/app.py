import json
import os
import sys
from flask import Flask, Response, request
from lib.SmapshotConnector import SmapshotConnector

try:
  token = os.environ['SMAPSHOT_TOKEN']
except:
  print("SMAPSHOT_TOKEN environment variable not set.")
  sys.exit(1)

try:
  endpoint = os.environ['SMAPSHOT_ENDPOINT']
except:
  print("SMAPSHOT_ENDPOINT environment variable not set.")
  sys.exit(1)

app = Flask(__name__)

smapshot = SmapshotConnector(url = endpoint, token = token)

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
      VALUES(?type ?image_id ?iiif_url ?regionByPx) {
        ("updateImageRegion" "210758" <https://www.e-rara.ch/zuz/i3f/v20/12581613> "35,28,2196,1445")
      }
    }

  Given this query the function will return the following data:   

  [{
    "type": "updateImageRegion",
    "image_id": "210758",
    "iiif_url": "https://www.e-rara.ch/zuz/i3f/v20/12581613",
    "regionByPx": "35,28,2196,1445"
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
        if not 'iiif_url' in row or not 'regionByPx' in row or not 'image_id' in row:
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
  r = smapshot.setImageRegion(data['image_id'], data['iiif_url'], [int(d) for d in data['regionByPx'].split(",")])
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

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)