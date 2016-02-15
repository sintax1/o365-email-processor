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

    python_method = '\n'.join([
        'def action(email):',
        '    from O365 import (Message, Attachment)',
        '    from textextractor import TextExtractor',
        '    from email_client import Client',
        '    import base64',
        '    import html2text',
        '',
        '    print email.json',
        '    client = Client()',
        '    response = Message()',
        '    sender = email.getSender()',
        '    sender_name = sender[\'EmailAddress\'][\'Name\']',
        '    sender_email = sender[\'EmailAddress\'][\'Address\']',
        '    recipients = email.json[\'ToRecipients\']',
        '    recipients_str = ",".join(',
        '        ["[%s, <%s>]" % (',
        '            e[\'EmailAddress\'][\'Name\'],',
        '            e[\'EmailAddress\'][\'Address\']) for e in recipients])',
        '    subject = email.getSubject()',
        #'    if \'@root9b.com\' in sender_email[-11:]:',
        #'        # return to sender if internal email', 
        #'        response.setRecipients(sender)',
        #'    else:',
        # TODO: Fix recipient here. Who should processed messages go to?
        # Be careful not to create a mail loop!
        '    response.setRecipients({\'EmailAddress\': {',
        '        \'Address\' : \'craig.koroscil@root9b.com\',',
        '        \'Name\': \'Craig\'}})',
        '    response.setSubject("%s /processed/" % subject)',
        '    extractor = TextExtractor()',
        '',
        '    # Extract text from attachments',
        '    for attachment in email.attachments:',
        '        new_attachment = Attachment()',
        '        clean_name, clean_content = extractor.extract(',
        '            attachment.json[\'Name\'], attachment.getByteString())',
        '        try:',
        '            new_attachment.setBase64(',
        '                base64.b64encode(clean_content))',
        '        except NameError:',
        '            # Workaround for O365 module bug',
        '            pass',
        '        new_attachment.setName(clean_name)',
        '        response.attachments.append(new_attachment)',
        '',
        '    # Extract text from email body',
        '    if \'html\' in email.json[\'Body\'][\'ContentType\'].lower():',
        '        original_body = html2text.html2text(email.getBody())',
        '    else:',
        '        original_body = email.getBody()',
        '    body_text = """Do Not Reply - This is an automated message',
        '-----------------------------------',
        'This message and all pdf, doc, and odt attachments have been \
processed by an automated text extractor',
        '',
        '------------------ Details -------------------',
        'From: %s, <%s>',
        'To: %s',
        'Subject: %s',
        '',
        '------------ Originial Message ---------------',
        '%s""" % (',
        'sender_name, sender_email, recipients_str, subject, original_body)',
        '    response.setBody(body_text)',
        '    client.send_email(response)',
        '    return True'])
    # TODO: set ReplyTo as original sender. Not supported is O365 module

    action.python_method = python_method
    db.session.add(action)
    db.session.commit()

from app import views  # noqa
