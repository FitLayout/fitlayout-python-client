FitLayout - Python Client
=========================

(c) 2025 Radek Burget (burgetr@fit.vut.cz)

The FitLayout client connects to the FitLayout REST API server and allows obtaining [artifact](https://github.com/FitLayout/FitLayout/wiki/Basic-Concepts#artifacts) data, performing SPARQL queries on the [artifact repository](https://github.com/FitLayout/FitLayout/wiki/Basic-Concepts#artifact-repository), modifying the repository content, or running remote FitLayout services. Its primary purpose is the implementation of algorithms for analyzing web pages in Python, where FitLayout serves as a source of data about rendered web pages, including details about the appearance and layout of individual content elements.

## Usage

FitLayout uses the RDF data model for representing the pages and other artifacts. It defines a set of [ontologies](https://fitlayout.github.io/ontology/) for describing the individual artifacts. The Python client is based on [RDFLib](https://rdflib.readthedocs.io/) that provides the RDF API for Python. The main `FitLayoutClient` class provides several functions for obtaining the artifact data.

A simple usage of the API:

```python
from flclient import FitLayoutClient, BOX

fl = FitLayoutClient("http://localhost:8400/api", "repositoryId")

# Get the IRIs of all rendered page in the repository
pageIris = fl.artifacts(BOX.Page)

# Get the first page IRI (as an example)
pageIri = next(pageIris)

# Get the RDF graph of the first page (a rdflib Graph object)
pageGraph = fl.get_artifact(pageIri)

# Print all properties of the page itself (excluding "pngImage" which is too large)
# This uses the RDFLib API for filtering the RDF triples.
for s, p, o in pageGraph.triples((pageIri, None, None)):
    prop = p.fragment # Omit the namespace from the property IRI
    if prop == "pngImage":
        continue
    print(f"{prop}: {o}")

# Get all content boxes from the page
for s, p, o in pageGraph.triples((None, BOX.belongsTo, pageIri)):
    boxIri = s
    # Get the box text (the box:text property)
    # See the ontology documentation for other box properties
    for bs, bp, bo in pageGraph.triples((boxIri, BOX.text, None)):
        print(f"Box: {boxIri}, text: {bo}")
```

The most efficient way to retrieve data for further analysis (e.g., machine learning) is to use SPARQL queries over the artifact repository. The following example uses one SPARQL query to retrieve all AreaTree artifacts and another SPARQL query to retrieve information about all distinguishable visual areas contained in a given area tree:

```python
from flclient import FitLayoutClient, default_prefix_string

fl = FitLayoutClient("http://localhost:8400/api", "repositoryId")

# Find all AreaTree IRIs in the repository.
# It returns a CSV with a single column 'areaTreeIri'.
listQuery = default_prefix_string() + """
    SELECT ?areaTreeIri
    WHERE {
        ?areaTreeIri rdf:type segm:AreaTree
    }
"""

# Execute the SPARQL query.
area_tree_rows = fl.sparql(listQuery)

# Get the first AreaTree IRI (as an example)
area_tree_iri = next(area_tree_rows)['areaTreeIri']
print("Area tree IRI:", area_tree_iri)

# A SPARQL query for finding area properties within the specified area tree
# For each area, retrieve its background color, text color, font size, position, dimensions, and text (if any)
# See the FitLayout ontology documentation for more details on the properties and relationships used.
areaQuery = default_prefix_string() + """
    SELECT (?c AS ?uri) ?backgroundColor ?color ?fontSize ?x ?y ?w ?h ?text
    WHERE {
        ?c rdf:type segm:Area .
        ?c segm:belongsTo <""" + str(area_tree_iri) + """> .
        ?c segm:containsBox ?box
        OPTIONAL { ?c box:backgroundColor ?backgroundColor } .
        OPTIONAL { ?box box:color ?color } .
        ?c box:fontSize ?fontSize .
        OPTIONAL { ?c segm:text ?text } .
        ?c box:bounds ?b . 

        ?b box:positionX ?x .
        ?b box:positionY ?y .
        ?b box:width ?w .
        ?b box:height ?h .
    }
"""

# Execute the SPARQL query
results = fl.sparql(areaQuery)

# Process the returned results.
for row in results:
    print(row)
```

## Server setup

The Python client requires a FitLayout server to be running and accessible. The easiest way to set up a server is to use the [fitlayout-local docker image](https://github.com/FitLayout/docker-images/tree/main/fitlayout-local), which provides both the server and a web GUI for adding and post-processing new web pages to the repository.
