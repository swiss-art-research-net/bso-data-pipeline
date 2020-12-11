RECORDSINPUTFOLDER=/data/xml/zbz
RECORDSOUTPUTFOLDER=/data/ttl/main

RECORDMAPPING=/mapping/mappings-zbz.x3ml
GENERATOR=/mapping/generator-policy.xml

BATCHSIZE=20

echo "Mapping Records"
numfiles=$(ls -l $RECORDSINPUTFOLDER/*.xml | wc -l)
count=1
echo "Found $numfiles record XML files"

(
for f in $(ls -1 $RECORDSINPUTFOLDER/*.xml); do
  ((i=i%BATCHSIZE)); ((i++==0)) && wait
  echo "Mapping record $count of $numfiles ($f)"
  o=${f/.xml/.ttl}
  o=${o/$RECORDSINPUTFOLDER/}
  java -jar /x3ml/x3ml-engine.exejar \
    --input $f \
    --x3ml $RECORDMAPPING \
    --policy $GENERATOR \
    --output $RECORDSOUTPUTFOLDER/$o \
    --format text/turtle &
  count=$((count+1)) 
done
)