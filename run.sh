source .env

JOBSCONTAINER=$(echo $PROJECT_NAME)_jobs
X3MLCONTAINER=$(echo $PROJECT_NAME)_x3ml

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
  read -p "Ingest data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "bash ingestData.sh"
fi
