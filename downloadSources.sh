#!/bin/bash
source .env
REPO=swiss-art-research-net/BSO


download () {
  remotepath=$1
  localpath=$2

  echo "Downloading $remotepath"
  python3 scripts/getFileContentsFromGit.py $GITHUB_USERNAME $GITHUB_PERSONAL_ACCESS_TOKEN $REPO $remotepath > $localpath
}

download "data/zbz/curate/100_curate.json" "data/source/100.json"
download "data/zbz/curate/264_curate.txt" "data/source/264.json"
download "data/zbz/curate/651_curate.txt" "data/source/651.json"
#  TODO: support git lfs
# download "data/zbz/source/sari_abzug-utf-8_23_04-tsv.txt" "data/source/sari_abzug-utf-8_23_04-tsv.json"