# Ohio shared textures

The accepted tile atlas and ground mist are preserved supplied exports. Their
current PNGs in [`src/assets/environments/ohio/shared/`](../../../../assets/environments/ohio/shared/) are the
authoritative artwork; the shared manifest records dimensions and hashes.

| Export | Accepted SHA-256 |
|---|---|
| `tileset.png` | `4c2afe5f03ef87b869cf8d88df536d8fa772438471da888220ff3b378b397e8d` |
| `mist.png` | `63fad0e9bf09499d6bec0f5b26b1c340b655ed77330f5946f816df2b00d98840` |

`ohio_materials_and_palettes.json` is retained source material. The historical procedural
Ohio generator and later refinement scripts are archived because running the
original generator does not reproduce these accepted textures. No exact
procedural rebuild is claimed. Keep the accepted PNGs when rebuilding unrelated
room art; changes to these textures require a reviewed replacement.

Historical code and restoration paths are indexed in
[`docs/maintenance/archive-manifest.json`](../../../../../docs/maintenance/archive-manifest.json).
