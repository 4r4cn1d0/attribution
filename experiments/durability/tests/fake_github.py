"""A fake GitHub REST API on 127.0.0.1 for the connector tests (ENGINEERING FIXTURE). It implements
only what ``GitHubReleaseDestination`` uses, with the documented behaviours the connector relies on:
create-only asset names (422 on a duplicate), a tag that cannot be created twice, pagination with
``Link`` headers, binary downloads through a redirect, asset states, and scripted faults (a 502 that
leaves a ``starter`` asset, rate-limit answers, stored bytes that differ from what was sent). It is
not GitHub and proves nothing about GitHub's real behaviour."""

from __future__ import annotations

import hashlib
import json
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = "fake-token-0123456789-never-a-real-credential"


class FakeGitHub:
    """State and scripted faults. ``faults``: a list of dicts consumed in order by the first matching
    request, each ``{"on": "upload"|"any"|"download"|"list", "status": int, "headers": {...},
    "starter": bool}``. ``corrupt``/``truncate``: upload ordinals (1-based) whose stored bytes are
    altered. ``page``: the server's page size cap."""

    def __init__(self, repository: str = "owner/backups", page: int = 100, digests: bool = True) -> None:
        self.repository, self.page, self.digests = repository, page, digests
        self.releases: dict[int, dict] = {}
        self.assets: dict[int, dict] = {}
        self.blobs: dict[int, bytes] = {}
        self.faults: list[dict] = []
        self.corrupt: set[int] = set()
        self.truncate: set[int] = set()
        self.uploads = 0
        self.log: list[tuple[str, str, bool]] = []     # (method, path with query, had an Authorization header)
        self.leaks: list[str] = []                     # requests that carried the token where they must not
        self.mangle_labels = False
        self._ids = 1000
        self._lock = threading.RLock()
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def _next(self) -> int:
        self._ids += 1
        return self._ids

    def names(self, state: str = "uploaded") -> list[str]:
        """The labels (keys) of every asset in a state, sorted."""
        with self._lock:
            return sorted(a["label"] for a in self.assets.values() if a["state"] == state)

    def asset_json(self, asset: dict) -> dict:
        label = asset["label"][::-1] if self.mangle_labels else asset["label"]
        return {"id": asset["id"], "name": asset["name"], "label": label, "state": asset["state"],
                "size": asset["size"], "digest": asset["digest"] if self.digests else None,
                "url": f"{self.url}/repos/{self.repository}/releases/assets/{asset['id']}"}

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):  # noqa: D102 - silence the test server
                return

            def _send(self, status: int, body=None, headers=None) -> None:
                data = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
                self.send_response(status)
                for name, value in (headers or {}).items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _fault(self, kind: str) -> bool:
                with fake._lock:
                    for fault in fake.faults:
                        if fault["on"] in (kind, "any"):
                            fake.faults.remove(fault)
                            self._send(fault["status"], {"message": "ENGINEERING FIXTURE fault"}, fault.get("headers"))
                            return True
                return False

            def _route(self, method: str) -> None:
                parts = urllib.parse.urlsplit(self.path)
                query = urllib.parse.parse_qs(parts.query)
                authorized = self.headers.get("Authorization") == f"Bearer {TOKEN}"
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                with fake._lock:
                    fake.log.append((method, self.path, "Authorization" in self.headers))
                    if TOKEN in self.path:
                        fake.leaks.append(f"token in a URL: {method} {parts.path}")
                path = parts.path
                if path.startswith("/_blob/"):                         # the signed storage URL of a download
                    if "Authorization" in self.headers:
                        fake.leaks.append("the token was forwarded on a redirect")
                    return self._send(200, fake.blobs[int(path.rsplit("/", 1)[1])],
                                      {"Content-Type": "application/octet-stream"})
                if not authorized:
                    return self._send(401, {"message": "Bad credentials"})
                base = f"/repos/{fake.repository}"
                if not path.startswith(base):
                    return self._send(404, {"message": "Not Found"})
                rest = path[len(base):]
                if method == "GET" and (m := re.fullmatch(r"/releases/tags/(.+)", rest)):
                    if self._fault("any"):
                        return None
                    found = [r for r in fake.releases.values() if r["tag_name"] == m.group(1)]
                    return self._send(200, found[0]) if found else self._send(404, {"message": "Not Found"})
                if method == "POST" and rest == "/releases":
                    spec = json.loads(body)
                    with fake._lock:
                        if any(r["tag_name"] == spec["tag_name"] for r in fake.releases.values()):
                            return self._send(422, {"message": "Validation Failed", "errors": [{"code": "already_exists"}]})
                        release = {"id": fake._next(), "tag_name": spec["tag_name"], "name": spec.get("name"),
                                   "draft": spec.get("draft", False), "prerelease": spec.get("prerelease", False)}
                        fake.releases[release["id"]] = release
                    return self._send(201, release)
                if method == "GET" and rest == "/releases":
                    if self._fault("list"):
                        return None
                    return self._page(sorted(fake.releases.values(), key=lambda r: r["id"]), query, path)
                if method == "GET" and (m := re.fullmatch(r"/releases/(\d+)/assets", rest)):
                    if self._fault("list"):
                        return None
                    release_id = int(m.group(1))
                    with fake._lock:
                        items = [fake.asset_json(a) for a in sorted(fake.assets.values(), key=lambda a: a["id"])
                                 if a["release"] == release_id]
                    return self._page(items, query, path)
                if method == "POST" and (m := re.fullmatch(r"/releases/(\d+)/assets", rest)):
                    return self._upload(int(m.group(1)), query, body)
                if (m := re.fullmatch(r"/releases/assets/(\d+)", rest)):
                    asset_id = int(m.group(1))
                    with fake._lock:
                        asset = fake.assets.get(asset_id)
                    if asset is None:
                        return self._send(404, {"message": "Not Found"})
                    if method == "DELETE":
                        with fake._lock:
                            fake.assets.pop(asset_id, None)
                            fake.blobs.pop(asset_id, None)
                        return self._send(204)
                    if method == "GET" and self.headers.get("Accept") == "application/octet-stream":
                        if self._fault("download"):
                            return None
                        return self._send(302, None, {"Location": f"{fake.url}/_blob/{asset_id}"})
                    if method == "GET":
                        return self._send(200, fake.asset_json(asset))
                return self._send(404, {"message": "Not Found"})

            def _page(self, items: list, query: dict, path: str) -> None:
                size = min(int(query.get("per_page", ["30"])[0]), fake.page)
                page = int(query.get("page", ["1"])[0])
                chunk = items[(page - 1) * size:page * size]
                headers = {}
                if page * size < len(items):
                    headers["Link"] = f'<{fake.url}{path}?per_page={size}&page={page + 1}>; rel="next"'
                self._send(200, chunk, headers)

            def _upload(self, release_id: int, query: dict, body: bytes) -> None:
                name, label = query["name"][0], query.get("label", [None])[0]
                with fake._lock:
                    if release_id not in fake.releases:
                        return self._send(404, {"message": "Not Found"})
                    if any(a["release"] == release_id and a["name"] == name for a in fake.assets.values()):
                        return self._send(422, {"message": "Validation Failed", "errors": [{"code": "already_exists"}]})
                    for fault in fake.faults:
                        if fault["on"] in ("upload", "any"):
                            fake.faults.remove(fault)
                            if fault.get("starter"):
                                asset_id = fake._next()
                                fake.assets[asset_id] = {"id": asset_id, "release": release_id, "name": name,
                                                         "label": label, "state": "starter", "size": 0, "digest": None}
                                fake.blobs[asset_id] = b""
                            return self._send(fault["status"], {"message": "ENGINEERING FIXTURE fault"},
                                              fault.get("headers"))
                    fake.uploads += 1
                    stored = body
                    if fake.uploads in fake.truncate:
                        stored = body[:-1]
                    if fake.uploads in fake.corrupt:
                        stored = bytes([body[0] ^ 0xFF]) + body[1:]
                    asset_id = fake._next()
                    # what GitHub reports describes what it received; the stored bytes are the fault
                    fake.assets[asset_id] = {"id": asset_id, "release": release_id, "name": name, "label": label,
                                             "state": "uploaded", "size": len(body),
                                             "digest": "sha256:" + hashlib.sha256(body).hexdigest()}
                    fake.blobs[asset_id] = stored
                    return self._send(201, fake.asset_json(fake.assets[asset_id]))

            def do_GET(self):  # noqa: N802,D102
                self._route("GET")

            def do_POST(self):  # noqa: N802,D102
                self._route("POST")

            def do_DELETE(self):  # noqa: N802,D102
                self._route("DELETE")

            def do_PATCH(self):  # noqa: N802,D102
                self._route("PATCH")

        return Handler
