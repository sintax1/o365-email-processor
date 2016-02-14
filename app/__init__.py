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
        'def action( email ):',
        '   from O365 import Message, Attachment',
        '   from textextractor import TextExtractor',
        '   from email_client import Client',
        '   import base64',
        '',
        '   client = Client()',
        '   response = Message()',
        '   sender = email.getSender()',
        '   if \'@<domain>.com\' in sender[\'Address\'][-11:]:',
        '        response.setRecipients( sender )',
        '   else:',
        '       response.setRecipients( {',
        '           \'Address\' : \'craig.koroscil@<domain>.com\',',
        '           \'Name\': \'Craig\'} )',
        '   response.setSubject(',
        '       \'Automatic Response: Text extracted from attachments\')',
        '   extractor = TextExtractor()',
        '   for attachment in email.attachments:',
        '       new_attachment = Attachment()',
        '       attachment_text = extractor.extract(',
        '           attachment.json[\'Name\'], attachment.getByteString())',
        '       new_attachment.setBase64(base64.b64encode(attachment_text))',
        '       new_attachment.setName(',
        '           \'%s.txt\' % attachment.json[\'Name\'])',
        '       response.attachments.append(new_attachment)',
        '   body_text = (',
        '       \'Do Not Reply - This is an automated response\'',
        '       \'\'',
        '       \'Original Message',
        '       \'-----------------------------------\'',
        '       \'%s\' % email.getBody())',
        '   response.setBody( body_text )',
        '   response.sendMessage()',
        '   client.send_email(response)',
        '   return True'])

    action.python_method = python_method
    db.session.add(action)
    db.session.commit()

from app import views  # noqa
