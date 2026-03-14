"""Thin XML-RPC server that runs inside FreeCAD.

Exposes only `ping` and `execute_code` — all business logic lives in the CLI client.
"""

import io
import sys
import threading
import traceback
from xmlrpc.server import SimpleXMLRPCServer

_server = None
_thread = None

HOST = "127.0.0.1"
PORT = 9875


def ping():
    return True


def execute_code(code):
    """Execute Python code in FreeCAD's interpreter.

    Returns a dict with:
        - output: captured stdout
        - error: error message if execution failed (empty string on success)
    """
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = stdout_capture
        exec(code, {"__builtins__": __builtins__})
        return {
            "output": stdout_capture.getvalue(),
            "error": "",
        }
    except Exception:
        return {
            "output": stdout_capture.getvalue(),
            "error": traceback.format_exc(),
        }
    finally:
        sys.stdout = old_stdout


def start():
    global _server, _thread
    if _server is not None:
        print(f"[FreecadCli] RPC server already running on {HOST}:{PORT}")
        return

    _server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=False)
    _server.register_function(ping, "ping")
    _server.register_function(execute_code, "execute_code")

    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print(f"[FreecadCli] RPC server started on {HOST}:{PORT}")


def stop():
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server = None
        _thread = None
        print("[FreecadCli] RPC server stopped")
