# Reads what a font file says about itself so the viewer can filter like Google Fonts: category, weight, width, slant, scripts.
import os, re, json
from fontTools.ttLib import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANS = re.compile(r"\bsans\b|grotesk|grotesque|gothic|helvetica|arial|univers|futura|akzidenz|frutiger|gill|avenir|verdana|tahoma|geneva|optima|syntax|myriad|segoe|trade ?gothic|din\b|folio|eurostile|bank gothic|franklin|news gothic|lucida sans|formata|meta\b|officina|rotis sans|stone sans|thesis sans|scala sans|nobel|vag|rounded")
SERIF = re.compile(r"\bserif\b|roman\b|garamond|caslon|bodoni|times|baskerville|bembo|palatino|century|didot|georgia|minion|utopia|clarendon|plantin|perpetua|goudy|jenson|caledonia|scotch|egyptian|slab|antiqua|cheltenham|bookman|galliard|sabon|janson|electra|fournier|walbaum|ionic|excelsior|melior|aldus|trump|dutch|new york|bell\b|cooper|windsor|rockwell|serifa|memphis|stymie|lubalin|souvenir|schneidler|cochin")
HAND = re.compile(r"script|hand|brush|pen\b|marker|scrawl|cursive|calligraph|written|writing|signature|ink\b|chancery|italic hand|mistral|zapf chancery|poster ?bodoni script|lettering|doodle|sketch|dry ?brush|felt")
MONO = re.compile(r"\bmono\b|\bmonospace|courier|typewriter|console|monaco|andale mono|\bocr\b|letter gothic|prestige|\bpica\b|\belite\b")
SYM = re.compile(r"dingbat|symbol|ornament|\bpi\b|\bpi \d|border|icons?\b|wingding|webding|cartographic|picto|arrows|bullets|stars|flowers|printers? ?ornaments|embellish|vignette|fleuron|zodiac|signs\b|logos?\b")
def cat(name, os2, post, cm):
    n = (name or "").lower()
    pan = list(getattr(os2, "panose", None).__dict__.values()) if os2 is not None and hasattr(os2, "panose") else []
    fam = pan[0] if pan else 0; ser = pan[1] if len(pan) > 1 else 0; prop = pan[3] if len(pan) > 3 else 0
    if fam == 5 or SYM.search(n): return "y"
    if (post is not None and post.isFixedPitch) or prop == 9 or MONO.search(n): return "m"
    if fam == 3 or HAND.search(n): return "h"
    if fam == 4: return "d"
    if fam == 2 and ser >= 11: return "n"
    if fam == 2 and 2 <= ser <= 10: return "s"
    if SANS.search(n): return "n"
    if SERIF.search(n): return "s"
    return "d"
def shape(t, cm):
    """Serif or sans from the capital I: a plain stem is a rectangle (about 4 to 8 segments); serifs add many more."""
    try:
        from fontTools.pens.recordingPen import RecordingPen
        g = cm.get(0x49)
        if not g: return None
        gs = t.getGlyphSet(); pen = RecordingPen(); gs[g].draw(pen)
        segs = sum(1 for op, _ in pen.value if op in ("lineTo", "curveTo", "qCurveTo"))
        contours = sum(1 for op, _ in pen.value if op in ("closePath", "endPath"))
        if contours != 1: return None
        return "n" if segs <= 8 else "s" if 10 <= segs <= 40 else None
    except Exception: return None
def traits(path, name):
    t = TTFont(path, lazy=True)
    os2 = t["OS/2"] if "OS/2" in t else None; post = t["post"] if "post" in t else None
    try: cm = t.getBestCmap() or {}
    except Exception: cm = {}
    w = os2.usWeightClass if os2 is not None and 100 <= os2.usWeightClass <= 900 else 400
    wd = os2.usWidthClass if os2 is not None and 1 <= os2.usWidthClass <= 9 else 5
    nl = (name or "").lower()
    if re.search(r"\b(thin|hairline)\b", nl): w = min(w, 200)
    elif re.search(r"\b(ultra ?light|extra ?light)\b", nl): w = min(w, 200)
    elif re.search(r"\blight\b", nl) and w >= 400: w = 300
    elif re.search(r"\b(black|heavy|ultra|extra ?bold|fat)\b", nl) and w < 800: w = 800
    elif re.search(r"\b(bold|semi ?bold|demi)\b", nl) and w < 600: w = 700
    if re.search(r"\b(cond(ensed)?|narrow|compressed|compact)\b", nl): wd = min(wd, 3)
    elif re.search(r"\b(extended|expanded|wide)\b", nl): wd = max(wd, 7)
    ital = bool((os2 is not None and os2.fsSelection & 1) or (post is not None and post.italicAngle) or re.search(r"italic|oblique|slanted", nl))
    has = lambda lo, hi, k: sum(1 for c in range(lo, hi + 1) if c in cm) >= k
    langs = 0
    if all(c in cm for c in map(ord, "ŁłŚśŻżĄąĘęĆćŃńÓóŹź")) or has(0x100, 0x17F, 90): langs |= 1     # Latin Extended
    if has(0x410, 0x44F, 55): langs |= 2                                                        # Cyrillic
    if has(0x391, 0x3C9, 40): langs |= 4                                                        # Greek
    if has(0x3041, 0x3096, 60) or has(0x30A1, 0x30FA, 60): langs |= 8                           # Japanese kana
    k = cat(name, os2, post, cm)
    if k == "d" and not (os2 is not None and list(os2.panose.__dict__.values())[0] == 4):   # unknown, not declared decorative: look at the shape
        k = shape(t, cm) or "d"
    return {"k": k, "w": w, "wd": 0 if wd <= 3 else 2 if wd >= 7 else 1, "it": 1 if ital else 0, "l": langs}
