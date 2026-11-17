# Usage: python3 build_viewer.py  -> writes ../index.html from ../data/*.json
import json, glob, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
def pretty(ps):                      # GarageGothic-Black -> Garage Gothic Black
    t = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)|[-_]+", " ", ps or "")
    return re.sub(r"\s+", " ", t).strip() or ps
fonts = []
NOT_FONTS = {"graphics", "added", "removed", "removed-items", "fontnames", "gfxhash"}
for m in sorted(glob.glob(os.path.join(root, "data", "*.json"))):
    if os.path.splitext(os.path.basename(m))[0] in NOT_FONTS: continue
    for r in json.load(open(m)):
        if not r.get("ok"): continue
        parts = r["source"].split("/Fonts Collection/")[-1].split("/")
        name = r["family"] or r["fontname"]
        n = (r["full"] or r["fontname"] or "").lower()
        style = "script" if re.search(r"script|hand|brush|write", n) else "mono" if r.get("fixed") else "other"
        fonts.append({"n": (r.get("full") if " " in (r.get("full") or "") else pretty(r.get("full") or r["fontname"])), "f": r["fontname"], "file": os.path.relpath(r["out"], root),
                      "c": parts[1] if len(parts) > 2 and parts[0] == "Wesley J Collection" else parts[0],
                      "s": r["source"], "g": r["glyphs"], "i": bool(r.get("italic")), "t": style})
cov_path = os.path.join(root, "data", "coverage.cache")
cov = json.load(open(cov_path)) if os.path.exists(cov_path) else {}
try:
    from fontTools.ttLib import TTFont
except ImportError: TTFont = None
LOWER = set(map(ord, "abcdefghijklmnopqrstuvwxyz"))
def partial(f):
    if f["file"] in cov: return cov[f["file"]]
    r = ""
    if TTFont:
        try:
            cm = TTFont(os.path.join(root, f["file"]), lazy=True).getBestCmap() or {}
            if not LOWER <= set(cm):      # not a full alphabet: expert set, caps-only, symbols
                r = "".join(chr(c) for c in sorted(cm) if c > 32 and not 126 < c < 161 and chr(c).isprintable())[:300]
        except Exception: pass
    cov[f["file"]] = r; return r
def tidy(n):   # "12 Akzidenz Grotesk** Black   09003" -> "Akzidenz Grotesk Black": drop the point size, the asterisks and the catalog code, none of which are in the font file
    if re.search(r"\*|\s\d{5}$", n):
        n = re.sub(r"^\d{1,2}\s+(?:pt\.?\s+)?(?=\D)", "", n)
        n = re.sub(r"\s+\d{5}$", "", n.replace("*", ""))
    return re.sub(r"\s+", " ", n).strip()
FIX = {"Itlic": "Italic", "Bld": "Bold", "Ital": "Italic"}
def fromps(ps):   # the name table holds a catalog code ("e 00100036"): use the PostScript name (Einhorn-Normal -> Einhorn Normal) and spell out its abbreviations
    return " ".join(FIX.get(w, w) for w in pretty(ps).split())
for f in fonts:
    f["n"] = fromps(f["f"]) if re.fullmatch(r"[A-Za-z] ?\d{6,10}.*", f["n"].strip()) else tidy(f["n"])
best = {}
for f in fonts:                     # dedupe by PostScript name, keep the most complete copy
    k = f["f"].lower()
    if k not in best or f["g"] > best[k]["g"]: best[k] = f
print(len(fonts) - len(best), "duplicates dropped")
fonts = sorted(best.values(), key=lambda x: x["n"].lower())
# Wes's rule: a font that can't set the sentence is dropped. Digits are optional (relaxed: fonts with all 52 letters stay).
NEED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
def covers(f):
    k = "need2:" + f["file"]
    if k not in cov:
        try: cm = TTFont(os.path.join(root, f["file"]), lazy=True).getBestCmap() or {}
        except Exception: cm = {}
        cov[k] = all(ord(c) in cm for c in NEED)
    return cov[k]
keep, removed = [], []
for f in fonts:
    f["n"] = f["n"].strip()
    (keep if covers(f) else removed).append(f)
fonts = keep
SENT = sorted(set("The quick brown fox jumps over the lazy dog 0123456789".replace(" ", "")))
def missing(f):                      # characters of the sample sentence this font can't set; cached
    k = "miss:" + f["file"]
    if k not in cov:
        try: cm = TTFont(os.path.join(root, f["file"]), lazy=True).getBestCmap() or {}
        except Exception: cm = {}
        cov[k] = "".join(c for c in SENT if ord(c) not in cm)
    return cov[k]
for f in fonts:
    m = missing(f)
    if m: f["x"] = m                 # incomplete: lists what's missing
for f in removed:                    # delete only this pipeline's converted copy; originals are never touched
    fp = os.path.join(root, f["file"])
    if os.path.exists(fp): os.remove(fp)
if removed:
    old = json.load(open(os.path.join(root, "data", "removed.json"))) if os.path.exists(os.path.join(root, "data", "removed.json")) else []
    seen = {(o["name"], o["original"]) for o in old}
    json.dump(old + [{"name": f["n"], "collection": f["c"], "original": f["s"]} for f in removed if (f["n"], f["s"]) not in seen], open(os.path.join(root, "data", "removed.json"), "w"), indent=1, ensure_ascii=False)
_rm = json.load(open(os.path.join(root, "data", "removed-items.json"))) if os.path.exists(os.path.join(root, "data", "removed-items.json")) else {"fonts": [], "gfx": []}
_ad = json.load(open(os.path.join(root, "data", "added.json"))) if os.path.exists(os.path.join(root, "data", "added.json")) else {"fonts": [], "gfx": []}
fonts = [f for f in fonts if f["file"] not in set(_rm["fonts"])]
json.dump([f["f"] for f in fonts], open(os.path.join(root, "data", "fontnames.json"), "w"))   # the drop box uses this to skip duplicates
fonts += [f for f in _ad["fonts"] if f["file"] not in set(_rm["fonts"]) and os.path.exists(os.path.join(root, f["file"]))]   # an added font whose file is gone is left out rather than shown blank
sys.path.insert(0, here)
from traits import traits                  # category, weight, width, slant, scripts: what each font file says about itself
tp = os.path.join(root, "data", "traits.cache")
tc = json.load(open(tp)) if os.path.exists(tp) else {}
for f in fonts:
    k = f["file"] + "|" + f["n"]
    if k not in tc:
        try: tc[k] = traits(os.path.join(root, f["file"]), f["n"])
        except Exception: tc[k] = {"k": "d", "w": 400, "wd": 1, "it": int(bool(f.get("i"))), "l": 0}
    f.update(tc[k]); f.pop("t", None)
from family import family_of
fp_ = os.path.join(root, "data", "family.cache")
fc = json.load(open(fp_)) if os.path.exists(fp_) else {}
for f in fonts:                                 # which family each font belongs to (cached by file)
    if f["file"] not in fc: fc[f["file"]] = family_of(os.path.join(root, f["file"]), f["n"], f["f"])
    f["fam"], f["fk"] = fc[f["file"]]
json.dump(fc, open(fp_, "w"))
_keys = {f["fk"] for f in fonts}                # "Aachen D" is "Aachen" with a one-letter suffix: join them
_join = {}
for f in fonts:
    w = f["fam"].split(" ")
    if len(w) > 1 and len(w[-1]) == 1 and w[-1].isalpha():
        base = re.sub(r"[^a-z0-9]", "", " ".join(w[:-1]).lower())
        if base in _keys and base != f["fk"]: _join[f["fk"]] = (" ".join(w[:-1]), base)
for f in fonts:
    if f["fk"] in _join: f["fam"], f["fk"] = _join[f["fk"]]
print(len(_join), "one-letter-suffix families joined:", sorted(v[0] for v in _join.values())[:20])
fonts.sort(key=lambda f: (f["fk"], f.get("w", 400), f.get("it", 0), f["n"].lower()))
json.dump(tc, open(tp, "w"))
json.dump(cov, open(cov_path, "w"))
print(len(removed), "fonts removed: can't set the sample sentence")
gp = os.path.join(root, "data", "graphics.json")
gfx = [g for g in (json.load(open(gp)) if os.path.exists(gp) else []) if g["p"] not in set(_rm["gfx"])] + [g for g in _ad["gfx"] if g["p"] not in set(_rm["gfx"])]
for g in gfx:                                  # originals with an empty data fork can't be downloaded; the viewer falls back to the preview
    fp = g.get("a") or ("/Users/Wes/Developer/_Fonts and Graphics/" + g["p"])
    try:
        if os.path.getsize(fp) == 0: g["z"] = 1
    except OSError: g["z"] = 1
gfx.sort(key=lambda g: g["p"])
html = open(os.path.join(here, "viewer_template.html")).read().replace("/*DATA*/[]", json.dumps(fonts, ensure_ascii=False)).replace("/*GFX*/[]", json.dumps(gfx, ensure_ascii=False))
open(os.path.join(root, "index.html"), "w").write(html)
print(len(fonts), "fonts ->", os.path.join(root, "index.html"))
