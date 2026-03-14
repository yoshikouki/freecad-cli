import json
import socket
import xmlrpc.client

from freecad_cli.output import error


class FreeCADClient:
    def __init__(self, host: str = "localhost", port: int = 9875, timeout: float = 5.0):
        self._url = f"http://{host}:{port}"
        self._timeout = timeout
        self._proxy = xmlrpc.client.ServerProxy(self._url)

    def _rpc_call(self, method: str, *args):
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

    def _execute(self, code: str):
        """Send Python code to FreeCAD for execution."""
        result = self._rpc_call("execute_code", code)
        if result and result.get("error"):
            error(result["error"], "rpc_fault")
        return result

    def ping(self):
        return self._rpc_call("ping")

    def get_active_document(self):
        result = self._execute("""
import FreeCAD, FreeCADGui, json
doc = FreeCAD.ActiveDocument
gui_doc = FreeCADGui.ActiveDocument
info = {
    "name": doc.Name if doc else None,
    "label": doc.Label if doc else None,
    "gui_active": gui_doc.Document.Name if gui_doc else None,
}
print(json.dumps(info))
""")
        return json.loads(result["output"])

    def set_active_document(self, name: str):
        result = self._execute(f"""
import FreeCAD, FreeCADGui
FreeCAD.setActiveDocument({name!r})
FreeCADGui.setActiveDocument({name!r})
FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
FreeCADGui.ActiveDocument.ActiveView.fitAll()
print(FreeCAD.ActiveDocument.Name)
""")
        return result["output"].strip()

    def create_document(self, name: str):
        result = self._execute(f"""
import FreeCAD
doc = FreeCAD.newDocument({name!r})
print(doc.Name)
""")
        return result["output"].strip()

    def list_documents(self):
        result = self._execute("""
import FreeCAD
print(__import__('json').dumps(list(FreeCAD.listDocuments().keys())))
""")
        return json.loads(result["output"])

    def execute_code(self, code: str):
        return self._execute(code)

    def get_active_screenshot(self, width: int = 800):
        result = self._execute(f"""
import FreeCADGui, tempfile, base64, os
view = FreeCADGui.ActiveDocument.ActiveView
tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
tmp.close()
view.saveImage(tmp.name, {width!r}, {width!r}, 'Current')
with open(tmp.name, 'rb') as f:
    data = base64.b64encode(f.read()).decode()
os.unlink(tmp.name)
print(data)
""")
        return result["output"].strip()

    def get_parts_list(self):
        result = self._execute("""
import json, os
parts_dir = os.path.join(os.path.dirname(__import__('FreeCAD').__file__), 'Mod', 'Parts_Library')
parts = []
if os.path.isdir(parts_dir):
    for root, dirs, files in os.walk(parts_dir):
        for f in files:
            if f.endswith(('.FCStd', '.step', '.stp', '.iges', '.igs')):
                parts.append(os.path.relpath(os.path.join(root, f), parts_dir))
print(json.dumps(parts))
""")
        return json.loads(result["output"])

    def export_object(self, format: str, output_path: str, object_name: str | None = None):
        """Export an object or document to the specified format."""
        if format == "stl":
            export_code = f"""
import Mesh, FreeCAD, os
doc = FreeCAD.ActiveDocument
obj_name = {object_name!r}
if obj_name:
    obj = doc.getObject(obj_name)
else:
    obj = doc.getObject('Body') or doc.Objects[0]
output = {output_path!r}
os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
Mesh.export([obj], output)
print(output)
"""
        elif format == "step":
            export_code = f"""
import Part, FreeCAD, os
doc = FreeCAD.ActiveDocument
obj_name = {object_name!r}
if obj_name:
    obj = doc.getObject(obj_name)
else:
    obj = doc.getObject('Body') or doc.Objects[0]
output = {output_path!r}
os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
Part.export([obj], output)
print(output)
"""
        elif format == "fcstd":
            export_code = f"""
import FreeCAD, os
doc = FreeCAD.ActiveDocument
output = {output_path!r}
os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
doc.saveAs(output)
print(output)
"""
        else:
            from freecad_cli.output import error
            error(f"Unsupported format: {format}. Use stl, step, or fcstd", "invalid_input")

        result = self._execute(export_code)
        return result["output"].strip()

    def insert_part_from_library(self, path: str):
        result = self._execute(f"""
import Part, FreeCAD
doc = FreeCAD.ActiveDocument
if doc is None:
    doc = FreeCAD.newDocument('Unnamed')
Part.insert({path!r}, doc.Name)
doc.recompute()
print(doc.Name)
""")
        return result["output"].strip()
