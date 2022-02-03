from flask_admin.contrib.sqla import ModelView
from wtforms.fields import TextAreaField
import history_table.history_table as ht
from models import MyModel
import sqlalchemy as sqla

my_cols = sqla.inspect(MyModel).local_table.c

class MyModelView(ModelView):
    #we add our own 'edit' template to use our 'version message' feature
    #edit_template = 'admin/myedit.html'

    #make versioning attributes (e.g. version number) not editable
    form_excluded_columns = tuple(c.key for c in my_cols 
                                    if ht._is_versioning_col(c))
        
    #writing these separately to illustrate their purpose
    _label = 'Changelog message'
    _input_id = 'history_message'
    
    #simple way to add placeholder text but possibly better handled by code 
    #dedicated to front-end presentation
    _render_kw = {'placeholder' : 'Enter a message explaining the edit here'}
    
    form_extra_fields = {
        _input_id : TextAreaField(_label, render_kw=_render_kw)
    }
    
    def on_model_change(self, form, model, is_created):
        '''Custom handler for model edits before commit to db. We use this
        to read the form's extra field and save it to the model's transient
        attribute (because the form field is not part of the model table).
        '''

        #creation isn't stored in the history
        if not is_created:
            model.version_message = form.history_message.data

class MyModelHistoryView(ModelView):
    #this is where we could do things like limit the columns
    #we want displayed
    pass
