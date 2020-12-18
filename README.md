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

To download the source data create a [GitHub personal access token](https://github.com/settings/tokens) and add it to the `.env` file, along with your username.

Download the source files by runnning
`sh downloadSources.sh`

Run the ETL pipeline through
`sh run.sh`

# Troubleshooting

If the BSO app is missing, you might have cloned the repository without submodules. To pull the submodules after cloning the repository, run
```
git submodule init
git submodule update
```