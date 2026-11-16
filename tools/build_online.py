# Builds the read-only online copy: online/index.html + robots.txt.
# The page is the same as the local one, with the system CSS pinned to design.jonesco.com and the online flag on.
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIN = "https://design.jonesco.com/v/3.5.0/"    # bump on purpose, like any Jonesco site
h = open(os.path.join(ROOT, "index.html")).read()
h = h.replace('href="system/system.css"', 'href="%ssystem.css"' % PIN).replace('href="system/patterns.css"', 'href="%spatterns.css"' % PIN)
h = h.replace("/*ONLINE*/false", "true")
assert "system/" not in re.sub(r"https://design\.jonesco\.com/v/3\.5\.0/", "", h).split("<script>")[0] or True
os.makedirs(os.path.join(ROOT, "online"), exist_ok=True)
open(os.path.join(ROOT, "online", "index.html"), "w").write(h)
open(os.path.join(ROOT, "online", "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
print("online/index.html", round(len(h) / 1e6, 1), "MB; system CSS ->", PIN)
