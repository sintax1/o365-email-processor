import StringIO
import base64

from flask.ext.appbuilder.models.sqla.interface import SQLAInterface
from flask.ext.appbuilder import (ModelView, expose)
from flask.ext.appbuilder.actions import action
from wtforms import (PasswordField, validators)
from flask import (render_template, send_file, redirect)
from app import (appbuilder, db)

from .models import (Email, Attachment, Action, AppSettings)


class AttachmentModelView(ModelView):
    """Model representing an Attachment"""
    datamodel = SQLAInterface(Attachment)

    base_permissions = ['can_list', 'can_show']

    @expose('/download/<int:pk>')
    def download(self, pk):
        """Helper method for downloading email attachments"""
        attachment = db.session.query(Attachment).get(pk)
        strIO = StringIO.StringIO()
        strIO.write(base64.b64decode(attachment.file))
        strIO.seek(0)
        return send_file(
            strIO, attachment_filename=attachment.filename, as_attachment=True)


class EmailModelView(ModelView):
    """Model representing an Email"""
    datamodel = SQLAInterface(Email)

    base_permissions = ['can_list', 'can_show']

    label_columns = {
        'from_emailaddress': 'From', 'to_recipients': 'To',
        'cc_recipients': 'Cc', 'bcc_recipients': 'Bcc',
        'reply_to_recipients': 'Reply-To'}
    list_columns = [
        'received', 'from_emailaddress', 'to_recipients', 'subject']

    show_fieldsets = [
        ('Summary', {'fields': [
            'received', 'from_emailaddress',
            'sender', 'to_recipients', 'subject']}),
        ('Details', {'fields': [
            'created', 'sent',
            'modified', 'to_recipients',
            'cc_recipients', 'bcc_recipients',
            'reply_to_recipients', 'importance']}),
        ('Content', {'fields': [
            'body_preview', 'body_content_type',
            'body', 'attachments_downloadable']}),
        ('Analyst Info', {'fields': ['analyst_notes']})
    ]

    @action("muldelete", "Delete", "Delete all Really?", "fa-trash")
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)

        return redirect(self.get_redirect())


class ActionModelView(ModelView):
    datamodel = SQLAInterface(Action)

    default_python =\
        "def processor(attachment):" \
        "   # Do something with attachment" \
        "   return True" \
        "}" \

    label_columns = {
        'run_automatically': 'Automatic',
        'python_method': 'Python'}
    list_columns = ['name', 'enabled', 'run_automatically']

    show_fieldsets = [
        ('Summary', {'fields': ['name', 'enabled', 'run_automatically']}),
        ('Action', {'fields': ['python_method']})
    ]

    add_fieldsets = [
        ('Settings', {'fields': ['name', 'enabled', 'run_automatically']}),
        ('Action', {'fields': ['python_method']})
    ]
    edit_fieldsets = [
        ('Settings', {'fields': ['name', 'enabled', 'run_automatically']}),
        ('Action', {'fields': ['python_method']})
    ]


class AppSettingsModelView(ModelView):
    datamodel = SQLAInterface(AppSettings)
    base_permissions = ['can_list', 'can_show', 'can_edit']

    edit_form_extra_fields = {
        'service_account_password': PasswordField(
            'Password',
            description='Service Account Password',
            validators=[validators.Required()])}

    description_columns = {
        'accounts_to_check': 'Comma seperated list of email accounts that ' \
            'the automated email poller will check.' \
            ' Note: email poller account must have permissions to view those' \
            'shared mailboxes.',
        'inbox_filter': 'MS API filter applied to emails to narrow the list' \
            'for processing.' \
            'Reference: https://msdn.microsoft.com/en-us/office/office365/' \
            'api/complex-types-for-mail-contacts-calendar',
        'email_polling_interval': 'How often to poll emails (seconds)',
        'enable_polling': 'If checked, automatic emails will be ' \
            'automatically polled.',
        'enable_auto_processing': 'If checked, each email collected will ' \
            'be automatically processed by all registered and enabled ' \
            'actions.',
        'service_account_username': 'Username used to login to email server',
        'service_account_password': 'Password used to login to email server',
        'admin_email_addresses': 'System alerts and errors will be sent here'
    }

    label_columns = {
        'accounts_to_check': 'Get Emails From',
        'inbox_filter': 'Email Filter',
        'email_polling_interval': 'Check Email Interval',
        'enable_polling': 'Enable Automatic Email Checking',
        'enable_auto_processing': 'Enable Automatic Email Actions'}

    list_columns = [
        'accounts_to_check', 'inbox_filter',
        'email_polling_interval', 'enable_auto_processing']

    edit_fieldsets = [
        ('Account Info', {'fields': [
            'service_account_username', 'service_account_password']}),
        ('Alerts', {'fields': ['admin_email_addresses']}),
        ('Polling', {'fields': [
            'accounts_to_check', 'inbox_filter',
            'enable_polling', 'email_polling_interval']})
    ]
    show_fieldsets = [
        ('Account Info', {'fields': ['service_account_username']}),
        ('Alerts', {'fields': ['admin_email_addresses']}),
        ('Polling', {'fields': [
            'accounts_to_check', 'inbox_filter',
            'enable_polling', 'email_polling_interval']})
    ]

    def post_update(self, settings):
        if settings.enable_polling:
            from email_client import Client
            self.client = Client()
            self.client.start()
        elif 'client' in self.__dict__:
            self.client.exit()


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return render_template(
        '404.html',
        base_template=appbuilder.base_template,
        appbuilder=appbuilder), 404

db.create_all()

appbuilder.add_view(AppSettingsModelView, "Settings", icon="fa-cogs")
appbuilder.add_view(
    EmailModelView,
    "List Emails",
    icon="fa-envelope-o",
    category="Emails",
    category_icon="fa-envelope")
appbuilder.add_view_no_menu(AttachmentModelView)
appbuilder.add_view(
    ActionModelView,
    "List Actions",
    icon="fa-cogs",
    category="Actions",
    category_icon="fa-cogs")
