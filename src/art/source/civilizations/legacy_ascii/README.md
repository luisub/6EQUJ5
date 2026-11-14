# Legacy portrait rebuild sources

The historical before/after comparison builder reads its original ASCII-era
portraits from this directory. These originals are currently missing; the
builder must continue reporting that missing source instead of substituting
the modern artwork. The installed game does not need these inputs.

Required originals:

| Civilization | Preferred filename | Accepted historical filename |
|---|---|---|
| FASR-001 | `fasr-001_face.png` | `fasr-001_legacy_face.png` |
| FASR-005 | `fasr-005_face.png` | `fasr-005_legacy_face.png` |
| FASR-009 | `fasr-009_face.png` | `fasr-009_legacy_face.png` |

If an original is recovered, verify its provenance before placing it here.
Keep recovery archives in `_trash/`; active rebuild inputs belong here.
`video_game.tools.build_assets.LEGACY_SOURCE_DIR` is the default source owner.
Callers testing a different source set can still pass `legacy_dir` explicitly.
