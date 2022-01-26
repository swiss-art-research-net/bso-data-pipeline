import json
from flask import Flask, Response
app = Flask(__name__)

example = """
{
  "head" : {
    "vars" : [ "sub", "pred", "obj" ]
  },
  "results" : {
    "bindings" : [ {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/prov#generatedAtTime"
      },
      "obj" : {
        "datatype" : "http://www.w3.org/2001/XMLSchema#dateTime",
        "type" : "literal",
        "value" : "2020-04-06T10:49:19.238Z"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/prov#wasAttributedTo"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/user/admin"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/collection"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/creator_of_object"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/objects_created"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/object_depicts"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/label"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://rs.swissartresearch.net/instances/knowledgePatterns/object_carries_visual_item"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://platform.swissartresearch.net/instances/knowledgePatterns/collection"
      }
    }, {
      "sub" : {
        "type" : "uri",
        "value" : "http://www.researchspace.org/resource/system/knowledgePatternContainer"
      },
      "pred" : {
        "type" : "uri",
        "value" : "http://www.w3.org/ns/ldp#contains"
      },
      "obj" : {
        "type" : "uri",
        "value" : "http://platform.swissartresearch.net/instances/knowledgePatterns/creator_of_object"
      }
    } ]
  }
}
"""

@app.route('/')
def index():
  return 'Server Works!'
  
@app.route('/sparql', methods=['GET', 'POST'])
def sparql():
  return Response(example, mimetype='application/json')