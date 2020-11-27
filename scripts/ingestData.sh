#!/bin/bash


RECORDSFOLDER=/data/ttl/main
ADDITIONALFOLDER=/data/ttl/additional

echo "Ingest records"
numfiles=$(ls -l $RECORDSFOLDER/*.ttl | wc -l)
count=1
for f in $(ls -1 $RECORDSFOLDER/*.ttl); do
  echo "Ingesting record $count of $numfiles ($f)"
  curl --silent -X POST http://blazegraph:8080/blazegraph/sparql --data-urlencode "update=DELETE { ?s ?p ?o } WHERE { GRAPH <file:/$f> { ?s ?p ?o } }" > /dev/null
  curl --silent -X POST --data-binary "uri=file://$f" http://blazegraph:8080/blazegraph/sparql > /dev/null
  count=$((count+1)) 
done

echo "Ingest additional data"
numfiles=$(ls -l $ADDITIONALFOLDER/*.ttl | wc -l)
count=1
for f in $(ls -1 $ADDITIONALFOLDER/*.ttl); do
  echo "Ingesting record $count of $numfiles ($f)"
  curl --silent -X POST http://blazegraph:8080/blazegraph/sparql --data-urlencode "update=DELETE { ?s ?p ?o } WHERE { GRAPH <file:/$f> { ?s ?p ?o } }" > /dev/null
  curl --silent -X POST --data-binary "uri=file://$f" http://blazegraph:8080/blazegraph/sparql > /dev/null
  count=$((count+1)) 
done
