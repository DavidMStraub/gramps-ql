import os
import shutil
import tempfile

import pytest
from gramps.cli.clidbman import CLIDbManager
from gramps.gen.db import DbReadBase, DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Note, Person, PersonRef

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
    with DbTxn("Add test objects", db) as trans:
        # person001
        person = Person()
        person.set_gramps_id("person001")
        person.set_handle("handle001")
        db.add_person(person, trans)

        # note003
        note = Note()
        note.set_gramps_id("note003")
        note.set_handle("handle003")
        db.add_note(note, trans)

        # person002
        person = Person()
        person.set_gramps_id("person002")
        person.set_handle("handle002")
        person_ref = PersonRef()
        person_ref.set_reference_handle("handle001")
        person.add_person_ref(person_ref)
        person.add_note("handle003")
        db.add_person(person, trans)

    yield db
    db.close()
    shutil.rmtree(TEST_GRAMPSHOME)


def test_fixture(db):
    assert isinstance(db, DbReadBase)


def test_get_person(db):
    q = GQLQuery("person_ref_list.any.ref = handle001", db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("person_ref_list.any.ref.get_person.gramps_id = person001", db=db)
    assert len(list(q.iter_objects())) == 1


def test_get_note(db):
    q = GQLQuery("note_list.any = handle003 and gramps_id = person002", db=db)
    assert len(list(q.iter_objects())) == 1
    q = GQLQuery("note_list.any.get_note.gramps_id = note003", db=db)
    assert len(list(q.iter_objects())) == 1


def test_get_note_0(db):
    q = GQLQuery("note_list.any.get_person", db=db)
    assert len(list(q.iter_objects())) == 0
