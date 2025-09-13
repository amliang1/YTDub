import json
from types import SimpleNamespace
from typing import List

import pytest

from app.services.translator import Translator


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def make_payload(texts: List[str]):
    return {
        "data": {
            "translations": [{"translatedText": f"X:{t}"} for t in texts]
        }
    }


def test_translate_batch_success(monkeypatch):
    # Avoid real sleeps
    monkeypatch.setenv("TESTING", "true")

    def fake_post(url, params=None, **kwargs):
        # params may be list of tuples or dict
        if isinstance(params, list):
            texts = [v for (k, v) in params if k == 'q']
        else:
            texts = [params.get('q')] if params and 'q' in params else []
        payload = make_payload(texts)
        return DummyResponse(200, payload)

    import app.services.translator as tr
    monkeypatch.setattr(tr.requests, "post", fake_post)
    monkeypatch.setattr(tr.time, "sleep", lambda *_: None)

    t = Translator(failure_threshold=3, recovery_time_sec=1)
    texts = ["a", "b", "c"]
    out = t.translate_batch(texts, target_language="es", source_language="en")
    assert out == ["X:a", "X:b", "X:c"]


def test_translate_batch_retry_and_backoff(monkeypatch):
    calls = {"n": 0}

    def flaky_post(url, params=None, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            # fail first two attempts
            return DummyResponse(500, {})
        # success on third
        if isinstance(params, list):
            texts = [v for (k, v) in params if k == 'q']
        else:
            texts = [params.get('q')] if params and 'q' in params else []
        return DummyResponse(200, make_payload(texts))

    import app.services.translator as tr
    monkeypatch.setattr(tr.requests, "post", flaky_post)
    monkeypatch.setattr(tr.time, "sleep", lambda *_: None)

    t = Translator(failure_threshold=5, recovery_time_sec=1)
    out = t.translate_batch(["hi"], target_language="es", source_language="en")
    assert out == ["X:hi"]
    assert calls["n"] == 3


def test_circuit_breaker_opens(monkeypatch):
    def always_fail(url, params=None, **kwargs):
        return DummyResponse(500, {})

    import app.services.translator as tr
    monkeypatch.setattr(tr.requests, "post", always_fail)
    monkeypatch.setattr(tr.time, "sleep", lambda *_: None)

    t = Translator(failure_threshold=2, recovery_time_sec=30)

    with pytest.raises(Exception):
        t.translate_batch(["x"], target_language="es", source_language="en")
    # second attempt should quickly fail and open circuit
    with pytest.raises(Exception):
        t.translate_batch(["y"], target_language="es", source_language="en")
    # now circuit is open; immediate rejection
    with pytest.raises(RuntimeError) as ei:
        t.translate_batch(["z"], target_language="es", source_language="en")
    assert "translator_circuit_open" in str(ei.value)

