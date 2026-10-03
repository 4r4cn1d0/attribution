"""A small HTTPS client for the real connectors (stdlib ``urllib`` only).

What the connectors need and nothing more:

- **The secret stays in the environment.** The token is read from a named environment variable at
  each request and sent as ``Authorization: Bearer`` only to the configured service hosts. It is
  never stored on an object, logged, put in a URL or in an exception. A missing or empty variable
  raises ``NotConfigured``; so does a 401.
- **No credential on redirects.** Redirects are followed by hand (at most three) and *without* the
  Authorization header: GitHub answers an asset download with a redirect to a signed storage URL,
  which must not receive the token.
- **HTTPS only**, except for a loopback host (the tests' fake services on 127.0.0.1).
- **Bounded retries.** A rate-limit answer (429, or 403 with ``retry-after`` or
  ``x-ratelimit-remaining: 0``) waits for the stated time when that is within ``max_wait_seconds``
  and otherwise fails; a 5xx answer or a connection error backs off and retries. After
  ``max_retries`` the call raises ``TransferError``. Nothing retries forever: a blocked copy means
  no acknowledgement, and the dispatch gate then starts nothing.
- **Errors name the method, host, path and status only**: never a header, a query string or a body.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .common import NotConfigured, TransferError

__all__ = ["Http", "Reply", "next_link"]

_REDIRECTS = (301, 302, 303, 307, 308)
_TRANSIENT = (500, 502, 503, 504)
_LOOPBACK = ("127.0.0.1", "localhost", "::1")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Redirects are returned to the caller, which follows them without credentials."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102 - urllib hook
        return None


@dataclass(frozen=True)
class Reply:
    status: int
    headers: Mapping[str, str]
    body: bytes
    sha256: str | None = None      # of a streamed download
    size: int | None = None

    def json(self):
        try:
            return json.loads(self.body)
        except ValueError as exc:
            raise TransferError("the service answered with something that is not JSON") from exc


def next_link(headers: Mapping[str, str]) -> str | None:
    """The ``rel="next"`` URL of a ``Link`` header, or None."""
    for part in headers.get("link", "").split(","):
        url, _, rel = part.partition(";")
        if 'rel="next"' in rel:
            return url.strip().strip("<>")
    return None


class Http:
    """See the module doc. ``bases``: the service URL prefixes that receive the token.
    ``sleep`` and ``clock`` are injectable for tests."""

    def __init__(self, *, token_env: str, bases: Sequence[str], user_agent: str = "attribution-durability",
                 timeout: float = 60.0, max_retries: int = 4, max_wait_seconds: float = 120.0,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.time) -> None:
        self.token_env, self.bases = token_env, tuple(base.rstrip("/") for base in bases)
        self.user_agent, self.timeout = user_agent, timeout
        self.max_retries, self.max_wait_seconds, self.sleep, self.clock = max_retries, max_wait_seconds, sleep, clock
        self._opener = urllib.request.build_opener(_NoRedirect())
        for base in self.bases:
            self._check_url(base)

    def __repr__(self) -> str:
        return f"Http(token from ${self.token_env}, bases={list(self.bases)})"

    @staticmethod
    def _check_url(url: str) -> urllib.parse.SplitResult:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in _LOOPBACK):
            raise TransferError(f"refusing a request to a non-HTTPS address ({parts.scheme}://{parts.hostname})")
        return parts

    @staticmethod
    def _where(method: str, url: str) -> str:
        parts = urllib.parse.urlsplit(url)
        return f"{method} {parts.scheme}://{parts.netloc}{parts.path}"

    def _token(self) -> str:
        token = os.environ.get(self.token_env, "").strip()
        if not token:
            raise NotConfigured(f"the environment variable {self.token_env} is not set: this connector is not configured")
        return token

    def require_token(self) -> None:
        """Raise ``NotConfigured`` unless the token variable is set (nothing is sent)."""
        self._token()

    def _wait(self, status: int, headers: Mapping[str, str]) -> float | None:
        """Seconds a rate-limit answer asks to wait, or None when the answer is not a rate limit."""
        if status not in (403, 429):
            return None
        if headers.get("retry-after", "").strip().isdigit():
            return float(headers["retry-after"])
        if headers.get("x-ratelimit-remaining", "").strip() == "0" and headers.get("x-ratelimit-reset", "").strip().isdigit():
            return max(0.0, float(headers["x-ratelimit-reset"]) - self.clock())
        return 60.0 if status == 429 else None

    def request(self, method: str, url: str, *, headers: Mapping[str, str] | None = None,
                body: bytes | Path | None = None, sink: Path | None = None) -> Reply:
        """One request with the token, bounded retries and credential-free redirects. ``body``: bytes,
        or a file to stream. ``sink``: stream the answer to this file and return its hash and size.
        Returns every final answer that is not a rate limit, a 401 or an exhausted transient error;
        the caller judges the status."""
        self._token()   # fail closed before anything is sent
        authorized, hops, attempt, backoff = True, 0, 0, 1.0
        while True:
            self._check_url(url)
            send_token = authorized and any(url == base or url.startswith(base + "/") for base in self.bases)
            request = urllib.request.Request(url, method=method)
            request.add_header("User-Agent", self.user_agent)
            for name, value in (headers or {}).items():
                request.add_header(name, value)
            if send_token:
                request.add_header("Authorization", f"Bearer {self._token()}")
            handle = None
            if isinstance(body, Path):
                handle = open(body, "rb")  # noqa: SIM115 - closed below, reopened for every attempt
                request.data = handle
                request.add_header("Content-Length", str(body.stat().st_size))
            elif body is not None:
                request.data = body
                request.add_header("Content-Length", str(len(body)))
            try:
                with self._opener.open(request, timeout=self.timeout) as response:
                    status = response.status
                    reply_headers = {k.lower(): v for k, v in response.headers.items()}
                    if sink is not None and status == 200:
                        digest, size = hashlib.sha256(), 0
                        sink.parent.mkdir(parents=True, exist_ok=True)
                        with open(sink, "wb") as out:
                            for block in iter(lambda: response.read(1 << 20), b""):
                                out.write(block)
                                digest.update(block)
                                size += len(block)
                            out.flush()
                            os.fsync(out.fileno())
                        return Reply(status, reply_headers, b"", digest.hexdigest(), size)
                    return Reply(status, reply_headers, response.read())
            except urllib.error.HTTPError as exc:
                status, reply_headers = exc.code, {k.lower(): v for k, v in (exc.headers or {}).items()}
                payload = exc.read()
            except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
                attempt += 1
                if attempt > self.max_retries:
                    raise TransferError(f"{self._where(method, url)} failed after {attempt} attempts "
                                        f"({type(exc).__name__})") from None
                self.sleep(backoff)
                backoff = min(backoff * 2.0, 30.0)
                continue
            finally:
                if handle is not None:
                    handle.close()
            if status in _REDIRECTS and reply_headers.get("location"):
                hops += 1
                if hops > 3:
                    raise TransferError(f"{self._where(method, url)} redirected too many times")
                url, authorized = urllib.parse.urljoin(url, reply_headers["location"]), False
                continue
            if status == 401:
                raise NotConfigured(f"the token in {self.token_env} was rejected ({self._where(method, url)} -> 401)")
            wait = self._wait(status, reply_headers)
            if wait is not None:
                attempt += 1
                if wait > self.max_wait_seconds or attempt > self.max_retries:
                    raise TransferError(f"{self._where(method, url)} is rate limited (status {status}); the stated "
                                        f"wait of {wait:.0f} s is beyond the bound or the retries are used up")
                self.sleep(wait + 1.0)
                continue
            if status in _TRANSIENT:
                attempt += 1
                if attempt > self.max_retries:
                    raise TransferError(f"{self._where(method, url)} kept failing (status {status})")
                self.sleep(backoff)
                backoff = min(backoff * 2.0, 30.0)
                continue
            return Reply(status, reply_headers, payload)
