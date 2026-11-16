# Jonesco.library

A private library of fonts and graphics collected since college, with a viewer to browse, search and add to it. Personal use only: it holds licensed commercial fonts, so it is never public. Not a design system (that is design.jonesco.com) and not an app (see dev.jonesco.com); it is the raw material those draw from.

## The library
- **Fonts:** about 13,000 OpenType fonts, converted from classic Mac Type 1 and TrueType suitcases, in one flat `fonts/` folder.
- **Graphics:** about 3,700 EPS clip art, textures and images, with thumbnails (`thumbs/`) and large previews (`previews/`).
- **Viewer:** one page, `index.html`, built from `tools/viewer_template.html`. Jonesco system 3.5.0 (a copy in `system/` for offline use; online it links the pinned design.jonesco.com version). Light and dark mode.
- **Local mode** (opened through the launcher): Show in Finder, drag-and-drop adding of fonts, graphics and folders. There is no Remove button on purpose; removals are done deliberately with `tools/pipeline.remove()`.
- **Online mode** (library.jonesco.com): read-only; Download instead of Show in Finder. Preview locally with `index.html?online`.

## Layout
```
tools/          the code: converters, viewer template, launcher, deploy
Open Library.command   starts the local server and opens the viewer
fonts/ thumbs/ previews/ added/ data/   the collection and its state (not in git)
```

## Build and run
```
python3 -m venv .venv && .venv/bin/pip install fonttools pillow   # once; also needs fontforge and ghostscript (brew)
.venv/bin/python tools/build_viewer.py       # rebuild index.html from data/
./Open Library.command                       # local server on 127.0.0.1:8765
```
Rebuilding from the originals: `tools/run_all.sh` (fonts), `tools/thumbs.py`, `tools/previews.py`, `tools/classify.py` (graphics).

## Publishing
`BUCKET=… DIST_ID=… tools/deploy.sh --dryrun`, then without `--dryrun`. S3 behind CloudFront, with a login in front. Never publish without one.

## Non-goals
Not public. No accounts. Does not convert old Mac fonts dropped into the browser (browsers drop the resource fork); use `tools/convert.py` for those.
