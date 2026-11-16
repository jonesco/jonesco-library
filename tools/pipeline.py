# Adding and removing items for the viewer's drop box. Used by serve.py. Run with .venv/bin/python (needs fontTools).
import os, io, re, json, hashlib, subprocess, tempfile, threading
from fontTools.ttLib import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "/Users/Wes/Developer/_Fonts and Graphics/"
D = lambda n: os.path.join(ROOT, "data", n)
LOCK = threading.Lock()
FONT_EXT = {".ttf", ".otf"}
GFX_EXT = {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".psd", ".pdf", ".eps", ".ai", ".svg"}
PS_EXT = {".eps", ".ai", ".pdf"}
LETTERS = set(map(ord, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
SENT = sorted(set("The quick brown fox jumps over the lazy dog 0123456789".replace(" ", "")))

def jload(p, d):
    try: return json.load(open(p))
    except Exception: return d
def jsave(p, o): json.dump(o, open(p, "w"), ensure_ascii=False)
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:80] or "item"
def pretty(ps):
    t = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)|[-_]+", " ", ps or "")
    return re.sub(r"\s+", " ", t).strip() or ps
def inside(p): r = os.path.realpath(p); return r.startswith(os.path.realpath(ROOT) + os.sep)

def state():
    a = jload(D("added.json"), {"fonts": [], "gfx": []})
    return {"fonts": a["fonts"], "gfx": a["gfx"], "removed": jload(D("removed-items.json"), {"fonts": [], "gfx": []})}

def add_font(name, data):
    ext = os.path.splitext(name)[1].lower()
    try: t = TTFont(io.BytesIO(data), lazy=True); cm = t.getBestCmap() or {}
    except Exception as e: return {"status": "rejected", "reason": "not a readable font"}
    if "fvar" in t: return _add_variable(name, data, t)
    nm = lambda i: (t["name"].getDebugName(i) or "").strip() if "name" in t else ""
    full, ps = nm(4), nm(6)
    if not (full or ps): return {"status": "rejected", "reason": "has no name"}
    miss_letters = [chr(c) for c in sorted(LETTERS) if c not in cm]
    if miss_letters: return {"status": "rejected", "reason": "missing letters (%s…)" % "".join(miss_letters[:6])}
    f = ps or safe(full)
    with LOCK:
        a = jload(D("added.json"), {"fonts": [], "gfx": []})
        have = {x.lower() for x in jload(D("fontnames.json"), [])} | {x["f"].lower() for x in a["fonts"]}
        if f.lower() in have: return {"status": "skipped", "reason": "already in the library"}
        h = hashlib.md5(data).hexdigest()[:6]; rel = "fonts/%s-%s%s" % (safe(f), h, ext)
        open(os.path.join(ROOT, rel), "wb").write(data)
        n = full if " " in full else pretty(full or ps)
        post = t["post"] if "post" in t else None
        kind = "script" if re.search(r"script|hand|brush|write", n.lower()) else "mono" if (post and post.isFixedPitch) else "other"
        item = {"n": n.strip(), "f": f, "file": rel, "c": "Added", "s": "", "g": len(t.getGlyphOrder()), "i": bool(post and post.italicAngle), "t": kind}
        try:
            from traits import traits
            item.update(traits(os.path.join(ROOT, rel), n)); item.pop("t", None)
        except Exception: pass
        m = "".join(c for c in SENT if ord(c) not in cm)
        if m: item["x"] = m
        a["fonts"].append(item); jsave(D("added.json"), a)
    return {"status": "added", "kind": "font", "item": item}

def _add_variable(name, data, t):
    """A variable font holds many weights in one file; its PostScript name is only that of the default weight, which used to make the
    first one look like a duplicate of that weight's static file. Each named style becomes its own static font instead."""
    from fontTools.varLib import instancer
    nm = lambda f, i: (f["name"].getDebugName(i) or "").strip()
    fam = nm(t, 16) or nm(t, 1)
    items, skipped = [], 0
    for inst in t["fvar"].instances:
        sub = nm(t, inst.subfamilyNameID)
        if not (fam and sub): continue
        try:
            f = instancer.instantiateVariableFont(TTFont(io.BytesIO(data)), dict(inst.coordinates), inplace=False)
            full, ps = "%s %s" % (fam, sub), "%s-%s" % (fam.replace(" ", ""), sub.replace(" ", ""))
            for rec in list(f["name"].names):
                if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 25): f["name"].removeNames(nameID=rec.nameID)
            for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
                for i, v in ((1, fam), (2, "Regular"), (3, ps), (4, full), (6, ps), (16, fam), (17, sub)): f["name"].setName(v, i, pid, eid, lid)
            buf = io.BytesIO(); f.save(buf)
            r = add_font(ps + ".ttf", buf.getvalue())
            if r["status"] == "added": items += r.get("items") or [r["item"]]
            else: skipped += 1
        except Exception: continue
    if items: return {"status": "added", "kind": "font", "item": items[-1], "items": items}
    return {"status": "skipped", "reason": "every weight in this variable font is already in the library"} if skipped else {"status": "rejected", "reason": "variable font with no named styles"}

def _gs(src, out, r):
    tmp = tempfile.mktemp(suffix=".png")
    try:
        subprocess.run(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-dFirstPage=1", "-dLastPage=1", "-sDEVICE=png16m", "-r%d" % r, "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", "-sOutputFile=" + tmp, src], capture_output=True, timeout=90)
        return os.path.exists(tmp) and subprocess.run(["sips", "-Z", "1000" if r > 100 else "360", tmp, "--out", out], capture_output=True, timeout=30).returncode == 0
    except Exception: return False
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def _base_hashes():
    h = jload(D("gfxhash.json"), None)
    if h is None:                     # one-time: hash the original graphics so duplicates are caught
        h = {}
        for g in jload(D("graphics.json"), []):
            try: h.setdefault(hashlib.md5(open(BASE + g["p"], "rb").read()).hexdigest(), g["p"])
            except Exception: pass
        jsave(D("gfxhash.json"), h)
    return h

def add_graphic(relname, data):
    parts = [safe(p) for p in relname.split("/") if p not in ("", ".", "..")]
    if not parts: return {"status": "rejected", "reason": "no file name"}
    fname = parts[-1]; ext = os.path.splitext(fname)[1].lower()
    if ext not in GFX_EXT: return {"status": "rejected", "reason": "unsupported type " + (ext or "(none)")}
    coll = parts[0] if len(parts) > 1 else "Added"; c = "/".join(parts[:-1]) or "Added"
    hh = hashlib.md5(data).hexdigest()
    with LOCK:
        a = jload(D("added.json"), {"fonts": [], "gfx": []})
        base = _base_hashes()
        if hh in base: return {"status": "skipped", "reason": "already in the library"}
        if any(x.get("hash") == hh for x in a["gfx"]): return {"status": "skipped", "reason": "already added"}
        folder = os.path.join(ROOT, "added", "graphics", *( [c] if c != "Added" else ["Added"] ))
        os.makedirs(folder, exist_ok=True); path = os.path.join(folder, fname)
        if os.path.exists(path): fname = os.path.splitext(fname)[0] + "-" + hh[:6] + ext; path = os.path.join(folder, fname)
        open(path, "wb").write(data)
        key = os.path.relpath(path, ROOT); h = hashlib.md5(key.encode()).hexdigest()
        t = v = None
        if ext == ".svg": t = key
        else:
            th = os.path.join(ROOT, "thumbs", h + ".png"); ok = False
            if ext in PS_EXT: ok = _gs(path, th, 60)
            else: ok = subprocess.run(["sips", "-s", "format", "png", "-Z", "360", path, "--out", th], capture_output=True, timeout=90).returncode == 0 and os.path.exists(th)
            if ok and os.path.exists(th): t = "thumbs/%s.png" % h
            if t and ext not in (".png", ".gif"):
                jpg = ext in (".tif", ".tiff", ".jpg", ".jpeg", ".psd")
                pv = os.path.join(ROOT, "previews", h + (".jpg" if jpg else ".png"))
                if jpg: ok = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", "-Z", "1000", path, "--out", pv], capture_output=True, timeout=90).returncode == 0
                else: ok = _gs(path, pv, 200)
                if ok and os.path.exists(pv): v = "previews/" + os.path.basename(pv)
        item = {"n": os.path.splitext(fname)[0], "p": key, "a": path, "c": c, "top": coll, "ext": ext.lstrip("."), "t": t, "hash": hh}
        try:
            from classify import is_bw
            if t and ext != ".svg" and is_bw(os.path.join(ROOT, t)): item["bw"] = 1
        except Exception: pass
        if v: item["v"] = v
        a["gfx"].append(item); jsave(D("added.json"), a)
    return {"status": "added", "kind": "graphic", "item": item}

def add(relname, data):
    ext = os.path.splitext(relname)[1].lower()
    if ext in FONT_EXT: return add_font(os.path.basename(relname), data)
    return add_graphic(relname, data)

def remove(kind, key):
    """Hides an item and deletes this library's copy of it. Originals in _Fonts and Graphics are never touched."""
    with LOCK:
        r = jload(D("removed-items.json"), {"fonts": [], "gfx": []}); a = jload(D("added.json"), {"fonts": [], "gfx": []})
        lst = r["fonts" if kind == "font" else "gfx"]
        if key not in lst: lst.append(key)
        jsave(D("removed-items.json"), r); doomed = []
        if kind == "font":
            doomed.append(os.path.join(ROOT, key)); a["fonts"] = [x for x in a["fonts"] if x["file"] != key]
        else:
            h = hashlib.md5(key.encode()).hexdigest()
            doomed += [os.path.join(ROOT, "thumbs", h + ".png"), os.path.join(ROOT, "previews", h + ".png"), os.path.join(ROOT, "previews", h + ".jpg")]
            for x in a["gfx"]:
                if x["p"] == key: doomed.append(x["a"])
            a["gfx"] = [x for x in a["gfx"] if x["p"] != key]
        jsave(D("added.json"), a)
        for p in doomed:
            if inside(p) and os.path.isfile(p): os.remove(p)
    return {"status": "removed"}
