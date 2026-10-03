"""The off-pod destination on GitHub release assets (stdlib only).

``GitHubReleaseDestination`` implements the ``Destination`` contract on the release assets of one
private repository. It relies only on behaviour GitHub documents (REST "release assets" and
"releases"; checked 3 October 2026, links in the README):

- **An object is one asset.** Its name is the SHA-256 of its key (asset names with other
  characters are renamed by GitHub, and keys contain ``/``); its label is the key itself, which is
  what makes listing by prefix possible. A listed asset whose label does not hash to its name is
  refused: the listing is not trusted.
- **Shards.** A release holds at most 1000 assets, so a key goes to the release
  ``<scheme>-<shard>``, the shard being a hash of the key modulo ``shards``. Releases are created
  on first use; creating a tag that exists is refused by GitHub, so two writers cannot make two
  releases for one shard. A full shard raises ``CapacityError`` before anything is uploaded.
- **Create-only.** Uploading a name that already exists in a release is refused (422). That is
  the exclusivity ``commit`` and ``put_new`` need: a final object is created by one upload, an
  existing identical object is reused, an existing different object is a ``CollisionError`` and is
  never replaced. Nothing here deletes a final object.
- **Staging.** ``upload`` writes a staging asset (replaced if the name exists). ``sha256`` downloads
  the asset from GitHub and hashes those bytes; the read-back copy is kept in a local cache so that
  ``commit`` publishes exactly the bytes that were read back, as a new create-only upload under
  the final name, checked against the size and digest GitHub reports. The staging asset is then
  deleted. (A server-side rename would save the second upload, but what GitHub does when the new
  name exists is not documented; see the README.)
- **Torn uploads.** GitHub documents that a failed upload "may leave an empty asset with a state of
  starter" that "can be safely deleted". An asset whose state is not ``uploaded`` is never an
  object; when it occupies a needed name it is deleted and the upload is repeated once.
- **Limits.** A file of 2 GiB or more is refused before any upload. GitHub reports no free space:
  ``free_bytes`` returns the declared cap given at construction. Requests are rate limited by
  GitHub (README); the transport waits within its bound and then fails.

**Single writer per namespace.** The asset index of a release is read once per process and kept
current with this process's own writes. Another writer of the *same* keys is not supported (the
vault's rule already); exclusivity itself never depends on the index, only on GitHub's 422.

**The token** comes from the environment variable named at construction (default
``ATTRIBUTION_BACKUP_GITHUB_TOKEN``) and is handled only by ``transport.Http``. Without it every
call raises ``NotConfigured``. ``describe()`` names the repository and the release scheme, nothing
else. A token that can write can also delete: this destination protects evidence against a lost
worker and an exhausted GPU account, not against a compromised token (README, threat model).
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import urllib.parse
from pathlib import Path
from typing import Callable

from .common import CapacityError, CollisionError, TransferError, relative_name, sha256_bytes, token
from .destination import STAGING, Destination, is_staging
from .transport import Http, next_link

__all__ = ["GitHubReleaseDestination", "GITHUB_TOKEN_ENV", "MAX_ASSET_BYTES", "MAX_ASSETS_PER_RELEASE"]

GITHUB_TOKEN_ENV = "ATTRIBUTION_BACKUP_GITHUB_TOKEN"
MAX_ASSET_BYTES = 2 * 1024 ** 3          # "each file must be under 2 GiB"
MAX_ASSETS_PER_RELEASE = 1000
_REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}")
_SCHEME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
_JSON = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
_BINARY = {"Accept": "application/octet-stream", "X-GitHub-Api-Version": "2022-11-28"}


class GitHubReleaseDestination(Destination):
    """See the module doc. ``declared_free_bytes``: the capacity the operator declares (GitHub
    reports none). ``shards`` and ``assets_per_release`` fix the layout of a scheme and must not
    change once objects exist under it. ``cache_dir``: where read-back copies of staging assets are
    kept until their commit (a private temporary folder by default)."""

    def __init__(self, repository: str, *, declared_free_bytes: int, scheme: str = "durability-v1", shards: int = 64,
                 assets_per_release: int = MAX_ASSETS_PER_RELEASE, max_file_bytes: int = MAX_ASSET_BYTES,
                 token_env: str = GITHUB_TOKEN_ENV, api_url: str = "https://api.github.com",
                 upload_url: str = "https://uploads.github.com", cache_dir: str | Path | None = None,
                 max_retries: int = 4, max_wait_seconds: float = 120.0,
                 sleep: Callable[[float], None] | None = None) -> None:
        if not _REPOSITORY.fullmatch(repository):
            raise TransferError(f"{repository!r} is not an owner/name repository")
        if not _SCHEME.fullmatch(scheme):
            raise TransferError(f"the release scheme {scheme!r} must match {_SCHEME.pattern}")
        if not (isinstance(shards, int) and 1 <= shards <= 10000):
            raise TransferError("shards must be between 1 and 10000")
        if not (isinstance(assets_per_release, int) and 1 <= assets_per_release <= MAX_ASSETS_PER_RELEASE):
            raise TransferError(f"a release holds at most {MAX_ASSETS_PER_RELEASE} assets")
        if not (isinstance(max_file_bytes, int) and 1 <= max_file_bytes <= MAX_ASSET_BYTES):
            raise TransferError("GitHub refuses release assets of 2 GiB or more")
        if isinstance(declared_free_bytes, bool) or not isinstance(declared_free_bytes, int) or declared_free_bytes < 0:
            raise TransferError("the declared free capacity must be a non-negative number of bytes")
        self.repository, self.scheme, self.shards = repository, scheme, shards
        self.assets_per_release, self.max_file_bytes = assets_per_release, max_file_bytes
        self.declared_free_bytes = declared_free_bytes
        self.api, self.uploads = api_url.rstrip("/"), upload_url.rstrip("/")
        options = {} if sleep is None else {"sleep": sleep}
        self.http = Http(token_env=token_env, bases=(self.api, self.uploads), max_retries=max_retries,
                         max_wait_seconds=max_wait_seconds, **options)
        self._cache_dir = None if cache_dir is None else Path(cache_dir)
        self._releases: dict[int, dict | None] = {}
        self._assets: dict[int, dict[str, dict]] = {}          # release id -> asset name -> asset
        self._read_back: dict[int, tuple[Path, str, int]] = {}  # asset id -> (local copy, sha256, size)
        self._all_loaded = False

    def __repr__(self) -> str:
        return f"GitHubReleaseDestination({self.repository!r}, scheme={self.scheme!r}, shards={self.shards})"

    # ----- names, shards, releases ---------------------------------------------------

    def describe(self) -> dict:
        return {"kind": "github-release-assets", "location": None, "repository": self.repository,
                "scheme": self.scheme, "shards": self.shards, "assets_per_release": self.assets_per_release,
                "declared_free_bytes": self.declared_free_bytes}

    @staticmethod
    def _name(key: str) -> str:
        return sha256_bytes(relative_name(key).encode("utf-8"))

    def _shard(self, key: str) -> int:
        return int(self._name(key)[:12], 16) % self.shards

    def _tag(self, shard: int) -> str:
        return f"{self.scheme}-{shard:04d}"

    def _repo(self, path: str) -> str:
        return f"{self.api}/repos/{self.repository}{path}"

    def _fail(self, what: str, status: int) -> TransferError:
        return TransferError(f"GitHub answered {status} to {what} in {self.repository}")

    def _release(self, shard: int, create: bool) -> dict | None:
        """The release of a shard (cached), created on first use when ``create``. A tag that exists
        cannot be created again, so concurrent creators end with one release."""
        if self._releases.get(shard) is not None:
            return self._releases[shard]
        tag = self._tag(shard)
        reply = self.http.request("GET", self._repo(f"/releases/tags/{tag}"), headers=_JSON)
        if reply.status == 404 and create:
            made = self.http.request("POST", self._repo("/releases"), headers=_JSON, body=_json_bytes({
                "tag_name": tag, "name": tag, "prerelease": True, "draft": False,
                "body": "Recovery-safeguard backup shard. Assets are named by the SHA-256 of their key; "
                        "do not edit, rename or delete them."}))
            if made.status not in (201, 422):
                raise self._fail(f"creating the release {tag}", made.status)
            reply = made if made.status == 201 else self.http.request(
                "GET", self._repo(f"/releases/tags/{tag}"), headers=_JSON)
        if reply.status == 404:
            self._releases[shard] = None
            return None
        if reply.status not in (200, 201):
            raise self._fail(f"reading the release {tag}", reply.status)
        release = reply.json()
        if not isinstance(release, dict) or not isinstance(release.get("id"), int) or release.get("tag_name") != tag:
            raise TransferError(f"GitHub described the release {tag} in an unexpected shape")
        self._releases[shard] = release
        return release

    def _load_assets(self, release: dict) -> dict[str, dict]:
        """Every asset of a release by name, following pagination."""
        assets: dict[str, dict] = {}
        url = self._repo(f"/releases/{release['id']}/assets?per_page=100")
        while url:
            reply = self.http.request("GET", url, headers=_JSON)
            if reply.status != 200:
                raise self._fail("listing release assets", reply.status)
            page = reply.json()
            if not isinstance(page, list):
                raise TransferError("GitHub listed release assets in an unexpected shape")
            for asset in page:
                if not (isinstance(asset, dict) and isinstance(asset.get("id"), int) and isinstance(asset.get("name"), str)
                        and isinstance(asset.get("state"), str)):
                    raise TransferError("GitHub described a release asset in an unexpected shape")
                assets[asset["name"]] = asset
            url = next_link(reply.headers)
        self._assets[release["id"]] = assets
        return assets

    def _assets_of(self, release: dict, refresh: bool = False) -> dict[str, dict]:
        if refresh or release["id"] not in self._assets:
            return self._load_assets(release)
        return self._assets[release["id"]]

    def _find(self, key: str) -> tuple[dict, dict] | None:
        """(release, asset) of a stored object. An asset that is not in the ``uploaded`` state is
        not an object. Without the token nothing is answered, not even from this process's index."""
        self.http.require_token()
        release = self._release(self._shard(key), create=False)
        if release is None:
            return None
        asset = self._assets_of(release).get(self._name(key))
        return (release, asset) if asset is not None and asset["state"] == "uploaded" else None

    def _need(self, key: str) -> tuple[dict, dict]:
        found = self._find(key)
        if found is None:
            raise TransferError(f"the object {self._name(key)[:12]} is not stored in {self.repository}")
        return found

    # ----- asset operations ----------------------------------------------------------

    def _delete_asset(self, release: dict, asset: dict) -> None:
        reply = self.http.request("DELETE", self._repo(f"/releases/assets/{asset['id']}"), headers=_JSON)
        if reply.status not in (204, 404):
            raise self._fail("deleting a release asset", reply.status)
        self._assets_of(release).pop(asset["name"], None)
        cached = self._read_back.pop(asset["id"], None)
        if cached is not None:
            cached[0].unlink(missing_ok=True)

    def _create(self, release: dict, key: str, source: Path) -> tuple[bool, dict]:
        """Upload ``source`` as the asset of ``key``. (True, asset): created and in the uploaded
        state with the right size. (False, existing asset): the name already holds an uploaded
        asset (nothing was changed). A leftover that is not in the uploaded state is deleted and
        the upload repeated once."""
        size = source.stat().st_size
        if size >= self.max_file_bytes:
            raise CapacityError(f"a file of {size} bytes exceeds the release-asset limit of {self.max_file_bytes} bytes")
        name = self._name(key)
        query = urllib.parse.urlencode({"name": name, "label": key})
        url = f"{self.uploads}/repos/{self.repository}/releases/{release['id']}/assets?{query}"
        for _ in range(2):
            assets = self._assets_of(release)
            if name not in assets and len(assets) >= self.assets_per_release:
                raise CapacityError(f"the release {release['tag_name']} holds {len(assets)} assets, its limit; "
                                    "this layout is full")
            reply = self.http.request("POST", url, headers={**_JSON, "Content-Type": "application/octet-stream"},
                                      body=source)
            if reply.status == 201:
                asset = reply.json()
                if not (isinstance(asset, dict) and asset.get("name") == name and asset.get("state") == "uploaded"
                        and asset.get("size") == size and isinstance(asset.get("id"), int)):
                    self._assets_of(release, refresh=True)
                    raise TransferError("GitHub did not confirm the upload as stored in full")
                assets[name] = asset
                return True, asset
            if reply.status != 422:
                raise self._fail("uploading a release asset", reply.status)
            existing = self._assets_of(release, refresh=True).get(name)
            if existing is None:
                raise self._fail("uploading a release asset", reply.status)
            if existing["state"] == "uploaded":
                return False, existing
            self._delete_asset(release, existing)   # a torn upload: documented as safe to delete
        raise TransferError("an upload kept leaving an unfinished asset behind")

    def _fetch(self, asset: dict, target: Path) -> tuple[str, int]:
        reply = self.http.request("GET", self._repo(f"/releases/assets/{asset['id']}"), headers=_BINARY, sink=target)
        if reply.status != 200 or reply.sha256 is None:
            raise self._fail("downloading a release asset", reply.status)
        return reply.sha256, reply.size

    def _cache(self) -> Path:
        if self._cache_dir is None:
            self._cache_dir = Path(tempfile.mkdtemp(prefix="github-destination-"))
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir

    def _read_back_copy(self, asset: dict) -> tuple[Path, str, int]:
        """A local copy of an asset's bytes as downloaded from GitHub, with their hash and size."""
        if asset["id"] not in self._read_back:
            path = self._cache() / f"asset-{asset['id']}-{token()}"
            digest, size = self._fetch(asset, path)
            self._read_back[asset["id"]] = (path, digest, size)
        return self._read_back[asset["id"]]

    @staticmethod
    def _reported(asset: dict, digest: str, size: int) -> bool:
        """Whether what GitHub reports for an asset agrees with the bytes we meant to store."""
        reported = asset.get("digest")
        return asset.get("size") == size and (reported is None or reported == f"sha256:{digest}")

    # ----- the Destination contract --------------------------------------------------

    def free_bytes(self) -> int:
        """The declared cap: GitHub reports no free space (and states no total size limit). Without
        the token even this refuses, so an unconfigured destination never looks usable."""
        self.http.require_token()
        return self.declared_free_bytes

    def probe(self) -> None:
        key = f"{STAGING}probe-{token()}"
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "probe"
            source.write_bytes(b"probe")
            self.upload(source, key)
        try:
            if self.read(key) != b"probe":
                raise TransferError(f"{self.repository}: the probe object read back differently")
        finally:
            self.discard(key)

    def upload(self, source: Path, key: str) -> None:
        if not is_staging(key):
            raise TransferError(f"{self._name(key)[:12]}: uploads go to the staging area only")
        self.http.require_token()
        source = Path(source)
        if source.stat().st_size >= self.max_file_bytes:
            raise CapacityError(f"a file of {source.stat().st_size} bytes exceeds the release-asset limit of "
                                f"{self.max_file_bytes} bytes")
        release = self._release(self._shard(key), create=True)
        created, asset = self._create(release, key, source)
        if not created:                       # a staging name may be overwritten: replace the old asset
            self._delete_asset(release, asset)
            created, asset = self._create(release, key, source)
            if not created:
                raise TransferError("a staging asset could not be replaced")

    def commit(self, staged: str, final: str) -> bool:
        if not is_staging(staged) or is_staging(final):
            raise TransferError("a commit moves a staging object to a final name")
        staged_release, staged_asset = self._need(staged)
        copy, digest, size = self._read_back_copy(staged_asset)
        release = self._release(self._shard(final), create=True)
        created, asset = self._create(release, final, copy)
        if created:
            if not self._reported(asset, digest, size):
                raise TransferError("GitHub reports another size or digest for a committed object than was sent")
            self._delete_asset(staged_release, staged_asset)
            return True
        if self.sha256(final) != (digest, size):
            raise CollisionError(f"the final object {self._name(final)[:12]} already holds different bytes; the "
                                 "staged copy is kept")
        self._delete_asset(staged_release, staged_asset)
        return False

    def put_new(self, key: str, data: bytes) -> bool:
        if is_staging(key):
            raise TransferError("put_new creates final objects")
        release = self._release(self._shard(key), create=True)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "object"
            source.write_bytes(data)
            created, asset = self._create(release, key, source)
        if created:
            if not self._reported(asset, sha256_bytes(data), len(data)):
                raise TransferError("GitHub reports another size or digest for a new object than was sent")
            return True
        if self.read(key) != data:
            raise CollisionError(f"the object {self._name(key)[:12]} exists with different content; immutable "
                                 "records are never replaced")
        return False

    def exists(self, key: str) -> bool:
        return self._find(key) is not None

    def read(self, key: str) -> bytes:
        _, asset = self._need(key)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "object"
            self._fetch(asset, target)
            return target.read_bytes()

    def sha256(self, key: str) -> tuple[str, int]:
        """The hash and size of the bytes downloaded from GitHub (never the reported digest). The
        copy of a staging object is kept for its commit."""
        _, asset = self._need(key)
        if is_staging(key):
            _, digest, size = self._read_back_copy(asset)
            return digest, size
        with tempfile.TemporaryDirectory() as folder:
            return self._fetch(asset, Path(folder) / "object")

    def download(self, key: str, target: Path) -> None:
        _, asset = self._need(key)
        target = Path(target)
        part = target.with_name(f".{target.name}.{token()}.part")
        try:
            self._fetch(asset, part)
            shutil.move(str(part), str(target))
        finally:
            part.unlink(missing_ok=True)

    def _load_all(self) -> None:
        """Read the asset index of every release of this scheme once per process."""
        if self._all_loaded:
            return
        pattern = re.compile(re.escape(self.scheme) + r"-(\d{4,})")
        url = self._repo("/releases?per_page=100")
        while url:
            reply = self.http.request("GET", url, headers=_JSON)
            if reply.status != 200:
                raise self._fail("listing releases", reply.status)
            page = reply.json()
            if not isinstance(page, list):
                raise TransferError("GitHub listed releases in an unexpected shape")
            for release in page:
                match = pattern.fullmatch(str(release.get("tag_name"))) if isinstance(release, dict) else None
                if match and int(match.group(1)) < self.shards and isinstance(release.get("id"), int):
                    self._releases[int(match.group(1))] = release
                    if release["id"] not in self._assets:
                        self._load_assets(release)
            url = next_link(reply.headers)
        self._all_loaded = True

    def list(self, prefix: str) -> list[str]:
        self.http.require_token()
        self._load_all()
        base = prefix.rstrip("/")
        keys = []
        for release in [r for r in self._releases.values() if r is not None]:
            for name, asset in self._assets_of(release).items():
                if asset["state"] != "uploaded":
                    continue
                key = asset.get("label")
                if not isinstance(key, str) or sha256_bytes(key.encode("utf-8")) != name:
                    raise TransferError("a release asset's label does not reproduce its name; the listing of "
                                        f"{self.repository} cannot be trusted")
                if not base or key == base or key.startswith(base + "/"):
                    keys.append(key)
        return sorted(keys)

    def discard(self, key: str) -> None:
        if not is_staging(key):
            raise TransferError(f"{self._name(key)[:12]}: only staging objects are ever removed")
        found = self._find(key)
        if found is not None:
            self._delete_asset(*found)


def _json_bytes(obj: dict) -> bytes:
    return json.dumps(obj).encode("utf-8")
