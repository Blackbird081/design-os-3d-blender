# Nodestack public story

Revision r01 publishes the project narrative and a sanitized manifest summary. It contains no Blender/STL/geometry archives, reference photographs or derived renders. The reference design is NODESTACK // SERVICE PACK by SMACKMAX_ (@SMACKMAX) on Printables; its redistribution license is unverified. The repository's software license does not establish reference-design rights.

Generate, never hand-edit the revision HTML:

```sh
python3 docs/reviews/nodestack/build-media.py --source "$PACKAGE" --out docs/reviews/nodestack/r01
python3 docs/reviews/nodestack/build-page.py --source "$PACKAGE" --out docs/reviews/nodestack/r01
```

`PACKAGE` is the delivered v16b print-test folder containing manifest.json. The public summary records its SHA-256 and configuration identity. The generator asserts the delivered status and part counts before creating the page. No source filesystem path is written to public output.

Digital checks and physical qualification are separate. The media narrative records an earlier E304 render source and does not claim the film proves v16b base geometry. Native-media or geometry publication requires verified rights and a new, explicit publication scope.
