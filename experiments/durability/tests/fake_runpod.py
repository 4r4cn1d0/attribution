"""A fake RunPod API on 127.0.0.1 for the provider tests (ENGINEERING FIXTURE): the REST lists of
pods and network volumes and the GraphQL account query, with the field names RunPod documents. It
records every request so the tests can show that the provider only reads. It is not RunPod and
proves nothing about RunPod's real answers."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = "fake-runpod-key-0123456789-never-a-real-credential"


def pod(pod_id: str, *, status: str = "RUNNING", cost: float = 1.6, volume: dict | None = None,
        mount: str | None = "/workspace", container_gb: int = 20, volume_gb: int = 0, **more) -> dict:
    return {"id": pod_id, "name": f"pod-{pod_id}", "desiredStatus": status, "costPerHr": cost,
            "adjustedCostPerHr": cost, "containerDiskInGb": container_gb, "volumeInGb": volume_gb,
            "volumeMountPath": mount, "networkVolume": volume, **more}


def network_volume(volume_id: str, size: int = 100) -> dict:
    return {"id": volume_id, "name": f"volume-{volume_id}", "size": size, "dataCenterId": "EU-FIXTURE-1"}


class FakeRunPod:
    def __init__(self) -> None:
        self.pods: object = []
        self.volumes: object = []
        self.myself: object = {"clientBalance": 100.0, "currentSpendPerHr": 0.0, "spendLimit": 80}
        self.graphql_errors = None
        self.log: list[tuple[str, str, str]] = []      # (method, path, body)
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):  # noqa: D102
                return

            def _send(self, status: int, body) -> None:
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _route(self, method: str) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length).decode() if length else ""
                fake.log.append((method, self.path, body))
                if self.headers.get("Authorization") != f"Bearer {KEY}":
                    return self._send(401, {"error": "unauthorized"})
                path = self.path.split("?")[0]
                if method == "GET" and path == "/v1/pods":
                    return self._send(200, fake.pods)
                if method == "GET" and path == "/v1/networkvolumes":
                    return self._send(200, fake.volumes)
                if method == "POST" and path == "/graphql":
                    answer = {"data": {"myself": fake.myself}}
                    if fake.graphql_errors:
                        answer = {"errors": fake.graphql_errors}
                    return self._send(200, answer)
                return self._send(404, {"error": "not found"})

            def do_GET(self):  # noqa: N802,D102
                self._route("GET")

            def do_POST(self):  # noqa: N802,D102
                self._route("POST")

            def do_DELETE(self):  # noqa: N802,D102
                self._route("DELETE")

            def do_PATCH(self):  # noqa: N802,D102
                self._route("PATCH")

        return Handler
