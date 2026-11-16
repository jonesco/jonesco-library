# Serves the library on 127.0.0.1 only: the viewer, Show in Finder, and the drop box (add / remove).
import http.server, socketserver, subprocess, os, sys, json, urllib.parse, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline
ROOT = pipeline.ROOT
ALLOWED = [os.path.realpath(ROOT), os.path.realpath("/Users/Wes/Developer/_Fonts and Graphics")]
PORT = 8765; HOSTS = {"127.0.0.1:%d" % PORT, "localhost:%d" % PORT}
MAX = {"font": 100 * 2**20, "gfx": 600 * 2**20}
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def _ok(s):                      # same-origin only: blocks other websites from driving the API
        o = s.headers.get("Origin")
        return s.headers.get("Host") in HOSTS and (not o or urllib.parse.urlparse(o).netloc in HOSTS)
    def _json(s, code, obj):
        b = json.dumps(obj).encode(); s.send_response(code); s.send_header("Content-Type", "application/json"); s.send_header("Content-Length", str(len(b))); s.end_headers(); s.wfile.write(b)
    def do_GET(s):
        u = urllib.parse.urlparse(s.path)
        if u.path == "/reveal":
            p = os.path.realpath(urllib.parse.parse_qs(u.query).get("p", [""])[0])
            ok = s._ok() and os.path.exists(p) and any(p == a or p.startswith(a + os.sep) for a in ALLOWED)
            if ok: subprocess.run(["open", "-R", p])
            s.send_response(200 if ok else 404); s.end_headers(); return
        if u.path == "/api/state":
            return s._json(200, pipeline.state()) if s._ok() else s._json(403, {})
        super().do_GET()
    def do_POST(s):
        u = urllib.parse.urlparse(s.path)
        if not s._ok(): return s._json(403, {"status": "rejected", "reason": "forbidden"})
        n = int(s.headers.get("Content-Length", 0))
        try:
            if u.path == "/api/add":
                name = urllib.parse.parse_qs(u.query).get("name", [""])[0]
                kind = "font" if os.path.splitext(name)[1].lower() in pipeline.FONT_EXT else "gfx"
                if n > MAX[kind]: s.rfile.read(0); return s._json(200, {"status": "rejected", "reason": "file too large"})
                return s._json(200, pipeline.add(name, s.rfile.read(n)))
            if u.path == "/api/remove":
                b = json.loads(s.rfile.read(n)); return s._json(200, pipeline.remove(b["kind"], b["key"]))
        except Exception as e: return s._json(200, {"status": "rejected", "reason": "error: %s" % str(e)[:80]})
        s._json(404, {})
    def log_message(s, *a): pass
class S(socketserver.ThreadingMixIn, socketserver.TCPServer): allow_reuse_address = True; daemon_threads = True
with S(("127.0.0.1", PORT), H) as srv:
    print("Fonts and Graphics Library running at http://127.0.0.1:%d  (close this window to stop)" % PORT)
    if "--no-open" not in sys.argv: webbrowser.open("http://127.0.0.1:%d/index.html" % PORT)
    srv.serve_forever()
