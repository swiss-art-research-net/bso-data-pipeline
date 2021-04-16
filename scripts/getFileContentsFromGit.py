import base64
import requests
import json
import re
import sys
from urllib.request import urlopen

# Call with arguments:
# 1: GitHub username
# 2: GitHub personal access token
# 3: Repository
# 4: path to file
if len(sys.argv) < 5:
    sys.stderr.write("Insufficient arguments\n")
    exit()
username = sys.argv[1]
token = sys.argv[2]
repo = sys.argv[3]
path = sys.argv[4]
localfile = sys.argv[5]

folder = path.rsplit('/',1)[0]
file = path.rsplit('/',1)[1]

folderURL = 'https://api.github.com/repos/' + repo + '/contents/' + folder
folderRequest = requests.get(folderURL, auth=(username, token))
folderData = folderRequest.json()

try:
    requestedFile = [d for d in folderData if d['name'] == file][0]
except:
    sys.stderr.write("could not find file %s in path %s\n" % (file, folderURL))
    exit()

fileURL = 'https://api.github.com/repos/' + repo + '/git/blobs/' + requestedFile['sha']
fileRequest = requests.get(fileURL, auth=(username, token))

# Output to console

result = base64.b64decode( fileRequest.json()['content'] ).decode('UTF-8', 'ignore')
if not "https://git-lfs.github.com/spec/v1" in result:
    with open(localfile, 'w', encoding='utf-8') as f:
        f.write(result)
else:
    # Download from GIT LFS
    sha = re.findall(r'sha256:([a-z0-9]*)', result)[0]
    size = int(re.findall(r'size ([0-9]*)', result)[0])

    url =  "https://github.com/" + repo + ".git/info/lfs/objects/batch"
    data = {
        'operation': 'download', 
        'transfer': ['basic'], 
        'objects': [
            {'oid': sha, 'size': size}
        ]}
    headers = {'Content-type': 'application/json', 'Accept': 'application/vnd.git-lfs+json'}

    r = requests.post(url, data=json.dumps(data), headers=headers, auth=(username, token))
    downloadurl = r.json()['objects'][0]['actions']['download']['href']

    response = requests.get(downloadurl, stream=True)
    totalLength = response.headers.get('content-length')

    f = open(localfile, 'w', encoding='utf-8')

    if totalLength is None: # no content length header
        f.write(response.content.decode('UTF-8', 'ignore'))
    else:
        dl = 0
        totalLength = int(totalLength)
        for data in response.iter_content(chunk_size=4096):
            dl += len(data)
            f.write(data.decode('UTF-8', 'ignore'))
            done = int(50 * dl / totalLength)
            sys.stderr.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
            sys.stderr.flush()