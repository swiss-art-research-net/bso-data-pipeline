import sys
sys.path.append('/Users/fkraeutli/Sites/sari-field-definitions-generator/src')

from sariFieldDefinitionsGenerator import generator

inputFile = '../../../../researchplatform/apps/bso/src/fieldDefinitions.yml'
outputFile = '../ldp/assets/fieldDefinitions.trig'

model = generator.loadSourceFromFile(inputFile)
model['prefix'] = 'https://platform.swissartresearch.net/instances/knowledgePatterns/'

output = generator.generate(model, generator.RESEARCHSPACE)
output = output.replace("fieldDefinitionContainer","knowledgePatternContainer")

with open(outputFile, 'w') as f:
    f.write(output)