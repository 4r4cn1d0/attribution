"""Re-verifier demo (no network): a token value with an embedded newline reaches http.client's header check, whose
ValueError message holds the whole header value (the token); launch.http_get does not catch ValueError, so the exception
propagates with the token in its text. The token here is SYNTHETIC (hf_ + 34 letters, built in this script)."""
import http.client, io, sys, urllib.request, pathlib
sys.path.insert(0, sys.argv[1])            # ws-k/runkit/stage1-78b
TOKEN = "hf_" + "A" * 17 + "\n" + "B" * 16   # a 2-line value: .strip() leaves the inner newline
# 1. http.client alone: putrequest/putheader only buffer (no socket is opened before endheaders/send)
conn = http.client.HTTPConnection("203.0.113.9")        # TEST-NET-3; never connected
conn.putrequest("GET", "/api/whoami-v2")
try:
    conn.putheader("Authorization", "Bearer " + TOKEN)
    print("putheader accepted (no ValueError)")
except ValueError as exc:
    msg = str(exc)
    print("ValueError raised; message holds the token's first line:", "A" * 17 in msg, "; second line:", "B" * 16 in msg)
    print("message length", len(msg), "; starts with:", msg[:22])
assert conn.sock is None, "no socket was opened"
# 2. launch.http_get with the opener's open replaced by a raiser of that same ValueError (no network): does it propagate?
import launch
def fake_build_opener(*handlers):
    class O:
        def open(self, request, timeout=None):
            raise ValueError("Invalid header value %r" % request.get_header("Authorization"))
    return O()
urllib.request.build_opener = fake_build_opener
try:
    launch.http_get("https://huggingface.co/api/whoami-v2", TOKEN, None, 1)
    print("http_get returned (caught)")
except ValueError as exc:
    print("http_get let ValueError propagate; its text holds the token:", ("A" * 17) in str(exc))
# 3. the same for a non-latin-1 character in the token (UnicodeEncodeError, a ValueError subclass): message content
try:
    conn2 = http.client.HTTPConnection("203.0.113.9"); conn2.putrequest("GET", "/x")
    conn2.putheader("Authorization", "Bearer hf_" + "C" * 33 + "’")
    print("non-latin-1 accepted")
except UnicodeEncodeError as exc:
    print("UnicodeEncodeError:", str(exc)[:90], "| holds C*33:", "C" * 33 in str(exc))
print("token_checks/gated_precheck/main catch ValueError?", any("ValueError" in l for l in pathlib.Path(sys.argv[1], "launch.py").read_text().splitlines() if "except" in l))
