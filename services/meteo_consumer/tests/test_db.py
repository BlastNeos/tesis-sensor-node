from src.db import MeteoDB


def test_from_env_builds_postgresql_dsn(monkeypatch) -> None:
    monkeypatch.setenv("METEO_DB_HOST", "meteo-test-host")
    monkeypatch.setenv("METEO_DB_PORT", "5556")
    monkeypatch.setenv("METEO_DB_NAME", "meteo_data_test")
    monkeypatch.setenv("METEO_DB_USER", "meteo_test_user")
    monkeypatch.setenv("METEO_DB_PASSWORD", "meteo_test_pw")

    db = MeteoDB.from_env()
    url = db._engine.url

    assert url.drivername == "postgresql+psycopg2"
    assert url.host == "meteo-test-host"
    assert url.port == 5556
    assert url.database == "meteo_data_test"
    assert url.username == "meteo_test_user"
    assert url.password == "meteo_test_pw"

    db.dispose()


def test_from_env_uses_local_defaults(monkeypatch) -> None:
    for variable in (
        "METEO_DB_HOST",
        "METEO_DB_PORT",
        "METEO_DB_NAME",
        "METEO_DB_USER",
        "METEO_DB_PASSWORD",
    ):
        monkeypatch.delenv(variable, raising=False)

    db = MeteoDB.from_env()
    url = db._engine.url

    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "meteo_data"
    assert url.username == "meteo_app"

    db.dispose()
