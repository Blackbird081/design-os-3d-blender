#!/usr/bin/env python3
"""Build and optimize media assets for Nodestack review publication.

Enforces scope:
- r01: story-only, zero images (retained immutable).
- r02: 9 authorized native still images converted to metadata-stripped
  progressive JPEG q88. Video, geometry, and raw receipt paths withheld.
  Requires verified source inputs with pinned SHA-256 assertions.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path

# Relative specs with pinned expected source SHAs and verified blend SHAs
MEDIA_SPECS = [
    {
        'id': 'hero',
        'out_name': 'nodestack-hero.jpg',
        'rel_path': 'final-canonical-render-e304-v2/steps/hero/attempt-0001/0001.png',
        'orig_basename': '0001.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': '91fe5ee38ad9b383f5cbbcd04482d1ca22dcec53f179a8c6d1a1ea68499ffc6e',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'exact native render from E304 canonical studio setup'
    },
    {
        'id': 'drawer',
        'out_name': 'nodestack-drawer.jpg',
        'rel_path': 'final-native60-render-v3/steps/drawer/attempt-0001/0650.png',
        'orig_basename': '0650.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': 'd76e800966478da236f056f18279c405f1460b62504f2a201d54ec474a714426',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'native drawer stroke frame 0650 from E304 render suite'
    },
    {
        'id': 'canonical',
        'out_name': 'nodestack-canonical.jpg',
        'rel_path': 'final-native60-render-v3/steps/canonical/attempt-0001/1100.png',
        'orig_basename': '1100.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': 'be594143532dbebe1897a4979557dc649af231cd4d3c3a93859fcd7b30538e07',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'canonical 2x2 arrangement frame 1100 from E304 render suite'
    },
    {
        'id': 'tall',
        'out_name': 'nodestack-tall.jpg',
        'rel_path': 'final-native60-render-v3/steps/tall/attempt-0001/1350.png',
        'orig_basename': '1350.png',
        'source_version': 'E304-tall-derivation',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': '14e7acd754a319c1087354b79e857d231fe666863607b7b1454d0168896d2e70',
        'blend_source_sha256': '43ca2170252388e3bbda3220273735489099063a65e0dbc2875c2fa719ed2171',
        'provenance': 'tall 2x3 tower arrangement frame 1350 derived from E304 modular scene'
    },
    {
        'id': 'adjacent',
        'out_name': 'nodestack-adjacent.jpg',
        'rel_path': 'final-native60-render-v3/steps/adjacent/attempt-0001/1550.png',
        'orig_basename': '1550.png',
        'source_version': 'E304-adjacent-derivation',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': '750b798a9b63aff3bea8df7234bfa7a099a58f543e621ea2f0cf0b2eef6ccde3',
        'blend_source_sha256': '487fb427713cc4a3a9986ac470f6f97a36f5fe549729cc4383afe95f07babb15',
        'provenance': 'adjacent 4x2 arrangement frame 1550 derived from E304 modular scene'
    },
    {
        'id': 'blueprint',
        'out_name': 'nodestack-blueprint.jpg',
        'rel_path': 'additional-views-v4/blueprint-02/proof-0120.png',
        'orig_basename': 'proof-0120.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': 'de5e2979d8faff04a656ef827586a81e18aa12efcdff1cdd20bb280edcbf2c81',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'illustrative blueprint wireframe geometry view proof-0120'
    },
    {
        'id': 'exploded',
        'out_name': 'nodestack-exploded.jpg',
        'rel_path': 'additional-views-v4/exploded-02/proof-0180.png',
        'orig_basename': 'proof-0180.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': '77489c1e8d16808dba95d758222a2b19585bd53f578cad789c235290039eada0',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'illustrative exploded modular assembly view proof-0180'
    },
    {
        'id': 'catalog',
        'out_name': 'nodestack-catalog.jpg',
        'rel_path': 'additional-views-v4/catalog-02/proof-0240.png',
        'orig_basename': 'proof-0240.png',
        'source_version': 'E304',
        'expected_dim': (1920, 1080),
        'expected_src_sha256': '2005eeb2db4a91388ed4fdfd0270e027dffc20755aeabbbfdb8624e951286a88',
        'blend_source_sha256': 'e304e327b70a2eec93431ab5afe39a675b95282ad46689606324d60c1557a337',
        'provenance': 'canonical 32-part component catalog view proof-0240'
    },
]

def main():
    parser = argparse.ArgumentParser(description="Build and optimize media assets for Nodestack publication.")
    parser.add_argument('--source', type=Path, required=True, help="Delivered package root containing manifest.json")
    parser.add_argument('--out', type=Path, required=True, help="Output revision directory (e.g. docs/reviews/nodestack/r02)")
    parser.add_argument('--media-source', type=Path, default=None, help="Root directory for rendered native showcase stills")
    parser.add_argument('--selection', type=Path, default=None, help="Private asset selection JSON for receipts verification")
    args = parser.parse_args()

    assert (args.source / 'manifest.json').is_file(), f"Source package missing manifest.json: {args.source}"
    args.out.mkdir(parents=True, exist_ok=True)

    if args.out.name == 'r01':
        # Maintain immutable r01 story-only scope
        for f in args.out.rglob('*'):
            assert f.suffix.lower() not in {'.blend','.stl','.zip','.3mf','.glb','.mp4','.png','.jpg','.jpeg','.webp'}, f'Asset outside story-only scope: {f.name}'
        (args.out / 'media-manifest.json').write_text(json.dumps({
            'scope': 'STORY_ONLY',
            'files': [],
            'reason': 'Geometry downloads held by owner; reference-design redistribution license unverified. Reference photographs and derived renders are not published.'
        }, indent=2) + '\n')
        print('PASS: story only; zero geometry, render or reference-image assets for r01.')
        return

    assert args.media_source is not None, "--media-source required for r02 media build"
    assert args.media_source.is_dir(), f"Media source directory does not exist: {args.media_source}"

    # If selection file provided, verify first 5 receipts match
    if args.selection is not None:
        assert args.selection.is_file(), f"Selection file not found: {args.selection}"
        selection_data = json.loads(args.selection.read_text())
        selection_by_name = {item['name']: item for item in selection_data}
        for s in MEDIA_SPECS[:5]:
            sel = selection_by_name.get(s['id'])
            assert sel is not None, f"Spec {s['id']} missing from selection JSON"
            assert sel['sha256'] == s['expected_src_sha256'], f"Selection SHA mismatch for {s['id']}: {sel['sha256']} != {s['expected_src_sha256']}"

    manifest_entries = []
    total_bytes = 0

    # 1. Process 8 showcase render stills
    for spec in MEDIA_SPECS:
        src = args.media_source / spec['rel_path']
        assert src.is_file(), f"Source still missing: {src}"
        src_bytes = src.read_bytes()
        actual_src_sha = hashlib.sha256(src_bytes).hexdigest()
        assert actual_src_sha == spec['expected_src_sha256'], f"Source SHA256 mismatch for {spec['out_name']}: actual {actual_src_sha} != expected {spec['expected_src_sha256']}"

        out_file = args.out / spec['out_name']
        cmd = [
            '/opt/homebrew/bin/magick',
            str(src),
            '-strip',
            '-interlace', 'Plane',
            '-quality', '88',
            str(out_file)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"ImageMagick conversion failed for {spec['out_name']}: {res.stderr}"

        out_data = out_file.read_bytes()
        out_sha256 = hashlib.sha256(out_data).hexdigest()
        file_size = len(out_data)
        total_bytes += file_size

        dim_res = subprocess.run(['/opt/homebrew/bin/magick', 'identify', '-format', '%w %h', str(out_file)], capture_output=True, text=True)
        w, h = map(int, dim_res.stdout.strip().split())
        assert (w, h) == spec['expected_dim'], f"Dimension mismatch for {spec['out_name']}: {w}x{h} vs expected {spec['expected_dim']}"

        manifest_entries.append({
            'name': spec['out_name'],
            'original_basename': spec['orig_basename'],
            'source_version': spec['source_version'],
            'source_sha256': actual_src_sha,
            'output_sha256': out_sha256,
            'blend_source_sha256': spec['blend_source_sha256'],
            'provenance': spec['provenance'],
            'width': w,
            'height': h,
            'bytes': file_size,
        })
        print(f"Processed {spec['out_name']}: {w}x{h}, {file_size/1024:.1f} KB, sha256={out_sha256[:12]}...")

    # 2. Process technical engineering image from delivered package
    eng_src = args.source / 'images/nodestack-v16b-base-before-after.png'
    assert eng_src.is_file(), f"Engineering section image missing in package: {eng_src}"
    eng_bytes = eng_src.read_bytes()
    actual_eng_sha = hashlib.sha256(eng_bytes).hexdigest()
    expected_eng_sha = '078a59ab856c53957bfefa85a0725b34c5eb06e2d27b88eec51d49e61cccd999'
    assert actual_eng_sha == expected_eng_sha, f"Engineering image SHA mismatch: {actual_eng_sha} != {expected_eng_sha}"

    eng_out = args.out / 'nodestack-v16b-base-before-after.jpg'
    cmd = [
        '/opt/homebrew/bin/magick',
        str(eng_src),
        '-strip',
        '-interlace', 'Plane',
        '-quality', '88',
        str(eng_out)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"ImageMagick failed for engineering image: {res.stderr}"

    eng_data = eng_out.read_bytes()
    eng_out_sha = hashlib.sha256(eng_data).hexdigest()
    eng_size = len(eng_data)
    total_bytes += eng_size

    dim_res = subprocess.run(['/opt/homebrew/bin/magick', 'identify', '-format', '%w %h', str(eng_out)], capture_output=True, text=True)
    ew, eh = map(int, dim_res.stdout.strip().split())
    assert (ew, eh) == (1400, 800), f"Dimension mismatch for engineering image: {ew}x{eh} vs (1400, 800)"

    manifest_entries.append({
        'name': 'nodestack-v16b-base-before-after.jpg',
        'original_basename': 'nodestack-v16b-base-before-after.png',
        'source_version': 'v16b-print-test',
        'source_sha256': actual_eng_sha,
        'output_sha256': eng_out_sha,
        'blend_source_sha256': None,
        'provenance': 'technical section rendering from delivered v16b package comparing E304 and v16b seating profiles',
        'width': ew,
        'height': eh,
        'bytes': eng_size,
    })
    print(f"Processed nodestack-v16b-base-before-after.jpg: {ew}x{eh}, {eng_size/1024:.1f} KB, sha256={eng_out_sha[:12]}...")

    # Strict assertion against forbidden formats
    for f in args.out.rglob('*'):
        assert f.suffix.lower() not in {'.blend', '.stl', '.zip', '.3mf', '.glb', '.mp4'}, f"Forbidden asset found in output: {f.name}"

    assert total_bytes < 25 * 1024 * 1024, f"Media budget exceeded: {total_bytes / (1024*1024):.2f} MB > 25 MB"

    manifest_doc = {
        'revision': 'r02',
        'scope': 'NATIVE_STILL_IMAGES_AND_TECHNICAL_COMPARISON',
        'media_budget_bytes_limit': 26214400,
        'total_bytes': total_bytes,
        'image_count': len(manifest_entries),
        'policy': {
            'format': 'progressive JPEG q88 metadata-stripped',
            'video': 'WITHHELD',
            'geometry_downloads': 'WITHHELD — reference-design redistribution license unverified',
            'reference': {
                'creator': 'SMACKMAX_ (@SMACKMAX)',
                'title': 'NODESTACK // SERVICE PACK',
                'url': 'https://www.printables.com/model/1837797-nodestack-service-pack',
                'redistribution_license': 'UNVERIFIED'
            }
        },
        'images': manifest_entries
    }

    (args.out / 'media-manifest.json').write_text(json.dumps(manifest_doc, indent=2) + '\n')
    print(f"PASS: r02 media built successfully. Total images: {len(manifest_entries)}, total size: {total_bytes/1024:.1f} KB (< 25 MB).")

if __name__ == '__main__':
    main()
