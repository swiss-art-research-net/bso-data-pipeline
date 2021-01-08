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

read -p "Execute everything else? (y/n)" -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
  NOPROMPT=1
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Prepare ZBZ data in XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "RECORDS_LIMIT=$LIMIT task zbz-prepare-xml-records"
fi

if [[ $NOPROMPT -ne 1 ]]
then
  read -p "Pepare NB data to XML? (y/n)" -n 1 -r
  echo ""
fi
if [[ $NOPROMPT || $REPLY =~ ^[Yy]$ ]]
then
  docker exec $JOBSCONTAINER bash -c "RECORDS_LIMIT=$LIMIT task nb-prepare-xml-records"
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
  docker exec $JOBSCONTAINER bash -c "task ingest-data-main"
  docker exec $JOBSCONTAINER bash -c "task ingest-data-additional"
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
