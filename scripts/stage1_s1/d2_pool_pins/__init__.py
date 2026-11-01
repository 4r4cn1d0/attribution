"""Post-W1 deviation D-2 (addendum section 19): REQ-3's pool pins filled after W1 without changing a W1 file.

``fill_pins.py`` writes the filled pins file from the W1 pins file (scripts/stage1/settings/representation_pools.json)
and REQ-8's sealed text-free record (plant_record.json): only pools.plant.sha256 and pools.decoy.sha256 change.
``d2_representation_pass.py`` loads the W1 file ``scripts/stage1/representation_pass.py`` by path after its SHA-256
check (against the W1 manifest's entry and this package's pinned settings) and runs its main() unchanged except that
the pins path and its SHA-256 are the filled file's, checked again against REQ-8's record first. Every W1 file stays
byte-identical.
"""
