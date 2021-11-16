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
```sh
bash downloadSources.sh
```

Run the ETL pipeline through
```sh
bash run.sh
```

This will execute all relevant tasks to populate the platform with the data.

To only process a limited number of records (for testing purposes) add the `-l` parameter:
```sh
bash run.sh -l 20
```

This will process 20 records from each collection.

### Tasks

To interact with the task runner, connect to the jobs container (the name of the container depends on your setting of the project name):

`docker exec -it bso_pipeline_jobs bash`

To list available tasks, run:

`task --list`

This will output a list of tasks:
```
task: Available tasks for this project:
* add-relations:                        Materialise triples defined through the queries/addRelations.sparql query in the Blazegraph instance
* cleanup:                              Run Cleanup query (located in queries/cleanup.sparql)
* delete-field-definitions:             Delete the field definitions from the Blazegraph instance
* download-iiif-manifests:              Downloads the IIIF Manifests found in the ZBZ data source file
* ingest-data-additional:               Ingest the TTL and Trig files located in the data/ttl/additional folder to the Blazegraph instance
* ingest-data-main:                     Ingest the TTL files located in the data/ttl/main folder to the Blazegraph instance
* ingest-data-nb:                       Ingest the TTL files located in the data/ttl/main/nb folder to the Blazegraph instance
* ingest-data-nb-as-individual-graphs:  Ingest the TTL files located in the data/ttl/main/nb folder to the Blazegraph instance, placing each file into an individual named graph
* ingest-data-zbz:                      Ingest the TTL files located in the data/ttl/main/zbz folder to the Blazegraph instance
* ingest-data-zbz-as-individual-graphs: Ingest the TTL files located in the data/ttl/main/zbz folder to the Blazegraph instance, placing each file into an individual named graph
* ingest-ontologies:                    Ingests the ontologies into individual named Graphs
* mapping-nb:                           Map SNB XML data to CIDOC/RDF
* mapping-zbz:                          Map ZBZ XML data to CIDOC/RDF
* materialise-field-definitions:        Materialises the field definitions as propertes in the graph
* prepare-xml-records-nb:               Extract individual records from the NB data
* prepare-xml-records-zbz:              Convert the ZBZ data from JSON to individual XML Records
* retrieve-gnd:                         Extracts relevant data from GND based on identifiers found in the mapped TTL files
* retrieve-wikidata:                    Extracts relevant data from Wikidata based on identifiers found in the mapped TTL file                                         
```

To run a specific task type `task` followed by the task name, e.g.:

`task cleanup`

If the task is already up to date, it will not run. To force a task to run, type the command followed by `--force`

`task cleanup --force`

## Troubleshooting

### Missing BSO App

If the BSO app is missing, you might have cloned the repository without submodules. To pull the submodules after cloning the repository, run
```
git submodule init
git submodule update
```

### Problems saving forms

If forms do not save correctly, or regions cannot be drawn or deleted, it might be because a form container is missing. Create a new form container by executing the following SPARQL query:

```
INSERT {
    GRAPH <http://www.metaphacts.com/ontologies/platform#formContainer/context> {
        <http://www.metaphacts.com/ontologies/platform#rootContainer> <http://www.w3.org/ns/ldp#contains> <http://www.metaphacts.com/ontologies/platform#formContainer> .
        <http://www.metaphacts.com/ontologies/platform#formContainer> a <http://www.w3.org/ns/ldp#Container>,
                                                                     <http://www.w3.org/ns/ldp#Resource>,
                                                                     <http://www.w3.org/ns/prov#Entity> .
    }
} WHERE {}
```