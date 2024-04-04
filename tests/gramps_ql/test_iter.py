import os
import shutil
import tempfile

import pytest
from gramps.cli.clidbman import CLIDbManager
from gramps.gen.db import DbReadBase, DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Person

from gramps_ql.gql import GQLQuery


@pytest.fixture
def db():
    """Return Gramps Database."""
    TEST_GRAMPSHOME = tempfile.mkdtemp()
    os.environ["GRAMPSHOME"] = TEST_GRAMPSHOME
    dbman = CLIDbManager(DbState())
    path, name = dbman.create_new_db_cli("GQL Test", dbid="sqlite")
    db = make_database("sqlite")
    db.load(path)
    person = Person()
    person.gramps_id = "person001"
    with DbTxn("Add test objects", db) as trans:
        db.add_person(person, trans)
    yield db
    db.close()
    shutil.rmtree(TEST_GRAMPSHOME)


def test_fixture(db):
    assert isinstance(db, DbReadBase)


def test_person_gramps_id(db):
    q = GQLQuery("type=person")
    assert len(list(q.iter_objects(db))) == 1
    for obj in q.iter_objects(db):
        assert isinstance(obj, Person)
    q = GQLQuery("""type=person and gramps_id="person001" """)
    assert len(list(q.iter_objects(db))) == 1
    q = GQLQuery("""type=person and gramps_id!="person001" """)
    assert len(list(q.iter_objects(db))) == 0
    q = GQLQuery("""type=person and gramps_id="person002" """)
    assert len(list(q.iter_objects(db))) == 0
    q = GQLQuery("""type=person and gramps_id>"person002" """)
    assert len(list(q.iter_objects(db))) == 0
    q = GQLQuery("""type=person and gramps_id<"person002" """)
    assert len(list(q.iter_objects(db))) == 1
    q = GQLQuery("type=person and gramps_id < 'person002'")
    assert len(list(q.iter_objects(db))) == 1
    q = GQLQuery("type=person and gramps_id < 'person002'")
    assert len(list(q.iter_objects(db))) == 1
