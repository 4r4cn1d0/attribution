import sys,time
p=f'/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-epic-ritchie-cc4188/1a199637-2a19-4fac-9cf2-8b00c9c1b5ff/tasks/{sys.argv[1]}.output'
t=time.time()
while time.time()-t<90:
    if sys.argv[2] in open(p).read(): break
    time.sleep(5)
print(open(p).read()[-2500:])
