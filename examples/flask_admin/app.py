from flask import Flask, render_template
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
import history_table.history_table as ht

#### stuff that would normally be in an app factory ####
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECRET_KEY'] = "Don't do this set a real secret key"

admin = Admin(app)

#even though flask uses a session per request, you can version flask-admin's
#sessionmaker like this; the versioning event listeners still work
db = SQLAlchemy(app)
ht.version_session(db.session)

#### stuff that would normally be in a separate 'models.py' file ####
Base = declarative_base()

class MyModel(Base, ht.Versioned):
    __tablename__ = 'mymodel'
    
    #include this to allow use of edit message on our custom admin 'edit' form
    include_version_message = True
    
    id = Column(Integer, primary_key = True)
    data = Column(String)
    
    @classmethod
    def get_history_model(cls):
        return cls.__history_mapper__.class_

#### stuff that would normally go in a separate admin file #####

class MyModelView(ModelView):
    #we add our own 'edit' template to use our 'version message' feature
    #edit_template = 'admin/myedit.html'
    pass

class MyModelHistoryView(ModelView):
    #this is where we could do things like limit the columns
    #we want displayed
    pass

@app.route('/')
def index():
    return "<a href='/admin' >Click here to go to the admin page</a>"

if __name__ == '__main__': 

    view1 = MyModelView(MyModel, db.session)
    view2 = MyModelHistoryView(MyModel.get_history_model(), db.session)
    
    admin.add_views(view1, view2)
    
    #Create tables, add a couple sample rows for us to see on the admin page. 
    Base.metadata.create_all(db.get_engine())

    with app.app_context():
        m1 = MyModel(data='model #1')
        m2 = MyModel(data='model #2')
        db.session.add_all([m1, m2])
        db.session.commit()
    

    app.run()
