import pytest

import history_table.history_table as ht
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

@pytest.fixture(scope="session")
def base():
    return declarative_base()

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite://", echo=True)

@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_session_versioning(db_session):
    '''Tests whether the session successfully has its listener applied
    and removed. The before_flush listener is responsible for firing
    the history table row creation.
    '''
    
    session = db_session
    ht.version_session(session)

    assert event.contains(session, "before_flush", ht.before_flush)

    ht.deversion_session(session)

    assert not event.contains(session, "before_flush", ht.before_flush)
