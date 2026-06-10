from sqlalchemy import inspect


def test_init_db_creates_tables(monkeypatch, tmp_path):
    monkeypatch.setenv("FITAI_DB_PATH", str(tmp_path / "t.db"))
    import importlib
    import app.config as config; importlib.reload(config)
    import app.db as db; importlib.reload(db)
    db.init_db()
    names = inspect(db.get_engine()).get_table_names()
    assert "user" in names
