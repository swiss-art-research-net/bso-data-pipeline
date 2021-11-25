#!/bin/bash
source .env
REPO=swiss-art-research-net/bso-data

download () {
  remotepath=$1
  localpath=$2

  echo "Downloading $remotepath"
  python3 scripts/getFileContentsFromGit.py $GITHUB_USERNAME $GITHUB_PERSONAL_ACCESS_TOKEN $REPO $remotepath $localpath
}

download "data/zbz/zbz-curation-100-a_d.csv" "data/source/zbz-curation-100-a_d.csv"
download "data/zbz/zbz-curation-110-a.csv" "data/source/zbz-curation-110-a.csv"
download "data/zbz/zbz-curation-264-a.csv" "data/source/zbz-curation-264-a.csv"
download "data/zbz/zbz-curation-264-b.csv" "data/source/zbz-curation-264-b.csv"
download "data/zbz/zbz-curation-600-a_b.csv" "data/source/zbz-curation-600-a_b.csv"
download "data/zbz/zbz-curation-610-a_g.csv" "data/source/zbz-curation-610-a_g.csv"
download "data/zbz/zbz-curation-611-a_c_d.csv" "data/source/zbz-curation-611-a_c_d.csv"
download "data/zbz/zbz-curation-650-a_g.csv" "data/source/zbz-curation-650-a_g.csv"
download "data/zbz/zbz-curation-651-a_g.csv" "data/source/zbz-curation-651-a_g.csv"
download "data/zbz/zbz-curation-655-a.csv" "data/source/zbz-curation-655-a.csv"
download "data/zbz/zbz-curation-700-a_d.csv" "data/source/zbz-curation-700-a_d.csv"
download "data/zbz/zbz-curation-710-a.csv" "data/source/zbz-curation-710-a.csv"
download "data/zbz/zbz-curation-751-a_g.csv" "data/source/zbz-curation-751-a_g.csv"
download "data/zbz/zbz-corrections.csv" "data/source/zbz-corrections.csv"
download "data/zbz/source/dois.csv" "data/source/zbz-dois.csv"
download "data/zbz/source/BIBLIOGRAPHIC_8971984070005508_1.xml" "data/source/BIBLIOGRAPHIC_8971984070005508_1.xml"
download "data/zbz/source/BIBLIOGRAPHIC_8971984070005508_2.xml" "data/source/BIBLIOGRAPHIC_8971984070005508_2.xml"
download "data/zbz/source/BIBLIOGRAPHIC_8971984070005508_3.xml" "data/source/BIBLIOGRAPHIC_8971984070005508_3.xml"
download "data/zbz/source/BIBLIOGRAPHIC_8971984070005508_4.xml" "data/source/BIBLIOGRAPHIC_8971984070005508_4.xml"
download "data/zbz/source/BIBLIOGRAPHIC_8972912360005508_1.xml" "data/source/BIBLIOGRAPHIC_8972912360005508_1.xml"

download "data/nb/nb-curation-personen.csv" "data/source/nb-curation-personen.csv"
download "data/nb/nb-curation-geografika.csv" "data/source/nb-curation-geografika.csv"
download "data/nb/nb-curation-koerperschaften.csv" "data/source/nb-curation-koerperschaften.csv"
download "data/nb/nb-curation-names.csv" "data/source/nb-curation-names.csv"
download "data/nb/nb-curation-extracted-types.csv" "data/source/nb-curation-extracted-types.csv"
download "data/nb/nb-external-descriptors.csv" "data/source/nb-external-descriptors.csv"
download "data/nb/nb-image-sizes.csv" "data/source/nb-image-sizes.csv"
download "data/nb/source/WMC_Records_20201201.xml" "data/source/nb-records.xml"
download "data/nb/source/Gugelman.xml" "data/source/nb-parentrecords.xml"

download "data/sff/Werke.csv" "data/source/sff-werke.csv"
download "data/sff/sff-werk-masse.csv" "data/source/sff-werk-masse.csv"
download "data/sff/source/Literatur.csv" "data/source/sff-literatur.csv"
download "data/sff/source/Literatur_index_Verknupfung.csv" "data/source/sff-literatur-links.csv"
download "data/sff/sff-images.csv" "data/source/sff-images.csv"
download "data/sff/sff-curation-keywords.csv" "data/source/sff-curation-keywords.csv"
download "data/sff/sff-curation-ortsbezug.csv" "data/source/sff-curation-ortsbezug.csv"
download "data/sff/sff-artists.csv" "data/source/sff-artists.csv"

download "data/sari/prefLabels.trig" "data/ttl/additional/prefLabels.trig"
download "data/sari/zbzTypeLabels.trig" "data/ttl/additional/zbzTypeLabels.trig"
download "data/sari/datasetMetadata.trig" "data/ttl/additional/datasetMetadata.trig"
download "data/sari/smapshot-classifications.trig" "data/ttl/additional/smapshot-classifications.trig"

download "data/sari/imageRegions.trig" "data/graphs/imageRegions.trig"
