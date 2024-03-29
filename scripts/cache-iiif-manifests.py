from os.path import isfile
from tqdm import tqdm
import csv
import json
import requests
import threading
import urllib
import sys

inputFile = "../data/source/zbz-dois.csv"
manifestDirectory = "../data/manifests/"
offset = 0 if not len(sys.argv) > 1 else int(sys.argv[1])
limit = 99999 if not len(sys.argv) > 2 else int(sys.argv[2])

def fetchManuscript(url, filename):
    try:
        urlHandler = urllib.request.urlopen(url)
        data = urlHandler.read()
        content = json.loads(data.decode('utf-8'))
        with open(filename, 'w') as f:
            json.dump(content, f, indent=4)
    except urllib.error.HTTPError as e:
        print(e)
        print(url)        
        

with open(inputFile, 'r') as f:
    rawData = []
    reader = csv.DictReader(f)
    for row in reader:
        rawData.append(row)

rowsWithManifests = [d for d in rawData if d['manifest'] is not None]

urlsAndFilenames = [{
    "manifest": d['manifest'],
    "filename": manifestDirectory + urllib.parse.quote(d['manifest'], safe='') + '.json'
} for d in rowsWithManifests]

for row in tqdm(urlsAndFilenames[offset:offset + limit]):
    if not isfile(row['filename']):
        if row['manifest']:
            fetchManuscript(row['manifest'], row['filename'])
