# Usage: python3 convert.py <collection_dir> <outdir> <manifest.json>
import os, sys, json, subprocess
from concurrent.futures import ThreadPoolExecutor
root, outdir, manifest = sys.argv[1:4]
SKIP = {".bmap", ".afm", ".amfm", ".txt", ".rtf", ".doc", ".read me", ".url", ".lst", ".fam", ".screen", ".scr", ".ds_store", ".png", ".gif", ".jpg", ".pdf", ".sit", ".sea", ".cpt", ".zip", ".ps", ".eps", ".tif", ".psd", ".db", ".map", ".ttxt"}
files = []
for r, d, fs in os.walk(root):
    for n in fs:
        if os.path.splitext(n)[1].lower() in SKIP or n.startswith("."): continue
        files.append(os.path.join(r, n))
os.makedirs(outdir, exist_ok=True)
worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ff_worker.py")
def run(p):
    try:
        o = subprocess.run(["fontforge", "-lang=py", "-script", worker, p, outdir], capture_output=True, timeout=90)
        o.stdout = o.stdout.decode("utf-8", "replace"); o.stderr = ""
        recs = [json.loads(l[2:]) for l in o.stdout.splitlines() if l.startswith("@@")]
        if not recs and o.returncode != 0: recs = [{"source": p, "ok": False, "error": "crash rc=%d" % o.returncode}]
        return recs
    except subprocess.TimeoutExpired: return [{"source": p, "ok": False, "error": "timeout"}]
res = []
with ThreadPoolExecutor(6) as ex:
    for i, recs in enumerate(ex.map(run, files)):
        res += recs
        if i % 100 == 0: print(i, "/", len(files), flush=True)
json.dump(res, open(manifest, "w"), indent=1)
ok = [r for r in res if r.get("ok")]
print("candidates:", len(files), "fonts converted:", len(ok), "failed:", len([r for r in res if not r.get("ok")]))
