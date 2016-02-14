import logging
from flask import Flask
from flask.ext.appbuilder import SQLA, AppBuilder
from app.models import AppSettings, Action

"""
 Logging configuration
"""

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object('config')
db = SQLA(app)
appbuilder = AppBuilder(app, db.session)

# Load initial data
if db.session.query(AppSettings).count() < 1:
    appsettings = AppSettings()
    db.session.add(appsettings)
    db.session.commit()

if db.session.query(Action).count() < 1:
    action = Action(name='Extract Text From Attachments')

    python_method = ''.join([
        'def action( email ):\n',
        '   from O365 import Message, Attachment\n',
        '   from textextractor import TextExtractor\n',
        '   from email_client import Client\n',
        '   import base64\n',
        '\n',
        '   client = Client()\n',
        '   response = Message()\n',
        '   sender = email.getSender()\n',
        '   if \'@root9b.com\' in sender[\'Address\'][-11:]:\n',
        '        response.setRecipients( sender )\n',
        '   else:\n',
        '       response.setRecipients( {\n',
        '           \'Address\' : \'craig.koroscil@root9b.com\',\n',
        '           \'Name\': \'Craig\'} )\n',
        '   response.setSubject(\n',
        '       \'Automatic Response: Text extracted from attachments\')\n',
        '   extractor = TextExtractor()\n',
        '   for attachment in email.attachments:\n',
        '       new_attachment = Attachment()\n',
        '       attachment_text = extractor.extract(\n',
        '           attachment.json[\'Name\'], attachment.getByteString())\n',
        '       new_attachment.setBase64(base64.b64encode(attachment_text))\n',
        '       new_attachment.setName(\n',
        '           \'%s.txt\' % attachment.json[\'Name\'])\n',
        '       response.attachments.append(new_attachment)\n',
        '   body_text = (\n',
        '       \'Do Not Reply - This is an automated response\'\n',
        '       \'\'\n',
        '       \'Original Message\n',
        '       \'-----------------------------------\'\n',
        '       \'%s\' % email.getBody())\n',
        '   response.setBody( body_text )\n',
        '   response.sendMessage()\n',
        '   client.send_email(response)\n',
        '   return True'])

    action.python_method = python_method
    db.session.add(action)
    db.session.commit()

from app import views  # noqa
