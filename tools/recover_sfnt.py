# Recovers TrueType suitcases FontForge can't open. Run with .venv/bin/python.
# Usage: recover_sfnt.py data/_retry.json   -> fonts/recovered/*.ttf + data/recovered.json
import sys, os, json, io, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfnt_extract import sfnts
from fontTools.ttLib import TTFont
ROOT = os.path.expanduser("~/Developer/fonts-and-graphics-library"); OUT = os.path.join(ROOT, "fonts", "recovered"); os.makedirs(OUT, exist_ok=True)
recs = []
for src in json.load(open(sys.argv[1])):
    try:
        for k, blob in enumerate(sfnts(src)):
            try:
                t = TTFont(io.BytesIO(blob), lazy=False)
                nm = lambda i: (t["name"].getDebugName(i) or "") if "name" in t else ""
                fam, full, ps = nm(1), nm(4), nm(6)
                if not (full or ps): raise ValueError("no name")
                g = len(t.getGlyphOrder())
                if g < 2: raise ValueError("no glyphs")
                out = os.path.join(OUT, (ps or "font").replace("/", "_")[:60] + "-" + hashlib.md5(src.encode()).hexdigest()[:6] + ".ttf")
                t.save(out); TTFont(out)  # round-trip check
                post = t["post"] if "post" in t else None
                recs.append(dict(source=src, ok=True, out=out, fontname=ps or full, family=fam, full=full, weight="", glyphs=g,
                                 fixed=bool(post and post.isFixedPitch), italic=bool(post and post.italicAngle)))
            except Exception as e: recs.append(dict(source=src, ok=False, error=str(e)[:100]))
    except Exception as e: recs.append(dict(source=src, ok=False, error="parse: " + str(e)[:80]))
json.dump(recs, open(os.path.join(ROOT, "data", "recovered.json"), "w"), indent=1)
print("recovered", sum(r["ok"] for r in recs), "failed", sum(not r["ok"] for r in recs))
