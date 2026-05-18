import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from models.log_models import JobLog
from database.database_manager import DatabaseManager
from models.job_model import JobRecord

class AuditHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/jobs/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                job = JobLog.from_dict(data)
                
                # Access the server's db_manager
                db_manager = self.server.db_manager
                logger = self.server.logger
                
                record = JobRecord(
                    job_id=job.jobId,
                    name=job.name or f"Job {job.jobId}",
                    x=job.x,
                    y=job.y,
                    duration=job.duration
                )
                db_manager.upsert_job(record)
                logger.info(f"Audit Log: User manually started {record.name} (ID: {job.jobId})")
                
                self._send_response(200, {"status": "success", "message": "Job logged successfully"})
            except Exception as e:
                self.server.logger.error(f"Failed to log job: {e}")
                self._send_response(500, {"status": "error", "message": str(e)})
        else:
            self._send_response(404, {"status": "error", "message": "Not Found"})

    def _send_response(self, status_code, payload):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress default logging to console to keep it clean
        pass

class ApiServer:
    def __init__(self, db_manager: DatabaseManager, logger):
        self.db_manager = db_manager
        self.logger = logger
        self.server = None
        self._thread = None

    def start(self, host: str = "127.0.0.1", port: int = 8000):
        def run_server():
            self.server = HTTPServer((host, port), AuditHandler)
            # Attach dependencies to the server instance so the handler can access them
            self.server.db_manager = self.db_manager
            self.server.logger = self.logger
            self.server.serve_forever()

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()
        self.logger.info(f"Audit API Server (Standard Lib) started at http://{host}:{port}")

    def stop(self):
        if self.server:
            self.server.shutdown()