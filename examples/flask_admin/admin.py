from flask_admin.base import expose
from flask_admin.form import BaseForm
from flask_admin.babel import gettext, ngettext
from flask_admin.helpers import get_redirect_target, get_form_data, flash_errors
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.model.helpers import get_mdict_item_or_list
from wtforms.fields import TextAreaField, HiddenField
from wtforms.validators import InputRequired
from flask import request, redirect, flash
import history_table.history_table as ht
from models import MyModel
import sqlalchemy as sqla
import pdb

my_cols = sqla.inspect(MyModel).local_table.c

class BaseVersionedView(ModelView):
    '''Bare-bones view class for versioned models with history log message.
    '''
    
    #exclude versioning attributes (e.g. version number) from edit/create
    form_excluded_columns = tuple(c.key for c in my_cols 
                                    if ht._is_versioning_col(c))

    def on_model_change(self, form, model, is_created):
        '''Custom handler for model edits before commit to db. Save's user
        message from form's extra field to model's transient attribute.
        '''
        
        #versioned models don't record creation
        if model.include_version_message and not is_created:
            model.version_message = form.history_message.data

class VersionedModelView(BaseVersionedView):
    #prevent default delete from being present anywhere
    can_delete = False
    
    #our replacement for default delete toggle
    can_deleteplus = False
    
    #custom delete input page template for deleting-with-message
    delete_template = '/admin/deleteplus.html'
    
    def get_edit_form(self):
        '''Overrides the default edit_view form to add a non-model field for
        the edit message. This is used instead of form_extra_columns because
        that would also add the message field to the create_view, where a 
        message is not needed since Versioned models don't log creation. If
        history log modified to store entry for the original table's row 
        creation, then you could use that approach instead.
        '''
        
        form = super().get_edit_form()
        form.history_message = TextAreaField(
            'Changelog Message',
            render_kw={'placeholder' : 'Enter a message explaining the edit'}
        )

        return form
    
    def deleteplus_form(self):
        '''Creates the form in a way that flask-admin considers 
        "backwards-compatible". Our delete_view currently follows the 
        flask-admin approach used in its edit_view, with a querystring used to
        load the deletion page, but this would accommodate a form in the 
        list_row_actions created via a TemplateListRowAction (f-a does this for
        its link to the default delete_view).
        '''
        
        class DeleteForm(BaseForm):
            id = HiddenField(validators=[InputRequired()])
            history_message = TextAreaField(
            'Changelog Message',
            render_kw={'placeholder' : 'Enter a message explaining the deletion'}
            )
        
        if request.form:
            return DeleteForm(request.form)
        elif request.args:
            return DeleteForm(request.args)
        else:
            return DeleteForm()
    
    
class MyModelView(VersionedModelView):
    can_deleteplus = True

    column_extra_row_actions = [
        EndpointLinkRowAction('glyphicon icon-trash', '.delete_view')
    ]
    
    @expose('/delete/', methods=('GET','POST'))
    def delete_view(self):
        '''Overrides default delete_view to provide a page similar to edit_view,
        where user can submit a form with message explaining the delete request.
        The message, in turn, is appended to the model's connected sqlalchemy
        history table.

        References to a modal display option are omitted for simplicity. Templating
        a modal requires a custom list.html template. Easy enough to do, but beyond
        the scope of this example currently.
        '''
        
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_deleteplus:
            redirect(return_url)
         
        id = get_mdict_item_or_list(request.args, 'id')

        #'disables' original delete button(if not removed), b/c it POSTs a form
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)
        
        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)
        
        form = self.deleteplus_form()
       
        #validation fails when GET-ing page, skipping straight to form display
        if self.validate_form(form):
            model.version_message = form.history_message.data
            
            if self.delete_model(model):
                count = 1
                flash(ngettext('Record was successfully deleted.',
                            '%(count)s records were successfully deleted.',
                             count, count=count), 'success')

                return redirect(return_url)

            else:
                flash_errors(form, message='Failed to delete record. %(error)s')

        template = self.delete_template
        
        return self.render(template, form=form, return_url=return_url) 

class MyModelHistoryView(ModelView):
    #keep the history log immutable from the user's perspective
    can_create = False
    can_edit = False
    can_delete = False
