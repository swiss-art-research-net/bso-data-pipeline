#!/bin/bash
source .env
REPO=swiss-art-research-net/bso-data


download () {
  remotepath=$1
  localpath=$2

  echo "Downloading $remotepath"
  python3 scripts/getFileContentsFromGit.py $GITHUB_USERNAME $GITHUB_PERSONAL_ACCESS_TOKEN $REPO $remotepath $localpath
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
download "data/zbz/curate/751_curate.txt" "data/source/751.json"
download "data/nb/nb-curation-personen.csv" "data/source/nb-curation-personen.csv"
download "data/nb/nb-curation-geografika.csv" "data/source/nb-curation-geografika.csv"
download "data/nb/nb-curation-koerperschaften.csv" "data/source/nb-curation-koerperschaften.csv"
download "data/nb/nb-curation-names.csv" "data/source/nb-curation-names.csv"
download "data/zbz/source/sari_abzug-utf-8_23_04-tsv.txt" "data/source/sari_abzug-utf-8_23_04-tsv.json"
download "data/nb/source/WMC_Records_20201201.xml" "data/source/nb-records.xml"
download "data/nb/source/Gugelman.xml" "data/source/nb-parentrecords.xml"

download "data/sari/prefLabels.trig" "data/ttl/additional/prefLabels.trig"
download "data/sari/zbzTypeLabels.trig" "data/ttl/additional/zbzTypeLabels.trig"