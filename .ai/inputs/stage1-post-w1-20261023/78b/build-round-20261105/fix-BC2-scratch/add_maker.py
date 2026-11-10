

def test_anchor_records_skips_an_incomplete_or_foreign_record(tmp_path):
    """RV-2 (C-D3b): an anchor record is an anchors.sealed.json of kind "gate-c anchor bank record" with complete true;
    an incomplete record (complete false, missing, or not the boolean true), another kind or a non-object document is
    skipped, so no S_78 config can be anchored to it."""
    good = {"kind": mk.ANCHOR_RECORD_KIND, "complete": True, "anchor_file_sha256": TEST_ANCHORS,
            "provenance": {"recipe_sha256": mk.MAIN["olmo2-7b"]["config_sha256"]}}
    cases = {"complete": good, "incomplete": {**good, "complete": False},
             "unfinished": {k: v for k, v in good.items() if k != "complete"},
             "complete-as-a-string": {**good, "complete": "true"}, "foreign-kind": {**good, "kind": "gate-c anchor bank"},
             "a-list": [good]}
    for name, doc in cases.items():
        folder = tmp_path / name / "out"
        folder.mkdir(parents=True)
        (folder / "anchors.sealed.json").write_text(json.dumps(doc), encoding="utf-8")
    records = mk.anchor_records(tmp_path)
    assert [Path(r["path"]).parent.parent.name for r in records] == ["complete"]
    assert records[0]["anchor_file_sha256"] == TEST_ANCHORS and records[0]["recipe_sha256"] == mk.MAIN["olmo2-7b"]["config_sha256"]
    s78 = mk.make(load_main("olmo2-7b"), "olmo2-7b", TEST_ANCHORS)
    assert mk.anchored_to(s78, "olmo2-7b", records) == records[0]
    for name in cases:
        if name != "complete":
            assert mk.anchor_records(tmp_path / name) == [], name
            assert mk.anchored_to(s78, "olmo2-7b", mk.anchor_records(tmp_path / name)) is None, name
