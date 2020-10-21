from tqdm import tqdm
import json
import requests
import threading
import urllib
import sys

inputFile = "../input/sari_abzug-utf-8_23_04-tsv.txt"
manifestDirectory = "../manifests/"
offset = 0 if not len(sys.argv) > 1 else int(sys.argv[1])
limit = 1000 if not len(sys.argv) > 2 else int(sys.argv[2])

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
        exit()
        

with open(inputFile, 'r') as f:
    rawData = json.load(f)

rowsWithManifests = [d for d in rawData['rows'] if d['manifest'] is not None]

urlsAndFilenames = [{
    "manifest": d['manifest'],
    "filename": manifestDirectory + urllib.parse.quote(d['manifest'], safe='') + '.json'
} for d in rowsWithManifests]

for row in tqdm(urlsAndFilenames[offset:offset + limit]):
    fetchManuscript(row['manifest'], row['filename'])

# threads = [threading.Thread(target=fetchManuscript, args=(d['manifest'], d['filename'])) for d in urlsAndFilenames[offset:offset + limit]]
# for thread in threads:
#     thread.start()
# for thread in threads:
#     thread.join()