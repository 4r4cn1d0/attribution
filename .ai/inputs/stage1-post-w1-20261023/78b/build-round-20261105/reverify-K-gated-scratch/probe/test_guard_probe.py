"""Re-verifier probe of the PP10 guard's reach, run under the kit's conftest loaded as a plugin (-p conftest). Local
calls only: getaddrinfo/gethostbyname on 'localhost' (/etc/hosts; no packet leaves), attribute checks, refusal texts.
Nothing reaches the network; nothing starts."""
import json, os, socket, subprocess
import conftest as c

R = {}


def rec(label, f):
    try:
        R[label] = "NOT refused: " + str(f())[:70]
    except c.NetworkOrProcessRefused as exc:
        R[label] = "refused: " + str(exc)[:80]
    except Exception as exc:  # noqa: BLE001
        R[label] = f"other {type(exc).__name__}: {str(exc)[:70]}"


def test_probe(tmp_path):
    rec("subprocess.run ssh", lambda: subprocess.run(["ssh", "-V"], capture_output=True))
    rec("Popen(args= keyword)", lambda: subprocess.Popen(args=["ssh", "-V"]))
    rec("socket.connect", lambda: socket.socket().connect(("203.0.113.9", 22)))
    rec("getaddrinfo(localhost)", lambda: socket.getaddrinfo("localhost", 80)[0][4])
    rec("gethostbyname(localhost)", lambda: socket.gethostbyname("localhost"))
    rec("socket.sendto patched (in class dict)", lambda: "sendto" in vars(socket.socket))
    rec("socket.sendall patched", lambda: "sendall" in vars(socket.socket))
    rec("os.posix_spawn refusal text", lambda: os.posix_spawn("/bin/true", ["true"], {}))
    rec("os.posix_spawnp refusal text", lambda: os.posix_spawnp("true", ["true"], {}))
    rec("os.execv patched", lambda: type(os.execv).__name__ != "builtin_function_or_method")
    rec("os.fork patched", lambda: type(os.fork).__name__ != "builtin_function_or_method")
    (tmp_path.parent / "guard-probe.json").write_text(json.dumps(R, indent=1))
    print(json.dumps(R, indent=1))
