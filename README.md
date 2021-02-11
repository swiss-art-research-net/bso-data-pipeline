# Bilder der Schweiz Online

## About

This contains the pipeline for converting BSO input data into CIDOC/RDF

## How to use

Prerequisites: [Docker](http://docker.io) including Docker Compose

Copy and (if required) edit the .env.example
```
cp .env.example .env
```

Run the project with
```
docker-compose up -d
```

## Initialisation

To include the [BSO App](https://github.com/swiss-art-research-net/bso-app) when cloning, clone with:
```
git clone --recurse-submodules git@github.com:swiss-art-research-net/bso-data-pipeline.git
```

To download the source data create a [GitHub personal access token](https://github.com/settings/tokens) and add it to the `.env` file, along with your username.

Download the source files by runnning
`sh downloadSources.sh`

Run the ETL pipeline through
`sh run.sh`

This will execute all tasks defined in the taskfile
### Tasks

To interact with the task runner, connect to the jobs container (the name of the container depends on your setting of the project name):

`docker exec -it bso_pipeline_jobs bash`

To list available tasks, run:

`task --list`

This will output a list of tasks:
```
task: Available tasks for this project:
* add-relations:                Materialise triples defined through the queries/addRelations.sparql query in the Blazegraph instance
* cleanup:                      Run Cleanup query (located in queries/cleanup.sparql)
* delete-assets:                Delete the assets (field definitions, etc.) from the Blazegraph instance
* download-iiif-manifests:      Downloads the IIIF Manifests found in the ZBZ data source file
* ingest-data-additional:       Ingest the TTL files located in the data/ttl/additional folder to the Blazegraph instance
* ingest-data-main:             Ingest the TTL files located in the data/ttl/main folder to the Blazegraph instance
* ingest-data-nb:               Ingest the TTL files located in the data/ttl/main/nb folder to the Blazegraph instance
* ingest-data-zbz:              Ingest the TTL files located in the data/ttl/main/zbz folder to the Blazegraph instance
* mapping-nb:                   Map SNB XML data to CIDOC/RDF
* mapping-zbz:                  Map ZBZ XML data to CIDOC/RDF
* materialise-field-definitions:Materialises the field definitions as propertes in the graph
* prepare-xml-records-nb:       Extract individual records from the NB data
* prepare-xml-records-zbz:      Convert the ZBZ data from JSON to individual XML Records
* retrieve-gnd:                 Extracts relevant data from GND based on identifiers found in the mapped TTL files
* retrieve-wikidata:            Extracts relevant data from Wikidata based on identifiers found in the mapped TTL files
```

To run a specific task type `task` followed by the task name, e.g.:

`task cleanup`

If the task is already up to date, it will not run. To force a task to run, type the command followed by `--force`

`task cleanup --force`
## Troubleshooting

If the BSO app is missing, you might have cloned the repository without submodules. To pull the submodules after cloning the repository, run
```
git submodule init
git submodule update
```
