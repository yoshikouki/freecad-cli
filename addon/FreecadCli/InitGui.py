"""FreeCAD GUI initialization — auto-starts the RPC server."""

try:
    from FreecadCli import rpc_server
except ImportError:
    # FreeCAD adds the addon directory itself (not its parent Mod dir) to sys.path
    import rpc_server

rpc_server.start()
