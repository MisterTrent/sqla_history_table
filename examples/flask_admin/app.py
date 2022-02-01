from flask import Flask, render_template
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
import history_table.history_table as ht

from models import MyModel, Base
from admin import MyModelView, MyModelHistoryView

#### stuff that would normally be in an app factory ####
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECRET_KEY'] = "Don't do this set a real secret key"

#even though flask uses a session per request, you can version flask-admin's
#sessionmaker like this; the versioning event listeners still work
db = SQLAlchemy(app)
ht.version_session(db.session)

admin = Admin(app)
view1 = MyModelView(MyModel, db.session)
view2 = MyModelHistoryView(MyModel.get_history_model(), db.session)
admin.add_views(view1, view2)

#Create tables, add a couple sample rows for us to see on the admin page. 
Base.metadata.create_all(db.get_engine())
with app.app_context():
    m1 = MyModel(data='row 1 starting data')
    m2 = MyModel(data='row 2 starting data')
    db.session.add_all([m1, m2])
    db.session.commit()

@app.route('/')
def index():
    #just a simple route to make it a "real" flask app
    return "<a href='/admin' >Click here to go to the admin page</a>"

if __name__ == '__main__': 
    app.run()
