from sariFieldDefinitionsGenerator import generator

inputFile = '../../../../researchplatform/apps/bso/src/fieldDefinitions.yml'
outputFile = '../ldp/assets/fieldDefinitions.trig'

model = generator.loadSourceFromFile(inputFile)

output = generator.generate(model, generator.RESEARCHSPACE)

with open(outputFile, 'w') as f:
    f.write(output)