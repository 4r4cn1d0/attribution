"""Administrative setup dispatch for an already-created, owned worker."""
import json,pathlib,subprocess,sys
r=pathlib.Path(__file__).resolve().parent;w=sys.argv[1]
def call(action,*args):subprocess.run(['python3',str(r/'pool_admin.py'),w,action,*args],check=True)
call('ssh','mkdir -p /workspace/attribution-study-v2')
call('send',str(r/'worker-setup-v3.tar.gz'),'/workspace/attribution-study-v2/worker-setup-v3.tar.gz')
call('ssh',"""cd /workspace/attribution-study-v2 && python3 - <<'REMOTE'
import pathlib,hashlib,tarfile
p=pathlib.Path('worker-setup-v3.tar.gz');assert hashlib.sha256(p.read_bytes()).hexdigest()=='4a73f5c41c80cd340fe3e9340018b502af01d059cfeee499b4ce4b31d9fa8151'
assert not pathlib.Path('worker-bootstrap-process-001').exists()
with tarfile.open(p) as t:t.extractall('.',filter='data')
REMOTE
python3 process_receipt.py --out worker-bootstrap-process-001 -- bash worker_bootstrap_v3.sh""")
