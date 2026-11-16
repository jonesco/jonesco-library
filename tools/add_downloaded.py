# Copies the already-modern .ttf/.otf from Downloaded Fonts as-is and writes data/downloaded-fonts.json
import os, shutil, json, fontforge
src = "/Users/Wes/Developer/_Fonts and Graphics/Downloaded Fonts"; out = os.path.expanduser("~/Developer/fonts-and-graphics-library/fonts/downloaded"); os.makedirs(out, exist_ok=True)
recs = []
for r, d, fs in os.walk(src):
    for n in fs:
        if n.startswith(".") or os.path.splitext(n)[1].lower() not in (".ttf", ".otf"): continue
        p = os.path.join(r, n); dst = os.path.join(out, n)
        try:
            f = fontforge.open(p); shutil.copy2(p, dst)
            recs.append(dict(source=p, ok=True, out=dst, fontname=f.fontname, family=f.familyname, full=f.fullname, weight=f.weight, glyphs=len(list(f.glyphs())), fixed=False, italic=f.italicangle != 0))
        except Exception as e: recs.append(dict(source=p, ok=False, error=str(e)[:100]))
json.dump(recs, open(os.path.expanduser("~/Developer/fonts-and-graphics-library/data/downloaded-fonts.json"), "w"), indent=1)
print(len([r for r in recs if r["ok"]]), "copied,", len([r for r in recs if not r["ok"]]), "failed")
