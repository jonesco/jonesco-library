# Works out which family a font belongs to, so the viewer can group weights and italics together.
import re
from fontTools.ttLib import TTFont
STYLE = re.compile(r"\b(thin|hairline|extra ?light|ultra ?light|light|book|regular|roman|normal|plain|medium|demi ?bold|semi ?bold|demi|bold|extra ?bold|ultra ?bold|heavy|black|italic|oblique|ital|obl|bd|it)\b", re.I)
JUNK = re.compile(r"[A-Za-z]? ?\d{5,}.*")
def strip_style(s):
    t = re.sub(r"\s+", " ", STYLE.sub(" ", s or "")).strip(" -_.,")
    return t or (s or "").strip()
def family_of(path, name="", ps=""):
    """Typographic family (name ID 16) if the font has one; otherwise the family name (ID 1) or the font's own name with the style words
    (Bold, Italic, Light...) taken off. Returns (display name, grouping key)."""
    fam, has16 = "", False
    try:
        nt = TTFont(path, lazy=True)["name"]
        a16 = (nt.getDebugName(16) or "").strip(); a1 = (nt.getDebugName(1) or "").strip()
        fam, has16 = (a16, True) if a16 else (a1, False)
    except Exception: pass
    if not fam or JUNK.fullmatch(fam): fam, has16 = re.sub(r"[-_ ]+", " ", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", (ps or "").split("-")[0])).strip() or name, False
    if not has16: fam = strip_style(fam)
    return fam, re.sub(r"[^a-z0-9]", "", fam.lower()) or re.sub(r"[^a-z0-9]", "", (ps or name).lower())
