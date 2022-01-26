import json
from flask import Flask, Response, request
from lib.SmapshotConnector import SmapshotConnector

app = Flask(__name__)

with open('token.txt', 'r') as f:
  token = f.read().strip()

smapshot = SmapshotConnector(url = "https://smapshot-beta.heig-vd.ch/api/v1", token = token)

def getDataFromSparqlUpdate(payload):
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
  for row in data:
    if row['type'] == "updateImageRegion":
      return updateImageRegion(row)

def updateImageRegion(data):
  attributes = {
    "iiif_data" : {
      "image_service3_url": data['iiif_url'],
      "region_px": data['region_px']
    }
  }
  return smapshot.setImageAttributes(int(data['image_id']), attributes)

@app.route('/')
def index():
  return 'Server Works!'
  
@app.route('/sparql', methods=['GET', 'POST'])
def sparql():
  if request.form:
    data = getDataFromSparqlUpdate(request.form['update'])
    response = processRequest(data)
    return Response(json.dumps(response), mimetype='application/json')
  return Response("OK", mimetype='application/json')