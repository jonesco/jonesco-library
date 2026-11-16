# Builds the browse-only gallery into docs/ (what GitHub Pages serves). Run with .venv/bin/python.
#   fonts -> web-only WOFF2 (letters, figures, punctuation, Mac symbols), graphics -> small grayscale PNGs. No downloads.
import os, re, io, json, sys, shutil, hashlib, logging
from multiprocessing import Pool
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image
logging.disable(logging.CRITICAL)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "docs")
PIN = "https://design.jonesco.com/v/3.5.0/"
MAC = {ord(c) for c in bytes(range(128, 256)).decode("mac_roman")}
KEEP = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | MAC | {0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x20AC}
def font(f):
    src = os.path.join(ROOT, f["file"]); out = "f/" + os.path.splitext(os.path.basename(f["file"]))[0] + ".woff2"
    try:
        t = TTFont(src); o = subset.Options(); o.flavor = "woff2"; o.layout_features = []; o.hinting = False; o.name_IDs = [1, 2, 3, 4, 6]; o.notdef_outline = True; o.glyph_names = False
        s = subset.Subsetter(o); s.populate(unicodes=sorted(KEEP)); s.subset(t); t.flavor = "woff2"; t.save(os.path.join(OUT, out)); return f["file"], out
    except Exception as e: return f["file"], None
def img(g):
    res = {}
    for k, size, d in (("t", 300, "t"), ("v", 800, "p")):
        if not g.get(k): continue
        src = os.path.join(ROOT, g[k]); name = os.path.splitext(os.path.basename(g[k]))[0]
        try:
            im = Image.open(src); jpg = g[k].endswith(".jpg")
            im = im.convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
            im.thumbnail((size, size))
            if jpg: out = "%s/%s.jpg" % (d, name); im.save(os.path.join(OUT, out), "JPEG", quality=70, optimize=True)
            else:
                out = "%s/%s.png" % (d, name)
                (im.convert("L").quantize(16) if g.get("bw") else im.quantize(128)).save(os.path.join(OUT, out), "PNG", optimize=True)
            res[k] = out
        except Exception: pass
    return g["p"], res
if __name__ == "__main__":
    h = open(os.path.join(ROOT, "index.html")).read()
    fm = re.search(r"let FONTS=(\[.*?\]);\nconst LIB", h, re.S); gm = re.search(r"let GFX=(\[.*?\]);const BASE", h, re.S)
    FONTS, GFX = json.loads(fm.group(1)), json.loads(gm.group(1))
    PAGE_ONLY = "--page-only" in sys.argv       # refresh index.html from the fonts and images already in docs/
    if PAGE_ONLY:
        ex = lambda p: os.path.exists(os.path.join(OUT, p))
        fr = {f["file"]: ("f/%s.woff2" % os.path.splitext(os.path.basename(f["file"]))[0]) for f in FONTS}
        fr = {k: (v if ex(v) else None) for k, v in fr.items()}
        ir = {}
        for g in GFX:
            r = {}
            for k, d in (("t", "t"), ("v", "p")):
                if g.get(k):
                    n = os.path.splitext(os.path.basename(g[k]))[0]
                    for e in ("png", "jpg"):
                        if ex("%s/%s.%s" % (d, n, e)): r[k] = "%s/%s.%s" % (d, n, e); break
            ir[g["p"]] = r
    else:
        shutil.rmtree(OUT, ignore_errors=True)
        for d in ("f", "t", "p"): os.makedirs(os.path.join(OUT, d))
        with Pool(6) as pool:
            fr = dict(pool.imap_unordered(font, FONTS, 50)); print("fonts done", sum(1 for v in fr.values() if v), "of", len(FONTS), flush=True)
            ir = dict(pool.imap_unordered(img, GFX, 50)); print("graphics done", len(ir), flush=True)
    fonts = []
    for f in FONTS:
        if not fr.get(f["file"]): continue
        f = dict(f); f["file"] = fr[f["file"]]; f.pop("s", None)
        if f.get("p"): f["p"] = "".join(c for c in f["p"] if ord(c) in KEEP)
        fonts.append(f)
    gfx = []
    for g in GFX:
        r = ir.get(g["p"], {}); g = {k: v for k, v in g.items() if k not in ("a", "hash", "z")}
        g["t"] = r.get("t"); g["v"] = r.get("v"); g["p"] = g["p"] if not g["p"].startswith("added/") else g["p"]
        if not g["t"]: continue
        if not g["v"]: g.pop("v")
        gfx.append(g)
    h = h.replace(fm.group(1), json.dumps(fonts, ensure_ascii=False)).replace(gm.group(1), json.dumps(gfx, ensure_ascii=False))
    h = h.replace('href="system/system.css"', 'href="%ssystem.css"' % PIN).replace('href="system/patterns.css"', 'href="%spatterns.css"' % PIN)
    h = h.replace("/*ONLINE*/false", "true").replace("/*LITE*/false", "true")
    open(os.path.join(OUT, "index.html"), "w").write(h)
    shutil.rmtree(os.path.join(OUT, "icons"), ignore_errors=True); shutil.copytree(os.path.join(ROOT, "icons"), os.path.join(OUT, "icons"))
    open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n"); open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, "CNAME"), "w").write("library.jonesco.com\n")
    print("docs/: %d fonts, %d graphics" % (len(fonts), len(gfx)))
