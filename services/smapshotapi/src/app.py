import json
import os
import sys
from flask import Flask, Response, request
from lib.SmapshotConnector import SmapshotConnector
from sariSparqlParser import parser

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
    p = parser()
    data = p.parseUpdate(request.form['update'])
    values = []
    for d in data['values']:
      row = {}
      for key in d.keys():
        row[key] = d[key]['value']
      values.append(row)
    response = processRequest(values)
    if 'error' in response:
      return response, 500
    return Response(json.dumps(response), mimetype='application/json')
  return Response("OK", mimetype='application/json')

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)