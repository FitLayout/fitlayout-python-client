import sys
import requests
from flclient import FitLayoutClient, default_prefix_string, R, SEGM

class FitLayoutCLI:

    def __init__(self, connection_url, repo_id):
        self.fl = FitLayoutClient(connection_url, repo_id)
    
    def ping(self):
        """ Performs a simple ping to the server."""
        print("Pinging FitLayout server...", end="")
        print(self.fl.ping())

    def list_artifacts(self, type=None):
        """ Lists all artifacts in the repository."""
        ret = []
        for artifact in self.fl.artifacts(type):
            ret.append(str(artifact))
        return ret

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
