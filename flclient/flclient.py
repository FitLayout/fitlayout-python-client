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
    
    def get_artifact(self, iri):
        """ Returns a graph of the entire artifact from the repository (artifact content included). """
        url = f"{self.repo_endpoint()}/artifact/item/" + requests.utils.quote(str(iri), safe="")
        headers = { "Accept": "text/turtle" }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.text
        g = Graph()
        g.parse(data=data, format="turtle")
        return g
    
    def delete_artifact(self, iri):
        """ Deletes the artifact from the repository. """
        url = f"{self.repo_endpoint()}/artifact/item/" + requests.utils.quote(str(iri), safe="")
        response = requests.delete(url)
        response.raise_for_status()
        return response.json()

    def clear_repository(self):
        """ Clears and re-initializes the repository. Deletes all artifacts. """
        url = f"{self.repo_endpoint()}/repository/clear"
        response = requests.delete(url)
        response.raise_for_status()
        url = f"{self.repo_endpoint()}/repository/forceInitRepo"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_artifact_info(self, iri):
        """ Returns a graph of the entire artifact from the repository (artifact content NOT included). """
        url = f"{self.repo_endpoint()}/artifact/info/" + requests.utils.quote(str(iri), safe="")
        headers = { "Accept": "text/turtle" }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = "utf-8"
        data = response.text
        g = Graph()
        g.parse(data=data, format="turtle")
        return g

    def get_artifact_image(self, iri):
        """ Returns a PNG image of the artifact. """
        url = f"{self.repo_endpoint()}/artifact/item/" + requests.utils.quote(str(iri), safe="")
        headers = { "Accept": "image/png" }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.content
    
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

    def invoke_artifact_service(self, service_id, parentUri, params = {}):
        """ Invokes a FitLayout service with the given parameters """
        url = f"{self.repo_endpoint()}/artifact/create"
        headers = { "Content-Type": "application/json" }
        body = { "serviceId": service_id, "params": params }
        if parentUri is not None:
            body["parentIri"] = str(parentUri)
        response = requests.post(url, json=body, headers=headers)
        #response.raise_for_status()
        return response.json()

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

FL = Namespace("http://fitlayout.github.io/ontology/fitlayout.owl#")
BOX = Namespace("http://fitlayout.github.io/ontology/render.owl#")
SEGM = Namespace("http://fitlayout.github.io/ontology/segmentation.owl#")
R = Namespace("http://fitlayout.github.io/resource/")
