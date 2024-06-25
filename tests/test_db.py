import datetime
import sqlite3

import pytest
from flaskr.db import get_db, convert_timestamp


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('flaskr.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called

def test_timestamp_converter():
    assert convert_timestamp(b'2008-01-01 00:00:00') == datetime.datetime(2008, 1, 1, 0, 0, 0)

    with pytest.raises(Exception) as e:
        convert_timestamp(b'invalid timestamp')
