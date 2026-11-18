"""Serves the repo and catches rendered frames from render-frames.html.

The intro is a canvas animation, not a video file. To also ship an mp4 we
render each frame deterministically in a real browser and POST the PNGs here,
then mux them with ffmpeg. See render-video.sh.

    python intro/tools/frame-server.py <repo-root> <out-dir> [port]
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

OUT_DIR = None


class Handler(SimpleHTTPRequestHandler):
    # HTTP/1.0 closes the socket after every response, and Chrome would
    # eventually try to reuse one mid-render and fail the fetch. Keep-alive
    # with an explicit Content-Length keeps the capture stable.
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        if not self.path.startswith("/frame/"):
            self.send_error(404)
            return
        try:
            index = int(self.path.rsplit("/", 1)[1])
        except ValueError:
            self.send_error(400, "bad frame index")
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        with open(os.path.join(OUT_DIR, "frame_%05d.png" % index), "wb") as f:
            f.write(payload)

        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, *args):
        pass  # the render loop prints its own progress


def main():
    global OUT_DIR
    root = sys.argv[1]
    OUT_DIR = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8791

    os.makedirs(OUT_DIR, exist_ok=True)
    handler = partial(Handler, directory=root)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print("serving %s on :%d, frames -> %s" % (root, port, OUT_DIR), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
