# Flags colorless images ("bw": line art, halftones, noise, gray gradients) so dark mode can reverse them out. Anything with color is left alone.
import json, os
from PIL import Image
ROOT = os.path.expanduser("~/Developer/fonts-and-graphics-library/")
def is_bw(path):
    try:
        im = Image.open(path).convert("RGBA").resize((64, 64))
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); px = list(bg.convert("RGB").getdata())
    except Exception: return False
    gray = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) < 24) / len(px)
    return gray > .97
if __name__ == "__main__":
    p = ROOT + "data/graphics.json"; G = json.load(open(p)); n = 0
    for g in G:
        g.pop("bw", None)
        if g.get("t") and g["ext"] != "svg" and is_bw(ROOT + g["t"]): g["bw"] = 1; n += 1
    json.dump(G, open(p, "w"), ensure_ascii=False); print(n, "of", len(G), "flagged as colorless (reversed in dark mode)")
    import collections; print(collections.Counter((g["top"], bool(g.get("bw"))) for g in G if g.get("t")))
