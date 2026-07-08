import pytest

from src import db, storage


@pytest.fixture(autouse=True)
def isolated_worker_data(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "worker.db")
    monkeypatch.setattr(storage, "STORAGE_ROOT", tmp_path / "summaries")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
