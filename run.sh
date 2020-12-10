source .env

JOBSCONTAINER=$(echo $PROJECT_NAME)_jobs
X3MLCONTAINER=$(echo $PROJECT_NAME)_x3ml

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Download IIIF Manifests? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "python /scripts/cache-iiif-manifests.py 0 99999"
fi

read -p "Execute everything else? (y/n)" -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
  NOPROMPT=1
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Convert to XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "python /scripts/json-to-xml.py"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Perform mapping? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $X3MLCONTAINER bash -c "bash /scripts/performMapping.sh"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Retrieve GND data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "python /scripts/extract-gnd-data.py"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Retrieve Wikidata data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "python /scripts/extract-wd-data.py"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Ingest data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "bash ingestData.sh"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Add relations? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "bash addRelations.sh"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Cleanup? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "bash postIngestCleanup.sh"
fi
