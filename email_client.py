#!/usr/bin/env python

import threading
import logging
import fcntl
import sys
import imp

from datetime import datetime
from app import db
from O365 import Message, Inbox

from app.models import (
    Email, EmailAddress, Attachment, Action, AppSettings)

logging.basicConfig(filename='o365.log', level=logging.DEBUG)
log = logging.getLogger(__name__)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


def lockFile(lockfile):
    """Attempt to create lock file or fail if already locked"""
    fp = open(lockfile, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True


class Client(object):
    """
    Office 365 email client
    """

    def __init__(self):
        """Constructor"""
        self.main_thread = None
        self.main_thread_stop = threading.Event()
        self.settings = None
        self._reload_settings()
        self.auth = (
            self.settings.service_account_username,
            self.settings.service_account_password)

    def _reload_settings(self):
        """Updates local settings from user specified settings in database"""
        self.settings = db.session.query(AppSettings).first()
        if not self.settings.enable_polling:
            self.main_thread_stop.set()
        return self.settings

    def send_email(self, message):
        """Adds authentication settings to a
        Message and transmits the message"""
        log.debug("Sending message: %s" % str(message))
        message = message
        message.auth = self.auth
        message.sendMessage()

    def report_error(self, error_message):
        """Send a specified message to the admininistrator
        via email (as specified in the settings)"""
        message = Message(auth=self.auth)
        message.setSubject('!! Email Processor Error !!')
        message.setBody(str(error_message))
        message.setRecipients(str(self.settings.admin_email_addresses))
        message.sendMessage()

    def check_for_messages(self):
        """
        Get all emails from mailboxes (specified in settings),
        store each message in the database, then pass each message
        to the registered Actions.
        """

        for user in self.settings.accounts_to_check.split(','):

            try:
                inbox = Inbox(auth=self.auth, getNow=False)
                inbox.inbox_url = 'https://outlook.office365.com/api/v1.0/'\
                    'Users(\'%s\')/Messages' % user
                inbox.setFilter(self.settings.inbox_filter)

                try:
                    inbox.getMessages()
                except ValueError:
                    log.debug("No valid json object received")

                log.debug(
                    "number of messages received: %s" %
                    len(inbox.messages))

                log.debug("messages: {0}".format(len(inbox.messages)))
                for message in inbox.messages:
                    self._process_message(message)
            except Exception:
                error = sys.exc_info()
                log.error(error)
                self.report_error(error)
                pass

    def _extract_email_info(self, message):
        """Copy email contents into Email object for database storage"""
        log.debug("Extracting email contents for database")
        email = Email()
        email.read_receipt_requested = message.json['IsReadReceiptRequested']
        email.from_emailaddress = EmailAddress(
            address=message.json['From']['EmailAddress']['Address'],
            name=message.json['From']['EmailAddress']['Name'])
        email.sender = EmailAddress(
            address=message.json['Sender']['EmailAddress']['Address'],
            name=message.json['Sender']['EmailAddress']['Name'])
        to_recipients = [EmailAddress(
            address=recipient['EmailAddress']['Address'],
            name=recipient['EmailAddress']['Name'])
            for recipient in message.json['ToRecipients']]
        for recipient in to_recipients:
            email.to_recipients.append(recipient)
        cc_recipients = [EmailAddress(
            address=recipient['EmailAddress']['Address'],
            name=recipient['EmailAddress']['Name'])
            for recipient in message.json['CcRecipients']]
        for recipient in cc_recipients:
            email.cc_recipients.append(recipient)
        bcc_recipients = [EmailAddress(
            address=recipient['EmailAddress']['Address'],
            name=recipient['EmailAddress']['Name'])
            for recipient in message.json['BccRecipients']]
        for recipient in bcc_recipients:
            email.bcc_recipients.append(recipient)
        reply_to_recipients = [EmailAddress(
            address=recipient['EmailAddress']['Address'],
            name=recipient['EmailAddress']['Name'])
            for recipient in message.json['ReplyTo']]
        for recipient in reply_to_recipients:
            email.reply_to_recipients.append(recipient)
        email.importance = message.json['Importance']
        email.subject = message.json['Subject'].encode('ascii', 'ignore')
        email.body_content_type = message.json['Body']['ContentType']
        email.body = message.json['Body']['Content'].encode('ascii', 'ignore')
        email.body_preview = message.json['BodyPreview'].encode(
            'ascii', 'ignore')
        email.created = datetime.strptime(
            message.json['DateTimeCreated'], '%Y-%m-%dT%H:%M:%SZ')
            # 2016-02-11T14:37:27Z
        email.sent = datetime.strptime(
            message.json['DateTimeSent'], '%Y-%m-%dT%H:%M:%SZ')
        email.received = datetime.strptime(
            message.json['DateTimeReceived'], '%Y-%m-%dT%H:%M:%SZ')
        email.last_modified = datetime.strptime(
            message.json['DateTimeLastModified'], '%Y-%m-%dT%H:%M:%SZ')
        email.has_attachments = message.hasAttachments
        if message.hasAttachments:
            for attachment in message.attachments:
                attachment_obj = Attachment(
                    filename=attachment.json['Name'],
                    file=attachment.json['ContentBytes'])
                email.attachments.append(attachment_obj)
        db.session.add(email)
        db.session.commit()

    def _process_message(self, message):
        """Fetch message attachments and then pass the message
        with attachments to all registered Actions."""

        log.debug('Fetching attachments for "%s"' % message)

        message.fetchAttachments()

        self._extract_email_info(message)

        if message.hasAttachments:
            for attachment in message.attachments:
                self._process_attachment(attachment)

        auto_actions = db.session.query(Action).filter(
            Action.enabled == True,
            Action.run_automatically == True).all()  # noqa

        if auto_actions:
            for action in auto_actions:

                log.debug("Running Action: %s" % action.name)

                # Build a module with a method from a string so we can execute
                action_module = imp.new_module('action_module')
                exec action.python_method in action_module.__dict__

                # TODO: Add wrapper for exception handling
                # to email admins with error
                thread = threading.Thread(
                    target=action_module.action, args=(message,))
                thread.daemon = True
                thread.start()
                thread.join()
        #message.markAsRead()

        return True

    def _process_attachment(self, attachment):
        """Process an email attachment"""
        log.debug('Processing attachment "%s"' % attachment)
        file = attachment.getByteString()
        if not file:
            log.debug(
                "Something went wrong with decoding attachment: {0} {1}"
                .format(attachment.json['Name'], str(attachment))
            )
            return False
        return True

    def _run(self):
        """Main lopp to check for and process
        messages at a specified interval"""
        if not lockFile(".lock.emailprocessor"):
            log.debug("Exiting. Client already running (lock file)")
            sys.exit(0)

        while not self.main_thread_stop.is_set():
            self.settings = self._reload_settings()
            self.check_for_messages()
            self.main_thread_stop.wait(self.settings.email_polling_interval)

    def start(self):
        """Start automatically checking messages
        at specified interval forever"""
        log.debug("Starting main loop")
        self.main_thread = threading.Thread(target=self._run)
        self.main_thread.start()

    def stop(self):
        """Stop automatically checking messages"""
        log.debug("Stopping main loop")
        self.main_thread_stop.set()
        self.main_thread.join()

if __name__ == "__main__":
    client = Client()
    client.auth = ('username', 'password')

    message = Message()
    message.setSubject('Test')
    message.setBody('This is a test message')
    message.setRecipients([{'EmailAddress': {
        'Name': 'Craig', 'Address': 'craig.koroscil@root9b.com'}}])
    client.send_email(message)

    #client._run()

