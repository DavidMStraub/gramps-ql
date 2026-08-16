import os
import shutil
import tempfile

import pytest
from gramps.cli.clidbman import CLIDbManager
from gramps.gen.db import DbReadBase, DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Note, Person, Tag

from gramps_ql.gql import GQLQuery


@pytest.fixture
def db():
    """Return Gramps Database."""
    TEST_GRAMPSHOME = tempfile.mkdtemp()
    os.environ["GRAMPSHOME"] = TEST_GRAMPSHOME
    dbman = CLIDbManager(DbState())
    path, _name = dbman.create_new_db_cli("GQL Test", dbid="sqlite")
    db = make_database("sqlite")
    db.load(path)
    person = Person()
    person.gramps_id = "person001"
    note = Note()
    note.gramps_id = "note001"
    note.set("Hello world")
    tag = Tag()
    tag.set_name("mytag")
    with DbTxn("Add test objects", db) as trans:
        db.add_person(person, trans)
        db.add_note(note, trans)
        db.add_tag(tag, trans)
    yield db
    db.close()
    shutil.rmtree(TEST_GRAMPSHOME)


def test_fixture(db):
    assert isinstance(db, DbReadBase)


def test_person_gramps_id(db):
    q = GQLQuery("class=person", db=db)
    assert len(list(q.iter_objects())) == 1
    for obj in q.iter_objects():
        assert isinstance(obj, Person)
    q = GQLQuery("""class=person and gramps_id="person001" """, db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("""class=person and gramps_id!="person001" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = GQLQuery("""class=person and gramps_id="person002" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = GQLQuery("""class=person and gramps_id>"person002" """, db=db)
    assert len(list(q.iter_objects())) == 0
    q = GQLQuery("""class=person and gramps_id<"person002" """, db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("class=person and gramps_id < 'person002'", db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("class=person and gramps_id < 'person002'", db=db)
    assert len(list(q.iter_objects())) == 1


def test_note(db):
    q = GQLQuery("class=note", db=db)
    assert len(list(q.iter_objects())) == 1
    for obj in q.iter_objects():
        assert isinstance(obj, Note)
    q = GQLQuery("class=note and text.string ~ hello", db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("class=note and text.string ~ bye", db=db)
    assert len(list(q.iter_objects())) == 0


def test_tag(db):
    q = GQLQuery("class=tag", db=db)
    assert len(list(q.iter_objects())) == 1
    for obj in q.iter_objects():
        assert isinstance(obj, Tag)
    q = GQLQuery("class=tag and name=mytag", db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("class=tag and name=othertag", db=db)
    assert len(list(q.iter_objects())) == 0
