# Publishes what is in the library to library.jonesco.com: rebuilds the page, converts only the new fonts and graphics
# into docs/, commits docs/ and pushes. GitHub Pages then updates in about a minute. Run with .venv/bin/python.
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PY = os.path.join(ROOT, ".venv", "bin", "python")
def run(*a, **k): return subprocess.run(a, cwd=ROOT, text=True, capture_output=True, **k)
def step(msg, r):
    if r.returncode: print("FAILED: " + msg + "\n" + (r.stderr or r.stdout)[-600:], flush=True); sys.exit(1)
print("Rebuilding the page...", flush=True)
step("build_viewer", run(PY, "tools/build_viewer.py"))
print("Converting new fonts and graphics...", flush=True)
r = run(PY, "tools/build_lite.py", "--update"); step("build_lite", r)
new = [l for l in r.stdout.splitlines() if l.startswith("new fonts")]
run("git", "add", "docs")
if run("git", "diff", "--cached", "--quiet").returncode == 0: print("Nothing new to publish.", flush=True); sys.exit(0)
step("commit", run("git", "commit", "-q", "-m", "Publish library update" + (" (%s)" % new[0] if new else "")))
print("Pushing...", flush=True)
step("push", run("git", "push", "-q", "origin", "main"))
print("Published. library.jonesco.com updates in about a minute.", flush=True)
