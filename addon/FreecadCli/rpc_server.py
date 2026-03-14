"""Thin XML-RPC server that runs inside FreeCAD.

Exposes only `ping` and `execute_code` — all business logic lives in the CLI client.
Code execution is dispatched to FreeCAD's main (GUI) thread via Qt.
"""

import io
import queue
import sys
import threading
import traceback
from xmlrpc.server import SimpleXMLRPCServer

from PySide2 import QtCore

_server = None
_thread = None

HOST = "127.0.0.1"
PORT = 9875


class _MainThreadExecutor(QtCore.QObject):
    """Receives code execution requests and runs them on the main thread."""

    execute_requested = QtCore.Signal(str, object)

    def __init__(self):
        super().__init__()
        self.execute_requested.connect(self._run)

    def _run(self, code, result_queue):
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_capture
            exec(code, {"__builtins__": __builtins__})
            result_queue.put({
                "output": stdout_capture.getvalue(),
                "error": "",
            })
        except Exception:
            result_queue.put({
                "output": stdout_capture.getvalue(),
                "error": traceback.format_exc(),
            })
        finally:
            sys.stdout = old_stdout


_executor = None


def ping():
    return True


def execute_code(code):
    """Execute Python code on FreeCAD's main thread.

    Returns a dict with:
        - output: captured stdout
        - error: error message if execution failed (empty string on success)
    """
    result_queue = queue.Queue()
    _executor.execute_requested.emit(code, result_queue)
    return result_queue.get(timeout=30)


def start():
    global _server, _thread, _executor
    if _server is not None:
        print(f"[FreecadCli] RPC server already running on {HOST}:{PORT}")
        return

    _executor = _MainThreadExecutor()

    _server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=False)
    _server.register_function(ping, "ping")
    _server.register_function(execute_code, "execute_code")

    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print(f"[FreecadCli] RPC server started on {HOST}:{PORT}")


def stop():
    global _server, _thread, _executor
    if _server is not None:
        _server.shutdown()
        _server = None
        _thread = None
        _executor = None
        print("[FreecadCli] RPC server stopped")
