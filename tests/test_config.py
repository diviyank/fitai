import importlib


def test_db_path_env_override(monkeypatch, tmp_path):
    db = tmp_path / "x.db"
    monkeypatch.setenv("FITAI_DB_PATH", str(db))
    import app.config as config
    importlib.reload(config)
    assert str(config.DB_PATH) == str(db)
    assert config.APP_TITLE == "fitai"
