import json
import requests
import threading
import urllib

inputFile = "../input/sari_abzug-utf-8_23_04-tsv.txt"
manifestDirectory = "../manifests/"
limitFrom = 100
limitTo = 200 

def fetchManuscript(url, filename):
    urlHandler = urllib.request.urlopen(url)
    data = urlHandler.read()
    content = json.loads(data.decode('utf-8'))
    with open(filename, 'w') as f:
        json.dump(content, f, indent=4)

with open(inputFile, 'r') as f:
    rawData = json.load(f)

rowsWithManifests = [d for d in rawData['rows'] if d['manifest'] is not None]

urlsAndFilenames = [{
    "manifest": d['manifest'],
    "filename": manifestDirectory + urllib.parse.quote(d['manifest'], safe='') + '.json'
} for d in rowsWithManifests]


threads = [threading.Thread(target=fetchManuscript, args=(d['manifest'], d['filename'])) for d in urlsAndFilenames[limitFrom:limitTo]]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()