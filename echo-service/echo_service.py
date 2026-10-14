import json, socket, time
from http.server import BaseHTTPRequestHandler, HTTPServer

class Penangan(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {
            "host": socket.gethostname(),
            "waktu_unix": time.time(),
            "waktu_lokal": time.strftime("%H:%M:%S"),
        }
        badan = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(badan)))
        self.end_headers()
        self.wfile.write(badan)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    # 0.0.0.0 = listen di semua network interface, bukan hanya localhost
    HTTPServer(("0.0.0.0", 8000), Penangan).serve_forever()
