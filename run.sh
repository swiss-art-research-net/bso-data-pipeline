source .env

JOBSCONTAINER=$(echo $PROJECT_NAME)_jobs

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Download IIIF Manifests? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task download-iiif-manifests --force"
fi

read -p "Execute everything else? (y/n)" -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
  NOPROMPT=1
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Convert to ZBZ data to XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task zbz-to-xml"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Perform mapping of ZBZ data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "taks mapping-zbz"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Perform mapping of NB data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task mapping-nb"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Retrieve GND data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task retrieve-gnd"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Retrieve Wikidata data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task retrieve-wikidata"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Ingest data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task ingest-main-data"
  docker exec $JOBSCONTAINER bash -c "task ingest-additional-data"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Add relations? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task add-relations"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Cleanup? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task cleanup"
fi
