# Usage: python3 thumbs.py  -> thumbs/<md5>.png + data/graphics.json
import os, sys, json, hashlib, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
BASE = "/Users/Wes/Developer/_Fonts and Graphics"
ROOT = os.path.expanduser("~/Developer/fonts-and-graphics-library"); TH = os.path.join(ROOT, "thumbs")
TOPS = ["Graphic Items", "Textures", "glyphish-icons", "instagram filters for photoshop", "social-media-buttons", "Vector Social Media Icons", "F0101 social media iconset"]
RASTER = {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".psd", ".pdf", ".bmp"}
PS = {".eps", ".ai", ".ps", ""}
JUNK = {".db", ".txt", ".zip", ".webloc", ".url", ".ds_store", ".read me", ".med res"}
def kind(p):
    e = os.path.splitext(p)[1].lower()
    if e in JUNK: return None
    if e in RASTER: return "raster"
    if e in PS:
        try:
            with open(p, "rb") as f: h = f.read(4)
            if h == b"%!PS" or h[:2] == b"\xc5\xd0": return "ps"
        except OSError: pass
    return "other"
_rm = json.load(open(os.path.join(ROOT, "data", "removed-items.json"))) if os.path.exists(os.path.join(ROOT, "data", "removed-items.json")) else {"gfx": []}
items = []
for top in TOPS:
    for r, d, fs in os.walk(os.path.join(BASE, top)):
        for n in sorted(fs):
            if n.startswith("."): continue
            p = os.path.join(r, n); k = kind(p)
            if n == "DE Catalog.pdf": continue  # user asked to drop the catalog
            if top.startswith("F0101") or top in ("Vector Social Media Icons", "glyphish-icons", "instagram filters for photoshop", "social-media-buttons"): continue  # user asked to drop these sets
            if k and os.path.relpath(p, BASE) not in set(_rm["gfx"]): items.append((p, k))
def make(it):
    p, k = it; rel = os.path.relpath(p, BASE); h = hashlib.md5(rel.encode()).hexdigest()
    out = os.path.join(TH, h + ".png"); parts = rel.split(os.sep)
    rec = {"n": os.path.splitext(parts[-1])[0] if k != "ps" or "." in parts[-1] else parts[-1], "p": rel, "c": "/".join(parts[:-1]) if len(parts) > 1 else parts[0],
           "top": parts[0], "ext": (os.path.splitext(p)[1].lower().lstrip(".") or "eps"), "t": None}
    if os.path.exists(out): rec["t"] = "thumbs/" + h + ".png"; return rec
    tmp = tempfile.mktemp(suffix=".png", dir=tempfile.gettempdir())
    try:
        if k == "ps":
            subprocess.run(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-sDEVICE=png16m", "-r60", "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", "-sOutputFile=" + tmp, p], capture_output=True, timeout=60)
            if os.path.exists(tmp): subprocess.run(["sips", "-Z", "360", tmp, "--out", out], capture_output=True, timeout=30)
        elif k == "raster":
            subprocess.run(["sips", "-s", "format", "png", "-Z", "360", p, "--out", out], capture_output=True, timeout=60)
    except Exception: pass
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    if os.path.exists(out) and os.path.getsize(out) > 0: rec["t"] = "thumbs/" + h + ".png"
    return rec
recs = []
with ThreadPoolExecutor(6) as ex:
    for i, r in enumerate(ex.map(make, items)):
        recs.append(r)
        if i % 200 == 0: print(i, "/", len(items), flush=True)
json.dump(recs, open(os.path.join(ROOT, "data", "graphics.json"), "w"), ensure_ascii=False)
print("items:", len(recs), "with thumbnail:", sum(1 for r in recs if r["t"]), "no preview:", sum(1 for r in recs if not r["t"]))
