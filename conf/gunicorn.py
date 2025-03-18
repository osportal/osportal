import os
from app.config import *

if SERVER_NAME:
    server_name=os.environ.get('SERVER_NAME', default=SERVER_NAME)
    host, port=server_name.rsplit(":", 1) if ":" in server_name else (server_name, "8000")
    print(f"server_name: {server_name}")
else:
    port=os.environ.get('CONTAINER_PORT')
    if not port:
        port=8000

bind=f"0.0.0.0:{port}"
accesslog='-'
access_log_format='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" in %(D)sµs'
