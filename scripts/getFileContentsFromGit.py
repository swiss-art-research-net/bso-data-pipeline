import base64
import requests
import json
import sys

# Call with arguments:
# 1: GitHub username
# 2: GitHub personal access token
# 3: Repository
# 4: path to file
if len(sys.argv) < 5:
    sys.stderr.write("Insufficient arguments")
    exit()
username = sys.argv[1]
token = sys.argv[2]
repo = sys.argv[3]
path = sys.argv[4]

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
print( base64.b64decode( fileRequest.json()['content'] ).decode('UTF-8', 'ignore') )