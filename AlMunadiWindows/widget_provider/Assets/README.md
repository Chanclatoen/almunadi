# Widget icons

Drop the following PNGs in this folder before building the MSIX. The manifest
references them; without them, `MakeAppx` will fail.

| File | Size | Purpose |
|---|---|---|
| `StoreLogo.png` | 50 × 50 | Identity in the Store / Settings |
| `Square44x44Logo.png` | 44 × 44 | Widget host icon |
| `Square150x150Logo.png` | 150 × 150 | App tile |
| `Wide310x150Logo.png` | 310 × 150 | Wide tile (optional, can be a stretched copy) |
| `Screenshot-Small.png` | 300 × 304 | Preview in widget picker |
| `Screenshot-Medium.png` | 600 × 304 | Preview in widget picker |
| `Screenshot-Large.png` | 600 × 624 | Preview in widget picker |

For the first build you can copy the existing tray-icon PNG from
`AlMunadiWindows/` (resized) and screenshot the rendered widget once it is
running.
