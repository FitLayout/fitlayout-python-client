import requests

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF


class FitLayoutClient:
    """ REST client for FitLayout """

    def __init__(self, api_root, repository_id):
        self.api_root = api_root
        self.repository_id = repository_id
    
    def repo_endpoint(self):
        return f"{self.api_root}/r/{self.repository_id}"
    
    def ping(self):
        """ Performs a simple ping to the server """
        url = f"{self.api_root}/service/ping"
        response = requests.get(url, timeout=1)
        response.raise_for_status()
        return response.text # should return "ok"

    def sparql(self, query):
        """ Executes a SPARQL query on the repository """
        url = f"{self.repo_endpoint()}/repository/query?limit=500000"
        headers = { "Content-Type": "application/sparql-query" }
        response = requests.post(url, data=query, headers=headers)
        response.raise_for_status()
        data = response.json()
        if "results" in data and "bindings" in data["results"]:
            for binding in data["results"]["bindings"]:
                row = {}
                for key, value in binding.items():
                    row[key] = decode_json_value(value)
                yield row
        else:
            return []
        
    def artifacts(self, type = None):
        """ Returns a list of all artifacts in the repository """
        query = default_prefix_string()
        if (type is None):
            query += "SELECT ?pg WHERE { ?pg rdf:type ?type . ?type rdfs:subClassOf fl:Artifact }"
        else:
            query += " SELECT ?pg WHERE { ?pg rdf:type <" + str(type) + "> }\n"
        for row in self.sparql(query):
            yield row["pg"]
    
    def get_artifact(self, uri):
        """ Returns a single artifact from the repository """
        url = f"{self.repo_endpoint()}/artifact/item/" + requests.utils.quote(str(uri), safe="")
        headers = { "Accept": "text/turtle" }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.text
        g = Graph()
        g.parse(data=data, format="turtle")
        return g
    
    def add_quad_object(self, subject, predicate, object, artifact):
        """ Adds a quad with an object to the repository """
        url = f"{self.repo_endpoint()}/repository/add"
        headers = { "Content-Type": "application/json" }
        data = {
            "s": str(subject),
            "p": str(predicate),
            "o": str(object),
            "artifact": str(artifact)
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def add_quad_literal(self, subject, predicate, literal, artifact):
        """ Adds a quad with a literal to the repository """
        url = f"{self.repo_endpoint()}/repository/add"
        headers = { "Content-Type": "application/json" }
        data = {
            "s": str(subject),
            "p": str(predicate),
            "value": literal,
            "artifact": str(artifact)
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def delete_quad(self, subject=None, predicate=None, object=None, artifact=None):
        """ Delete a quad with a literal to the repository. The value of None is used as a wildcard. """
        url = f"{self.repo_endpoint()}/repository/statements"
        headers = { "Content-Type": "application/json" }
        data = {}
        if subject is not None:
            data["subj"] = "<" + str(subject) + ">"
        if predicate is not None:
            data["pred"] = "<" + str(predicate) + ">"
        if object is not None:
            data["obj"] = "<" + str(object) + ">"
        if artifact is not None:
            data["context"] = "<" + str(artifact) + ">"

        # Pass the data as query parameters
        response = requests.delete(url, params=data, headers=headers)
        #response.raise_for_status()
        return response.json()

    def add_tag(self, subject, tagType, tagName, support, artifact):
        """ Adds a tag to a subject """
        tagId = 'tag-' + tagType + '--' + tagName
        tagUri = R[tagId]
        tagSupportUri = URIRef(str(subject) + '-t-' + tagType + '--' + tagName)
        self.add_quad_object(subject, SEGM.hasTag, tagUri, artifact)
        self.add_quad_object(subject, SEGM.tagSupport, tagSupportUri, artifact)
        self.add_quad_object(tagSupportUri, SEGM.hasTag, tagUri, artifact)
        self.add_quad_literal(tagSupportUri, SEGM.support, support, artifact)

def decode_json_value(value):
    """ Decodes a value from the FitLayout API into a Python object """
    if value["type"] == "uri":
        return URIRef(value["value"])
    elif value["type"] == "literal":
        return Literal(value["value"], datatype=value["datatype"])
    else:
        return value["value"]

def default_prefixes():
    return {
        "fl": "http://fitlayout.github.io/ontology/fitlayout.owl#",
        "r": "http://fitlayout.github.io/resource/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "box": "http://fitlayout.github.io/ontology/render.owl#",
        "segm": "http://fitlayout.github.io/ontology/segmentation.owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }

def default_prefix_string():
    prefixes = default_prefixes()
    return "\n".join(f"PREFIX {prefix}: <{value}>" for prefix, value in prefixes.items())

BOX = Namespace("http://fitlayout.github.io/ontology/render.owl#")
SEGM = Namespace("http://fitlayout.github.io/ontology/segmentation.owl#")
R = Namespace("http://fitlayout.github.io/resource/")
