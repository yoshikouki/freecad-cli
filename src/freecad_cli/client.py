import socket
import xmlrpc.client

from freecad_cli.output import error


class FreeCADClient:
    def __init__(self, host: str = "localhost", port: int = 9875, timeout: float = 5.0):
        self._url = f"http://{host}:{port}"
        self._timeout = timeout
        self._proxy = xmlrpc.client.ServerProxy(self._url)

    def call(self, method: str, *args):
        try:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self._timeout)
            try:
                return getattr(self._proxy, method)(*args)
            finally:
                socket.setdefaulttimeout(old_timeout)
        except ConnectionRefusedError:
            error("FreeCAD is not running or RPC server is not started", "connection_refused")
        except socket.timeout:
            error("RPC request timed out", "timeout")
        except xmlrpc.client.Fault as e:
            error(f"RPC fault: {e.faultString}", "rpc_fault")
        except OSError as e:
            error(f"Connection error: {e}", "connection_refused")

    def ping(self):
        return self.call("ping")

    def create_document(self, name: str):
        return self.call("create_document", name)

    def list_documents(self):
        return self.call("list_documents")

    def create_object(self, document: str, type_name: str, name: str, properties: dict | None = None):
        if properties:
            return self.call("create_object", document, type_name, name, properties)
        return self.call("create_object", document, type_name, name)

    def edit_object(self, document: str, name: str, properties: dict):
        return self.call("edit_object", document, name, properties)

    def delete_object(self, document: str, name: str):
        return self.call("delete_object", document, name)

    def get_objects(self, document: str):
        return self.call("get_objects", document)

    def get_object(self, document: str, name: str):
        return self.call("get_object", document, name)

    def execute_code(self, code: str):
        return self.call("execute_code", code)

    def get_active_screenshot(self, width: int = 800):
        return self.call("get_active_screenshot", width)

    def get_parts_list(self):
        return self.call("get_parts_list")

    def insert_part_from_library(self, path: str):
        return self.call("insert_part_from_library", path)
