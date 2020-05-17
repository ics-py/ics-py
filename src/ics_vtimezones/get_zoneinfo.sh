#!/usr/bin/env bash

set -ex

tmp_dir=$(mktemp -d)
git clone "https://github.com/libical/libical.git" "$tmp_dir"
rm "$tmp_dir/zoneinfo/CMakeLists.txt"
cp -a "$tmp_dir/zoneinfo" .
rm -rf "$tmp_dir"

tmp_dir=$(mktemp -d)
git clone "https://github.com/python-babel/babel.git" "$tmp_dir"
python3 "$tmp_dir/scripts/download_import_cldr.py"
python3 "$tmp_dir/scripts/import_cldr.py" -j "$tmp_dir/cldr/cldr-core-36/common"
jq -c ".windows_zone_mapping" "$tmp_dir/babel/global.dat.json" > "./windows_zone_mapping.json"
rm -rf "$tmp_dir"
