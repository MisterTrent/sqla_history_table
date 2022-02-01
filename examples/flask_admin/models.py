from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
import history_table.history_table as ht

Base = declarative_base()

class MyModel(Base, ht.Versioned):
    __tablename__ = 'mymodel'
    
    #include this to allow use of edit message on our custom admin 'edit' form
    include_version_message = True
    
    id = Column(Integer, primary_key = True)
    data = Column(String)
    
    @classmethod
    def get_history_model(cls):
        '''Convenience method to retrieve ORM model for history table'''
        return cls.__history_mapper__.class_


