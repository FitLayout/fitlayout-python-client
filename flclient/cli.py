import sys
import requests
from rdflib import URIRef
from flclient import FitLayoutClient, default_prefix_string, R, SEGM, BOX

# If flclient is a dependency in your project, the interactive CLI can be invoked by:
# python -i -m flclient.cli <server_url> <repository_id>

class FitLayoutCLI:
    """
    A command-line interface for interacting with a FitLayout server.
    """

    mime_types = {
        "turtle": "text/turtle",
        "n3": "application/n-triples",
        "json-ld": "application/ld+json",
        "xml": "application/edf+xml",
        "nquads": "application/n-quads"
    }

    def __init__(self, connection_url, repo_id):
        """
        Initializes the CLI with a connection to a FitLayout server.
        @param connection_url: The URL of the FitLayout API server.
        @param repo_id: The ID of the repository to use.
        """
        self.fl = FitLayoutClient(connection_url, repo_id)
    
    def ping(self):
        """ Performs a simple ping to the server. """
        print("Pinging FitLayout server...", end="")
        print(self.fl.ping())

    def get_artifacts(self, type=None):
        """
        Gets a list of artifact IRIs in available the repository.
        @param type: The type of artifacts to list (e.g., BOX.Page or SEGM.AreaTree). If None, lists all artifacts.
        """
        ret = []
        for artifact in self.fl.artifacts(type):
            ret.append(str(artifact))
        return ret

    def list_artifacts(self, type=None):
        """
        Prints a list of artifact IRIs in the repository and their types.
        @param type: The type of artifacts to list (e.g., BOX.Page or SEGM.AreaTree). If None, lists all artifacts.
        """
        query = default_prefix_string()
        if (type is None):
            query += " SELECT ?pg ?type WHERE { ?pg rdf:type ?type . ?type rdfs:subClassOf fl:Artifact }"
        else:
            query += " SELECT ?pg ?type WHERE { ?pg rdf:type <" + str(type) + "> BIND (<" + str(type) + "> as ?type)}\n"
        for row in self.fl.sparql(query):
            print(f"{str(row['pg'])}\t {str(row['type'])}")

    def clear_repository(self):
        """
        Clears and re-initializes the repository. Deletes all artifacts.
        """
        clearConfirmed = input("Are you sure you want to clear the repository? (yes/no): ").lower() == "yes"
        if clearConfirmed:
            r = self.fl.clear_repository()
            print("Repository cleared.")
            return r
        else:
            print("Repository not cleared.")

    def get_artifact(self, iri):
        """
        Retrieves an artifact by its IRI.
        @param iri: The IRI of the artifact to retrieve.
        @return: The artifact RDF graph.
        """
        return self.fl.get_artifact(iri)
    
    def delete_artifact(self, iri):
        """
        Deletes an artifact by its IRI.
        @param iri: The IRI of the artifact to delete.
        """
        return self.fl.delete_artifact(iri)

    def info(self, iri):
        """
        Print information about an artifact by its IRI.
        @param iri: The IRI of the artifact to retrieve information about.
        """
        iriRef = URIRef(iri)
        g = self.fl.get_artifact_info(iri)
        for s, p, o in g.triples((iriRef, None, None)):
            prop = p.fragment
            if prop == "pngImage":
                continue
            print(f"{prop}: {o}")        

    def render(self, url, service_id = "FitLayout.Puppeteer", width=1200, height=800, params={}):
        """
        Renders a webpage using the FitLayout service.
        @param url: The URL of the webpage to render.
        @param service_id: The ID of the rendering service to use (default: FitLayout.Puppeteer).
        @param width: The viewport width for rendering (default: 1200).
        @param height: The viewport height for rendering (default: 800).
        @param params: A dictionary of additional parameters for the service.
        """
        service_params = {
            "url": url,
            "width": width,
            "height": height,
        }
        service_params.update(params)
        response = self.fl.invoke_artifact_service(service_id, None, service_params)
        return response
    
    def query(self, query, auto_prefixes=True):
        """
        Executes a SPARQL query on the FitLayout server.
        @param query: The SPARQL query to execute.
        @param auto_prefixes: If True, prepends a default set of RDF prefixes to the query.
        """
        if auto_prefixes:
            query = default_prefix_string() + query
        response = self.fl.sparql(query)
        return list(response)
    
    def segment(self, iri, service_id = "FitLayout.BasicAreas", params={'preserveAuxAreas': True}):
        """ 
        Creates an AreaTree from an input Page artifact by applying a FitLayout segmentation service. 
        @param iri: The IRI of the Page artifact to segment.
        @param service_id: The ID of the segmentation service to use.
        @param params: A dictionary of parameters for the segmentation service.
        """
        response = self.fl.invoke_artifact_service(service_id, iri, params)
        return response

    def export(self, artifact_graph, format="turtle", output_file=None):
        """ 
        Exports an artifact graph to a specified format.
        See the RDFLib documentation for more information on supported RDF formats.
        @param artifact_graph: The RDF graph of the artifact to export.
        @param format: The serialization format (e.g., 'turtle', 'xml').
        @param output_file: The path to the output file. If None, prints to standard output.
        @see https://rdflib.readthedocs.io/en/7.1.1/plugin_serializers.html
        """
        # Use RDFLib to serialize the artifact RDF graph in the specified format.
        if output_file:
            with open(output_file, "w") as f:
                f.write(artifact_graph.serialize(format=format))
        else:
            print(artifact_graph.serialize(format=format))

    def export_artifact(self, iri, format="turtle", output_file=None):
        """
        Exports an artifact graph by its IRI to a specified format.
        @param iri: The IRI of the artifact to export.
        @param format: The serialization format.
        @param output_file: The path to the output file. If None, prints to standard output.
        """
        art = self.get_artifact(iri)
        self.export(art, format, output_file)

    def export_image(self, artifact_iri, output_file):
        """ 
        Exports an artifact's image as a PNG file.
        @param artifact_iri: The IRI of the artifact whose image is to be exported.
        @param output_file: The path to save the output PNG file.
        """
        imgdata = self.fl.get_artifact_image(artifact_iri)
        with open(output_file, "wb") as f:
            f.write(imgdata)
    
    def dump(self, format="turtle", output_file=None):
        """
        Dumps all artifacts in the repository to a specified format.
        @param format: The format to export the data in. Supported formats: turtle, n3, json-ld, xml, nquads.
        @param output_file: The path to the output file. If None, prints to standard output.
        """
        endpoint = self.fl.repo_endpoint() + "/repository/statements"
        # Set the Accept header based on the specified format.
        accept = self.mime_types.get(format)
        if not accept:
            print(f"Unsupported format: {format}. Supported formats: {', '.join(self.mime_types.keys())}")
            return
        headers = { "Accept": accept }
        # Perform a GET request to retrieve the repository statements.
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        if output_file:
            with open(output_file, "w") as f:
                f.write(response.text)
        else:
            print(response.text)

    def import_file(self, input_file, format, split=None):
        """
        Imports serialized RDF from a file.
        The split parameter is applicable to nquads and n3 formats only and is used for splitting the source file by the given number of lines and uploading by 
        separate requests to bypass the POST data max size limit.
        @param input_file: The path to the input file.
        @param format: The format of the input data. Supported formats: turtle, n3, json-ld, xml, nquads.
        @param split: The number of lines per chunk for chunked upload.
        """
        endpoint = self.fl.repo_endpoint() + "/repository/statements"
        content_type = self.mime_types.get(format)
        if not content_type:
            print(f"Unsupported format: {format}. Supported formats: {', '.join(self.mime_types.keys())}")
            return
        
        headers = { "Content-Type": content_type }

        if split and format in ["nquads", "n3"]:
            print(f"Importing {input_file} in chunks of {split} lines...")
            try:
                with open(input_file, "r") as f:
                    chunk = []
                    for i, line in enumerate(f):
                        chunk.append(line)
                        if (i + 1) % split == 0:
                            data = "".join(chunk)
                            response = requests.post(endpoint, headers=headers, data=data.encode('utf-8'))
                            response.raise_for_status()
                            chunk = []
                            print(f"Uploaded {i + 1} lines.")
                    if chunk:
                        data = "".join(chunk)
                        response = requests.post(endpoint, headers=headers, data=data.encode('utf-8'))
                        response.raise_for_status()
                        print(f"Uploaded remaining {len(chunk)} lines.")
                print("Import finished successfully.")
            except FileNotFoundError:
                print(f"Error: Input file not found at {input_file}")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred during import: {e}")
        else:
            if split:
                print(f"Warning: 'split' parameter is ignored for '{format}' format.")
            print(f"Importing {input_file}...")
            try:
                with open(input_file, "rb") as f:
                    data = f.read()
                response = requests.post(endpoint, headers=headers, data=data)
                response.raise_for_status()
                print("Import finished successfully.")
            except FileNotFoundError:
                print(f"Error: Input file not found at {input_file}")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred during import: {e}")
    
    def list_tags(self):
        query = default_prefix_string() + """
            SELECT ?a ?text ?tag ?support ?ts
            WHERE {
                ?a segm:text ?text .
                ?a segm:tagSupport ?ts .
                ?ts segm:hasTag ?tag .
                ?ts segm:support ?support
            }
        """
        # Print the result
        for row in self.fl.sparql(query):
            print(f"\"{row['text']}\" : {row['tag']} ({row['support']})")


def p(data):
    """ Pretty-prints a list of data. """
    print("\n".join(data))

def main():
    # Require connection URL and optional repository ID as command-line arguments.
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python client_example.py <connection_url> [<repository_id>]")
        sys.exit(1)

    connection_url = sys.argv[1]
    repo_id = sys.argv[2] if len(sys.argv) == 3 else "default"

    return FitLayoutCLI(connection_url, repo_id)

if __name__ == "__main__":
    requests.packages.urllib3.util.connection.HAS_IPV6 = False
    cli = main()
    cli.ping()
    print("Use `cli` to interact with FitLayout.")
