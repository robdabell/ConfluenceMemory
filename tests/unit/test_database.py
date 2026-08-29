from contextlib import contextmanager

from knowledge_poc.storage import database as database_module
from knowledge_poc.storage.database import Database


class FakeResult:
    def __init__(self, rows=None):
        self.rows = rows or []

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.versions = set()
        self.migration_bodies = []
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.queries.append(query)
        if query == "SELECT version FROM schema_migration":
            return FakeResult([(version,) for version in sorted(self.versions)])
        if query.startswith("INSERT INTO schema_migration"):
            self.versions.add(params[0])
        elif query.strip().startswith("SELECT"):
            self.migration_bodies.append(query)
        return FakeResult()


def test_migrate_skips_versions_already_applied(tmp_path, monkeypatch):
    migration = tmp_path / "001_test.sql"
    migration.write_text("SELECT 'migration body';", encoding="utf-8")
    connection = FakeConnection()
    monkeypatch.setattr(database_module.psycopg, "connect", lambda _url: connection)
    database = Database("postgresql://unused")

    assert database.migrate(tmp_path) == ["001_test.sql"]
    assert database.migrate(tmp_path) == []
    assert connection.migration_bodies == ["SELECT 'migration body';"]


def test_search_casts_query_parameters_to_vector(monkeypatch):
    connection = FakeConnection()
    database = Database("postgresql://unused")

    @contextmanager
    def connect():
        yield connection

    monkeypatch.setattr(database, "connect", connect)

    assert database.search([0.1, 0.2], limit=3) == []
    search_query = connection.queries[-1]
    assert search_query.count("%s::vector") == 2
