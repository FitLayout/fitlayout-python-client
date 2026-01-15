import sys
import requests
from flclient import FitLayoutClient, default_prefix_string, R, SEGM

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
        self.fl = FitLayoutClient(connection_url, repo_id)
    
    def ping(self):
        """ Performs a simple ping to the server. """
        print("Pinging FitLayout server...", end="")
        print(self.fl.ping())

    def list_artifacts(self, type=None):
        """ Lists all artifacts in the repository. """
        ret = []
        for artifact in self.fl.artifacts(type):
            ret.append(str(artifact))
        return ret

    def get_artifact(self, iri):
        """ Retrieves an artifact by its IRI. """
        return self.fl.get_artifact(iri)

    def render(self, url, service_id = "FitLayout.Puppeteer", width=1200, height=800, params={}):
        """ Renders a webpage using the FitLayout service. """
        service_params = {
            "url": url,
            "width": width,
            "height": height,
        }
        service_params.update(params)
        response = self.fl.invoke_artifact_service(service_id, None, service_params)
        return response
    
    def query(self, query, auto_prefixes=True):
        """ Performs a query using the FitLayout server. """
        if auto_prefixes:
            query = default_prefix_string() + query
        response = self.fl.sparql(query)
        return list(response)
    
    def segment(self, iri, service_id = "FitLayout.BasicAreas", params={'preserveAuxAreas': True}):
        """ 
        Creates an AreaTree from an input Page artifact by applying a FitLayout segmentation service. 
        """
        response = self.fl.invoke_artifact_service(service_id, iri, params)
        return response

    def export(self, artifact_graph, format="turtle", output_file=None):
        """ 
        Exports an artifact graph to a specified format.
        See the RDFLib documentation for more information on supported RDF formats.
        @see https://rdflib.readthedocs.io/en/7.1.1/plugin_serializers.html
        """
        # Use RDFLib to serialize the artifact RDF graph in the specified format.
        if output_file:
            with open(output_file, "w") as f:
                f.write(artifact_graph.serialize(format=format))
        else:
            print(artifact_graph.serialize(format=format))

    def export_artifact(self, iri, format="turtle", output_file=None):
        """ Exports an artifact graph by its IRI to a specified format. """
        art = self.get_artifact(iri)
        self.export(art, format, output_file)

    def export_image(self, artifact_iri, output_file):
        """ 
        Exports an artifact's image as a PNG file.
        """
        imgdata = self.fl.get_artifact_image(artifact_iri)
        with open(output_file, "wb") as f:
            f.write(imgdata)
    
    def dump(self, format="turtle", output_file=None):
        """
        Dumps all artifacts in the repository to a specified format.
        @param format: The format to export the data in. Supported formats: turtle, n3, json-ld, xml, nquads. 
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
