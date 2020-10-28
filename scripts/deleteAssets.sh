#!/bin/bash
QUERY=$(cat deleteAssets.sparql)
curl -X POST http://blazegraph:8080/blazegraph/sparql --data-urlencode "update=$QUERY" 
