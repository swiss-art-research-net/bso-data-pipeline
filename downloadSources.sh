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
download "data/zbz/curate/110_curate.json" "data/source/110.json"
download "data/zbz/curate/264_curate.txt" "data/source/264.json"
download "data/zbz/curate/600_curate.json" "data/source/600.json"
download "data/zbz/curate/610_curate.json" "data/source/610.json"
download "data/zbz/curate/611_curate.json" "data/source/611.json"
download "data/zbz/curate/650_curate.json" "data/source/650.json"
download "data/zbz/curate/651_curate.txt" "data/source/651.json"
download "data/zbz/curate/655_curate.json" "data/source/655.json"
download "data/zbz/curate/700_curate.json" "data/source/700.json"
download "data/zbz/curate/710_curate.json" "data/source/710.json"
download "data/zbz/source/sari_abzug-utf-8_23_04-tsv.txt" "data/source/sari_abzug-utf-8_23_04-tsv.json"
download "data/nb/source/WMC_Records_20201201.xml" "data/source/nb-allRecords.xml"