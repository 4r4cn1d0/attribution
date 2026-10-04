"""A fake RunPod API on 127.0.0.1 for the provider and watchdog tests (ENGINEERING FIXTURE): the REST
lists of pods and network volumes, one pod by id, the stop of a pod (REST, and the GraphQL
``podStop`` mutation), and the GraphQL account query,
with the field names RunPod documents. It records every request so the tests can show that the
provider only reads and that the watchdog only reads and stops. ``stop_mode``: "ok" (the pod
becomes EXITED), "ignored" (answered 200, nothing changes), "error" (500) or "forbidden" (403);
``read_mode`` "error" makes the read of one pod fail. It is not RunPod and proves nothing about
RunPod's real answers."""

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
        self.stop_mode = "ok"
        self.gpu_types: list = [{"id": "NVIDIA A100-SXM4-80GB", "securePrice": 1.59, "communityPrice": 1.39}]
        self.created_cost: float | None = None         # the price a created pod reports (default: the secure price)
        self.create_status = 201
        self._ids = 0
        self.read_mode = "ok"                          # "error": a pod read by id answers 500
        self.foreign: list[str] = []                   # other services' secrets, which must never arrive here
        self.leaks: list[str] = []
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()

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
                if KEY in self.path or KEY in body or any(secret in self.path + str(self.headers) + body
                                                          for secret in fake.foreign):
                    fake.leaks.append(f"a secret was sent where it does not belong: {method} {self.path.split('?')[0]}")
                if self.headers.get("Authorization") != f"Bearer {KEY}":
                    return self._send(401, {"error": "unauthorized"})
                path = self.path.split("?")[0]
                if path.startswith("/v1/pods/"):
                    name, _, action = path[len("/v1/pods/"):].partition("/")
                    found = [p for p in fake.pods if isinstance(p, dict) and p.get("id") == name] \
                        if isinstance(fake.pods, list) else []
                    if not found:
                        return self._send(404, {"error": "pod not found"})
                    if method == "GET" and not action:
                        if fake.read_mode == "error":
                            return self._send(500, {"error": "ENGINEERING FIXTURE fault"})
                        return self._send(200, found[0])
                    if method == "POST" and action == "stop":
                        if fake.stop_mode == "error":
                            return self._send(500, {"error": "ENGINEERING FIXTURE fault"})
                        if fake.stop_mode == "forbidden":
                            return self._send(403, {"error": "forbidden"})
                        if fake.stop_mode == "ok":
                            found[0]["desiredStatus"] = "EXITED"
                        return self._send(200, found[0])
                    return self._send(404, {"error": "not found"})
                if method == "GET" and path == "/v1/pods":
                    return self._send(200, fake.pods)
                if method == "POST" and path == "/v1/networkvolumes":
                    wanted = json.loads(body)
                    fake._ids += 1
                    volume = {"id": f"vol-new-{fake._ids}", "name": wanted["name"], "size": wanted["size"],
                              "dataCenterId": wanted["dataCenterId"]}
                    fake.volumes.append(volume)
                    return self._send(200, volume)
                if method == "POST" and path == "/v1/pods":
                    if fake.create_status != 201:
                        return self._send(fake.create_status, {"error": "ENGINEERING FIXTURE: no instances available"})
                    wanted = json.loads(body)
                    fake._ids += 1
                    cost = fake.created_cost if fake.created_cost is not None else fake.gpu_types[0]["securePrice"]
                    made = {"id": f"pod-new-{fake._ids}", "name": wanted["name"], "desiredStatus": "RUNNING",
                            "costPerHr": cost, "adjustedCostPerHr": cost, "image": wanted["imageName"],
                            "env": wanted["env"], "containerDiskInGb": wanted["containerDiskInGb"], "volumeInGb": 0,
                            "volumeMountPath": wanted["volumeMountPath"],
                            "networkVolume": next((v for v in fake.volumes if v["id"] == wanted.get("networkVolumeId")), None)}
                    fake.pods.append(made)
                    return self._send(201, made)
                if method == "POST" and path == "/graphql" and "gpuTypes" in body:
                    return self._send(200, {"data": {"gpuTypes": fake.gpu_types}})
                if method == "GET" and path == "/v1/networkvolumes":
                    return self._send(200, fake.volumes)
                if method == "POST" and path == "/graphql" and "podStop" in body:      # the stop mutation
                    named = [p for p in fake.pods if isinstance(p, dict) and '\\"%s\\"' % p.get("id") in body] \
                        if isinstance(fake.pods, list) else []
                    if fake.stop_mode in ("error", "forbidden") or not named:
                        return self._send(200, {"errors": [{"message": "ENGINEERING FIXTURE fault"}]})
                    if fake.stop_mode == "ok":
                        named[0]["desiredStatus"] = "EXITED"
                    return self._send(200, {"data": {"podStop": {"id": named[0]["id"],
                                                                 "desiredStatus": named[0]["desiredStatus"]}}})
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
