# Large (up to 1000px) previews for the detail view. EPS/PostScript are re-rendered from the vector source.
import os, json, subprocess, tempfile, hashlib
from concurrent.futures import ThreadPoolExecutor
BASE = "/Users/Wes/Developer/_Fonts and Graphics/"; ROOT = os.path.expanduser("~/Developer/fonts-and-graphics-library/")
G = json.load(open(ROOT + "data/graphics.json"))
def go(x):
    if not x["t"] or x["ext"] in ("png", "gif"): x.pop("v", None); return x
    h = hashlib.md5(x["p"].encode()).hexdigest(); src = BASE + x["p"]
    jpg = x["ext"] in ("tif", "tiff", "jpg", "jpeg", "psd")
    out = ROOT + "previews/" + h + (".jpg" if jpg else ".png")
    if not (os.path.exists(out) and os.path.getsize(out) > 0):
        tmp = tempfile.mktemp(suffix=".png")
        try:
            if jpg: subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", "-Z", "1000", src, "--out", out], capture_output=True, timeout=90)
            else:
                subprocess.run(["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-sDEVICE=png16m", "-r200", "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4", "-sOutputFile=" + tmp, src], capture_output=True, timeout=90)
                if os.path.exists(tmp): subprocess.run(["sips", "-Z", "1000", tmp, "--out", out], capture_output=True, timeout=30)
        except Exception: pass
        finally:
            if os.path.exists(tmp): os.remove(tmp)
    if os.path.exists(out) and os.path.getsize(out) > 0: x["v"] = "previews/" + os.path.basename(out)
    return x
with ThreadPoolExecutor(6) as ex: G = list(ex.map(go, G))
json.dump(G, open(ROOT + "data/graphics.json", "w"), ensure_ascii=False)
print("previews:", sum(1 for x in G if x.get("v")), "of", len(G))
