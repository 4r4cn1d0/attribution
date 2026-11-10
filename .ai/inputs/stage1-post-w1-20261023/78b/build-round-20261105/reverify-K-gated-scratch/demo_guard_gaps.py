"""Re-verifier demo of the PP10 guard's reach, by driving conftest.pp10_guard with pytest.MonkeyPatch outside pytest.
Only local calls: getaddrinfo on 'localhost' (resolved from /etc/hosts, no packet leaves), a UDP socket to a TEST-NET
address created but NOT sent to, os.posix_spawn's refusal text. Nothing reaches the network."""
import importlib.util, os, socket, subprocess, sys, pytest
spec = importlib.util.spec_from_file_location("kit_conftest", sys.argv[1])
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
mp = pytest.MonkeyPatch()
gen = c.pp10_guard(mp); allowed = next(gen)
def tryit(label, f):
    try:
        r = f(); print(f"{label}: NOT refused -> {str(r)[:60]}")
    except c.NetworkOrProcessRefused as exc:
        print(f"{label}: refused -> {str(exc)[:75]}")
    except Exception as exc:
        print(f"{label}: other {type(exc).__name__}: {str(exc)[:60]}")
tryit("subprocess.run ssh", lambda: subprocess.run(["ssh", "-V"], capture_output=True))
tryit("socket.connect", lambda: socket.socket().connect(("203.0.113.9", 22)))
tryit("getaddrinfo(localhost)", lambda: socket.getaddrinfo("localhost", 80)[0][4])
tryit("gethostbyname(localhost)", lambda: socket.gethostbyname("localhost"))
tryit("udp sendto patched?", lambda: socket.socket.sendto is not socket._socket.socket.sendto)   # False = not patched
tryit("os.posix_spawn name", lambda: os.posix_spawn("/bin/true", ["true"], {}))
tryit("os.posix_spawnp name", lambda: os.posix_spawnp("true", ["true"], {}))
tryit("os.execv patched?", lambda: os.execv is not os.__dict__.get("execv"))
tryit("Popen(args=kw)", lambda: subprocess.Popen(args=["ssh", "-V"]))
mp.undo()
try:
    next(gen)
except StopIteration:
    pass
print("undone: subprocess.Popen.__init__ restored:", subprocess.Popen.__init__.__name__)
