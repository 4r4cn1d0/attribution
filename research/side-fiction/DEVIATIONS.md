# Fiction study: deviations from the frozen pre-registration

The frozen pre-registration is `PREREG-DRAFT.md` revision 4 (commit b33f4fe, SHA-256 `695090301b1a…`, recorded in FOCUS by the lead in 722d6c0). It is not edited after the freeze; deviations are recorded here, each before its result is read.

## 1. Seed light-1103 launched after the Gate B integration (recorded 2026-10-10T10:54Z, inserted by the shell)

- **Rule (§0, engine pin):** a fiction seed that cannot record its fixture before the integration "waits, and its engine handling is decided then and recorded as a deviation".
- **What happened:** the guard refused light-1103 at 09:44 UTC on 10 Oct (funds), and the lead integrated Gate B (engine X, 472fc7f6) at 10:13 UTC, before it launched. The other five fiction units recorded their fixtures on e49a978c before the integration.
- **Engine handling, decided now:** light-1103 runs its packed **e49a978c** bundle, like the rest of its arm. The only step that reads the main checkout after packing is record_first's `set-recipe`. Under engine X, `config_sha256(load_recipe(recipe-B mb4))` = `9e9bde6f…`, unchanged; the lead checked the same value independently, and the only config.py change adds a query-bank option that recipe B does not reach. Its plan was initialised before the integration (the reuse check passed on e49a978c); its MANIFEST `dbe1e4c5…` was unchanged.
- **Launch:** by the lead at 10:53:50 UTC on 10 Oct.
- **Effect on the analysis:** none expected; all six fiction units run on e49a978c. This is a timing deviation only, recorded before any fiction result was read.
