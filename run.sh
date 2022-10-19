source .env

JOBSCONTAINER=$(echo $PROJECT_NAME)_jobs
LIMIT=999999

usage() { echo "Usage: $0 [-l <limit>] [-y <yes to everything>]" 1>&2; exit 1; }

while getopts ":y:l:" o; do
    case "${o}" in
        y)
            NOPROMPT=1
            ;;
        l)
            LIMIT=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

echo $LIMIT

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Download IIIF Manifests? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task download-iiif-manifests --force"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Prepare ZBZ data in XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "RECORDS_LIMIT=$LIMIT task prepare-xml-records-zbz"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Pepare NB data to XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "RECORDS_LIMIT=$LIMIT task prepare-xml-records-nb"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Pepare SFF data to XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "RECORDS_LIMIT=$LIMIT task prepare-xml-records-sff"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Perform mapping of ZBZ data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task mapping-zbz"
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
  read -p "Perform mapping of SFF data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task mapping-sff"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Retrieve additional data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task retrieve-additional-data"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Ingest data? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task ingest-data-main"
  docker exec $JOBSCONTAINER bash -c "task ingest-data-additional"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Ingest similarities? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task ingest-similarities"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Ingest ontologies? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task ingest-ontologies"
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
  read -p "Add summaries? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task add-summaries"
fi

# if [[ $NOPROMPT -ne 1 ]]
# then
#   read -p "Materialise fields? (y/n)" -n 1 -r
#   echo ""
# fi
# if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
# then
#   docker exec $JOBSCONTAINER bash -c "task materialise-field-definitions"
# fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Cleanup? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "task cleanup"
fi
