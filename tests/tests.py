import pytest

import history_table.history_table as ht
from sqlalchemy import create_engine, event
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy import orm
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
    
    
    orm.clear_mappers()
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
    
    orm.clear_mappers()
    Base.metadata.drop_all(engine)
    Base.metadata.clear()

def test_version_message(db_versioned_session, engine, base):
    
    session = db_versioned_session
    Base = base

    class MyModel(Base, ht.Versioned):
        __tablename__ = 'mytable'
        
        include_version_message = True

        id = Column(Integer, primary_key = True)
        data = Column(String)

        @orm.reconstructor
        def set_version_message(self, msg = ''):
            if self.include_version_message is True:
                self.version_message = msg

    Base.metadata.create_all(engine)

    ModelHistory = MyModel.__history_mapper__.class_
    
    model = MyModel(data = 'initial data')
    session.add(model)
    session.commit()

    assert model.version == 1

    model.data = 'changed data'
    msg = 'test message'
    model.set_version_message(msg)
    
    session.commit()

    assert model.version == 2
    
    model.data = 'second change'
    msg2 = 'second test message'
    model.set_version_message(msg2)

    session.commit()

    assert model.version == 3

    hist1, hist2 = session.query(ModelHistory).all()

    assert hist1.version_message == msg 
    assert hist2.version_message == msg2
    assert model.version_message == ''
    
    orm.clear_mappers()
    Base.metadata.drop_all(engine)
    Base.metadata.clear()
