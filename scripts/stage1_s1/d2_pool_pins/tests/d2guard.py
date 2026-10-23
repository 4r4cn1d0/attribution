"""The fixture guard of the D-2 tests (standard library only; D-1's tests/d1guard.py, same rule). A module fixture that
runs D-2 code returns guarded(name, make): make()'s value, or, when make() raises an Exception, a FixtureFailed
stand-in whose every use (item, attribute, iteration, call, membership, len) raises AssertionError inside the test
body. A wrapper defect therefore shows as test failures, never as setup errors, which the mutation runner
(mutation/run_mutants.py) counts as invalid runs. A skip (pytest's Skipped is a BaseException) and KeyboardInterrupt
pass through. The failure message carries the original exception's type and text, so an errno 28 or 122 (a full disk)
still reaches the runner's invalid rule."""

from __future__ import annotations


class FixtureFailed:
    """Stands in for a fixture value whose making raised; any use fails the test that uses it."""

    def __init__(self, name: str, exc: BaseException):
        self._name = name
        self._exc = exc

    def __repr__(self) -> str:
        return f"FixtureFailed({self._name!r}, {type(self._exc).__name__}: {self._exc})"

    def _fail(self, *_args, **_kwargs):
        raise AssertionError(f"{self._name} failed in its fixture: {type(self._exc).__name__}: {self._exc}") from self._exc

    def __getattr__(self, name: str):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        self._fail()

    __getitem__ = __iter__ = __call__ = __contains__ = __len__ = _fail


def guarded(name: str, make):
    """make()'s value, or a FixtureFailed when it raises an Exception (a dependent fixture that touches a FixtureFailed
    raises AssertionError, so it becomes a FixtureFailed too)."""
    try:
        return make()
    except Exception as exc:  # noqa: BLE001  (every wrapper defect must become a test failure)
        return FixtureFailed(name, exc)
