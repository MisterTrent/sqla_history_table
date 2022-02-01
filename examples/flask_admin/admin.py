from flask_admin.contrib.sqla import ModelView

class MyModelView(ModelView):
    #we add our own 'edit' template to use our 'version message' feature
    #edit_template = 'admin/myedit.html'
    pass

class MyModelHistoryView(ModelView):
    #this is where we could do things like limit the columns
    #we want displayed
    pass
