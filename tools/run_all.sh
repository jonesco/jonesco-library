#!/bin/zsh
cd ~/Developer/fonts-and-graphics-library
SRC="/Users/Wes/Developer/_Fonts and Graphics/Fonts Collection"
for d in "$SRC"/*/; do
  n=$(basename "$d"); 
  s=$(echo "$n" | tr -c 'A-Za-z0-9\n' '-' | tr 'A-Z' 'a-z')
  echo "== $n"; python3 -I tools/convert.py "$d" "fonts/$s" "data/$s.json" 2>&1 | tail -1
done
echo ALLDONE
