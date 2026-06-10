# Al Munadi Linux Native (Rust spike)

Phase-one spike for the native Linux tray rewrite described in
[`shared/migration-plan.md`](../shared/migration-plan.md).

**Scope so far:** pure behavior core only — countdown/elapsed formatting, tray
label modes, iqama resolution, manual offsets, Jumuah notification keys,
version comparison, and Mawaqit slug extraction. No tray, GUI, or network code
yet.

The point of this crate is drift-prevention: `tests/fixtures.rs` asserts the
exact same cases from [`shared/fixtures/behavior-fixtures.json`](../shared/fixtures/behavior-fixtures.json)
that the Python suite (`AlMunadiWindows/test_al_munadi.py`) and the GNOME JS
suite (`tests/test_utils.js`) assert. If `cargo test` passes, the Rust core
behaves exactly like the shipping clients.

```bash
cd AlMunadiLinuxNative
cargo test
```

Next steps (per the migration plan): a StatusNotifier tray spike (`ksni`) on
KDE/XFCE/Cinnamon/MATE, then settings UI in GTK4/libadwaita — or a pivot to
Qt if the tray spike fails on older desktops. The Python tray app remains the
shipping Linux client until full feature parity.
