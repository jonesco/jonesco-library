# Lists what has been deleted from the library (it sits in deleted/) and puts items back.
#   .venv/bin/python tools/restore.py              list deleted items
#   .venv/bin/python tools/restore.py <text>       restore every deleted item whose name contains <text>  (or "all")
# Then the page is rebuilt. To get rid of something for good, drag its files out of deleted/ to the Trash yourself.
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline
items = pipeline.deleted()
if len(sys.argv) < 2:
    for m in items: print("%-5s %s  (deleted %s)" % (m["kind"], m["key"], m["when"]))
    print("%d deleted. Restore with: restore.py <part of the name>, or all" % len(items)); sys.exit(0)
q = sys.argv[1].lower(); hit = [m for m in items if q == "all" or q in m["key"].lower()]
for m in hit: print(m["key"], pipeline.restore(m["kind"], m["key"])["status"])
if hit: subprocess.run([sys.executable, os.path.join(pipeline.ROOT, "tools", "build_viewer.py")], cwd=pipeline.ROOT, capture_output=True); print("Page rebuilt. Reload the library.")
else: print("Nothing matched.")
