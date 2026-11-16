# Runs inside FontForge. Usage: fontforge -lang=py -script ff_worker.py <src> <outdir>
# Opens every font found in <src> (data fork, else resource fork), writes OpenType, prints one JSON line per font.
import fontforge, sys, os, json, re, hashlib

src, outdir = sys.argv[1], sys.argv[2]

def candidates(p):
    out = []
    if os.path.getsize(p) > 0: out.append(p)
    try:
        if os.path.getsize(p + "/..namedfork/rsrc") > 0: out.append(p + "/..namedfork/rsrc")
    except OSError: pass
    return out

def safe(s): return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:80] or "font"

results = []
seen = set()
for cand in candidates(src):
    try: names = fontforge.fontsInFile(cand)
    except Exception: names = ()
    if not names: names = (None,)   # single Type 1 outline fonts: fontsInFile() returns nothing, open() works
    for n in names:
        spec = cand if (n is None or len(names) == 1) else cand + "(" + n + ")"
        rec = {"source": src, "face": n}
        try:
            f = fontforge.open(spec)
            if len(list(f.glyphs())) == 0: raise ValueError("no glyphs")
            for g in f.glyphs():                      # keep Mac-encoded dingbats reachable
                if g.unicode == -1 and 32 <= g.encoding < 256:
                    try: g.unicode = ord(bytes([g.encoding]).decode("mac_roman"))
                    except Exception: pass
            try: f.reencode("UnicodeFull")
            except Exception: pass
            key = f.fontname
            if key in seen: continue
            seen.add(key)
            h = hashlib.md5(src.encode()).hexdigest()[:6]
            out = os.path.join(outdir, safe(f.fontname) + "-" + h + ".otf")
            f.generate(out)
            chk = fontforge.open(out)
            rec.update(ok=True, out=out, fontname=f.fontname, family=f.familyname, full=f.fullname,
                       weight=f.weight, glyphs=len(list(chk.glyphs())), fixed=bool(f.os2_panose[3] == 9) if f.os2_panose else False,
                       italic=f.italicangle != 0)
        except Exception as e:
            rec.update(ok=False, error=str(e)[:120])
        results.append(rec)
for r in results: print("@@" + json.dumps(r))
