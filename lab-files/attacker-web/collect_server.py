from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
import json


HOST = "192.168.141.1"
PORT = 8001
BASE_DIR = Path(__file__).resolve().parent
COLLECT_DIR = BASE_DIR / "collections"


class LabHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/collect":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        COLLECT_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = COLLECT_DIR / f"victim-profile-{timestamp}.json"

        try:
            data = json.loads(body.decode("utf-8"))
            output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            output.write_bytes(body)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')
        print(f"[COLLECT] Saved victim profile to {output}")


if __name__ == "__main__":
    print(f"Collecting lab results under {COLLECT_DIR}")
    print(f"Collector endpoint: http://{HOST}:{PORT}/collect")
    print("POST /collect will be saved under collections/")
    server = ThreadingHTTPServer((HOST, PORT), LabHandler)
    server.serve_forever()
