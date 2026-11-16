#!/bin/zsh
# Publishes the read-only online library to S3 behind CloudFront.
#   BUCKET=<bucket> [DIST_ID=<cloudfront id>] ./tools/deploy.sh [--dryrun]
# DIST_ID is only for a CloudFront setup; a plain S3 website does not need it.
# --dryrun lists what would change and uploads nothing. Run it first; --delete means a removed item disappears online too.
set -euo pipefail
: "${BUCKET:?set BUCKET}"; DIST_ID="${DIST_ID:-}"
DRY=""; [ "${1:-}" = "--dryrun" ] && DRY="--dryrun"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; BASE="/Users/Wes/Developer/_Fonts and Graphics"
cd "$ROOT"
.venv/bin/python tools/build_viewer.py >/dev/null && .venv/bin/python tools/build_online.py
S3="s3://$BUCKET"; CC="--cache-control public,max-age=86400"
for d in fonts thumbs previews icons; do aws s3 sync "$d" "$S3/$d" --delete $CC --exclude ".DS_Store" $DRY; done
# originals: only what the library shows, never the dropped collections or the junk beside them
for d in "Graphic Items" "Textures"; do
  aws s3 sync "$BASE/$d" "$S3/originals/$d" --delete $CC --exclude ".DS_Store" --exclude "*.db" --exclude "DE Catalog.pdf" $DRY
done
[ -d added ] && aws s3 sync added "$S3/originals/added" --delete $CC --exclude ".DS_Store" $DRY
aws s3 cp online/index.html "$S3/index.html" --cache-control "no-cache" --content-type "text/html; charset=utf-8" $DRY
aws s3 cp online/robots.txt "$S3/robots.txt" --content-type "text/plain" $DRY
[ -z "$DRY" ] && [ -n "$DIST_ID" ] && aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/index.html" "/robots.txt" >/dev/null && echo "published; invalidated /index.html"
echo "done ${DRY:+(dry run)}"
