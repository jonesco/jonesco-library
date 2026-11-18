# Puts fonts into one family when their names clearly say they belong together but the file's own family name split them:
# the same original folder, and names that are identical once weight, width and slant words are taken off
# ("AM Typewriter Light Condensed", "... Med Cond", "... Bold Cond"; "Kabel ITC T Bold", "... Book", "... Ultra").
# Old Mac names abbreviate those words (Bol, Lig, Med, Ita, Cd, Cn), so the list includes the abbreviations.
# A group is skipped when two of its fonts have exactly the same name (a duplicate copy, not a style), and a font already
# placed by hand (data/groups.json) is left alone.
import re, os, collections
STY = set("""thin hair hairline ult ultra xlight extralight exlight xl light lig lt book bk regular reg roman rom normal norm plain
medium med md mdm demi dem semibold semi sem sb sbold bold bol bd heavy hvy black blk bla blac bl extrabold xbold xbd
cond condensed con cd cn cnd narrow nar nrw compressed comp extended ext xtd wide italic ita it ital itl oblique obl slanted slant""".split())
def toks(s):
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s); s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    return [t for t in re.split(r"[^A-Za-z0-9]+", s) if t]
def base(name):
    t = toks(name)
    while t and t[-1].lower() in STY: t.pop()
    return " ".join(t)
def key(b): return re.sub(r"[^a-z0-9]", "", b.lower())

def autosets(fonts, manual=()):
    """Changes f["fk"] and f["fam"] in place. Returns (sets made, fonts moved, groups skipped).
    Only the fonts that share an original folder and a base name move. They join the family most of them are already in when
    every other font in that family has the same base name; otherwise they get a family of their own, so an odd existing
    family is never pulled into a set."""
    by = collections.defaultdict(list)
    for f in fonts:
        if f["file"] in manual or not f.get("s"): continue
        b = base(f["n"]); k = key(b)
        if len(k) >= 4: by[(os.path.dirname(f["s"]), k)].append((f, b))
    members = collections.defaultdict(list)
    for f in fonts: members[f["fk"]].append(f)
    sets = moved = skipped = 0
    for (d, k), L in sorted(by.items(), key=lambda x: x[0]):
        if len(L) < 2 or len({f["fk"] for f, _ in L}) < 2: continue
        low = [f["n"].lower() for f, _ in L]
        if len(set(low)) < len(low): skipped += 1; continue                  # two with the same name: a second copy, not another style
        name = collections.Counter(b for _, b in L).most_common(1)[0][0]
        ids = {id(f) for f, _ in L}
        dom = collections.Counter(f["fk"] for f, _ in L).most_common(1)[0][0]
        others = [f for f in members[dom] if id(f) not in ids]
        if others and any(key(base(f["n"])) != k for f in others): dom = "auto~" + re.sub(r"[^a-z0-9]", "", d.lower())[-24:] + "~" + k
        elif any(f["n"].lower() in set(low) for f in others): skipped += 1; continue
        for f, _ in L:
            members[f["fk"]] = [x for x in members[f["fk"]] if x is not f]
            f["fk"] = dom; members[dom].append(f)
        for f in members[dom]: f["fam"] = name
        sets += 1; moved += len(L)
    return sets, moved, skipped
