import pytest

import history_table.history_table as ht
from sqlalchemy import create_engine, event
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import Session, relationship
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

@pytest.fixture
def db_versioned_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    ht.version_session(session)
    
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

def test_simple_creation(db_versioned_session, engine, base):
    '''Tests that a trivial model has the expected history table created
    with it and that it records a change.
    '''
    
    session = db_versioned_session
    Base = base

    class MyModel(Base, ht.Versioned):
        __tablename__ = 'mytable'

        id = Column(Integer, primary_key = True)
        data = Column(String)
    
    Base.metadata.create_all(engine)

    model = MyModel(data="original data")
    session.add(model)
    session.commit()

    assert model.version == 1

    model.data = "changed data"
    session.commit()
    
    assert model.version == 2
    
    Base.metadata.drop_all(engine)
    Base.metadata.clear()

def test_relationship(db_versioned_session, engine, base):
    
    session = db_versioned_session
    Base = base

    class OtherModel(Base):
        __tablename__ = 'othertable'

        id = Column(Integer, primary_key = True)
        otherdata = Column(String)

    class MyModel(Base, ht.Versioned):
        __tablename__ = 'mytable'

        id = Column(Integer, primary_key = True)
        data = Column(String)
        other_id = Column(Integer, ForeignKey(OtherModel.id))
        other = relationship("OtherModel", backref='models')

    Base.metadata.create_all(engine)
    
    model = MyModel(data = 'initial data')
    session.add(model)
    session.commit()
    
    assert model.version == 1

    othermodel = OtherModel(otherdata = "om1")
    model.other = othermodel
    session.commit()
    
    assert model.version == 2
    
    Base.metadata.drop_all(engine)
    Base.metadata.clear()
