#!/usr/bin/env python3
"""Enforce the owner-selected story-only publication scope."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert (a.source/'manifest.json').is_file()
a.out.mkdir(parents=True,exist_ok=True)
for f in a.out.rglob('*'):
    assert f.suffix.lower() not in {'.blend','.stl','.zip','.3mf','.glb','.mp4','.png','.jpg','.jpeg','.webp'}, f'Asset outside story-only scope: {f.name}'
(a.out/'media-manifest.json').write_text(json.dumps({'scope':'STORY_ONLY','files':[],'reason':'Geometry downloads held by owner; reference-design redistribution license unverified. Reference photographs and derived renders are not published.'},indent=2)+'\n')
print('PASS: story only; zero geometry, render or reference-image assets.')
