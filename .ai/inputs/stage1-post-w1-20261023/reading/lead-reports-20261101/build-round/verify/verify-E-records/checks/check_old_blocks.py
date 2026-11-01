import re, sys
upd = open(sys.argv[1], encoding="utf-8").read()
plan = open(sys.argv[2], encoding="utf-8").read()
# find "Old:\n```\n...\n```"
blocks = re.findall(r"Old:\n```\n(.*?)\n```", upd, flags=re.S)
news = re.findall(r"New:\n```\n(.*?)\n```", upd, flags=re.S)
print("old blocks:", len(blocks), "new blocks:", len(news))
bad = 0
for i, b in enumerate(blocks, 1):
    ok = b in plan
    cnt = plan.count(b)
    if not ok:
        bad += 1
    print(i, "verbatim" if ok else "NOT FOUND", "count", cnt, repr(b[:70]))
sys.exit(1 if bad else 0)
