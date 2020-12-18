# About

This contains the pipeline for converting BSO input data into CIDOC/RDF

# How to use

Prerequisites: [Docker](http://docker.io) including Docker Compose

Copy and (if required) edit the .env.example
```
cp .env.example .env
```

Run the project with
```
docker-compose up -d
```

# Troubleshooting

If the BSO app is missing, you might have cloned the repository without submodules. To pull the submodules after cloning the repository, run
```
git submodule init
git submodule update
```