"""Transfer and launch the frozen per-host development schedule, without scientific changes."""
import pathlib,subprocess,sys,json
r=pathlib.Path(__file__).resolve().parent;h=sys.argv[1]
assert h in json.loads((r/'dev-matrix-assets/dev-matrix-plan.json').read_text())['assignments']
remote='/workspace/attribution-study-v2/'
if h=='lead':
 subprocess.run(['python3',str(r/'transfer.py'),'send',str(r/'dev-matrix-assets.tar.gz'),remote+'dev-matrix-assets.tar.gz'],check=True);prefix=['python3',str(r/'remote.py')]
else:
 subprocess.run(['python3',str(r/'pool_admin.py'),h,'send',str(r/'dev-matrix-assets.tar.gz'),remote+'dev-matrix-assets.tar.gz'],check=True);prefix=['python3',str(r/'pool_admin.py'),h,'ssh']
command="""cd /workspace/attribution-study-v2 && python3 - <<'REMOTE'
import pathlib,tarfile,hashlib,json
p=pathlib.Path('dev-matrix-assets.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='349668b7c3cab7843e31e4bb48e6206c7b6c0f2a4b074467439d0e93b9990048'
assert not pathlib.Path('dev-matrix-plan.json').exists()
with tarfile.open(p) as t:t.extractall('.',filter='data')
for n,h in json.loads(pathlib.Path('dev-matrix-assets-manifest.json').read_text()).items():assert hashlib.sha256(pathlib.Path(n).read_bytes()).hexdigest()==h,n
REMOTE
python3 process_receipt.py --out dev-matrix-outer-001 -- venv/bin/python run_dev_matrix.py """+h
subprocess.run([*prefix,command],check=True)
