import sys
import requests
from flclient import FitLayoutClient, default_prefix_string, R, SEGM

class FitLayoutCLI:
    """
    A command-line interface for interacting with a FitLayout server.
    """

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

    def export(self, art, format="turtle", output_file=None):
        """ 
        Exports an artifact graph to a specified format.
        See the RDFLib documentation for more information on supported RDF formats.
        @see https://rdflib.readthedocs.io/en/7.1.1/plugin_serializers.html
        """
        # Use RDFLib to serialize the artifact in the specified format.
        if output_file:
            with open(output_file, "w") as f:
                f.write(art.serialize(format=format))
        else:
            print(art.serialize(format=format))

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
