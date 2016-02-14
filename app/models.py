from flask import (
    Markup, url_for, redirect)
from flask.ext.appbuilder import Model
from flask.ext.appbuilder.models.mixins import FileColumn
from flask.ext.appbuilder.models.decorators import renders
from flask.ext.appbuilder.actions import action
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Text, DateTime, Table, Boolean)
from sqlalchemy.orm import relationship


class EmailAddress(Model):
    id = Column(Integer, primary_key=True)
    address = Column(String(64), nullable=False)
    name = Column(String(64), nullable=True)

    email_id = Column(Integer, ForeignKey('email.id'))
    email = relationship("Email")

    def __repr__(self):
        return '%s' % (self.address)


class Attachment(Model):
    id = Column(Integer, primary_key=True)
    filename = Column(String(128), nullable=False)
    file = Column(FileColumn, nullable=False)

    email_id = Column(Integer, ForeignKey('email.id'))
    email = relationship("Email", back_populates="attachments")

    def __repr__(self):
        return self.filename


assoc_to_emailaddresses_email = Table(
    'to_emailaddresses_email', Model.metadata,
    Column('emailaddress_id', Integer, ForeignKey('email_address.id')),
    Column('email_id', Integer, ForeignKey('email.id'))
)
assoc_cc_emailaddresses_email = Table(
    'cc_emailaddresses_email', Model.metadata,
    Column('emailaddress_id', Integer, ForeignKey('email_address.id')),
    Column('email_id', Integer, ForeignKey('email.id'))
)
assoc_bcc_emailaddresses_email = Table(
    'bcc_emailaddresses_email', Model.metadata,
    Column('emailaddress_id', Integer, ForeignKey('email_address.id')),
    Column('email_id', Integer, ForeignKey('email.id'))
)
assoc_reply_to_emailaddresses_email = Table(
    'reply_to_emailaddresses_email', Model.metadata,
    Column('emailaddress_id', Integer, ForeignKey('email_address.id')),
    Column('email_id', Integer, ForeignKey('email.id'))
)


class Email(Model):
    id = Column(Integer, primary_key=True)
    read_receipt_requested = Column(Boolean, default=False)
    from_emailaddress = relationship(
        "EmailAddress", uselist=False, back_populates="email")
    #from_emailaddress = relationship("EmailAddress", back_populates="email")
    sender = relationship(
        "EmailAddress", uselist=False, back_populates="email")
    #sender = relationship("EmailAddress", back_populates="email")
    to_recipients = relationship(
        'EmailAddress', single_parent=True,
        secondary=assoc_to_emailaddresses_email)
    cc_recipients = relationship(
        'EmailAddress', single_parent=True,
        secondary=assoc_cc_emailaddresses_email)
    bcc_recipients = relationship(
        'EmailAddress', single_parent=True,
        secondary=assoc_bcc_emailaddresses_email)
    reply_to_recipients = relationship(
        'EmailAddress', single_parent=True,
        secondary=assoc_reply_to_emailaddresses_email)
    importance = Column(String(64), nullable=True)
    subject = Column(Text, nullable=True)
    body_preview = Column(Text, nullable=True)
    body_content_type = Column(String(64), nullable=True)
    body = Column(Text, nullable=True)
    has_attachments = Column(Boolean, default=False)
    attachments = relationship("Attachment", single_parent=True,)
    created = Column(DateTime, nullable=True)
    sent = Column(DateTime, nullable=True)
    received = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)

    analyst_notes = Column(Text, nullable=True)

    @renders('attachments')
    def attachments_downloadable(self):
        if self.attachments:
            links = []
            for attachment in self.attachments:
                url = url_for(
                    'AttachmentModelView.download',
                    pk=str(attachment.id),
                    filename=str(attachment.filename))
                links.append(
                    '<a href="' + url + '">' + attachment.filename + '</a>')
            return Markup(",".join(links))

    @action("muldelete", "Delete", "Delete all Really?", "fa-trash")
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())

    def __repr__(self):
        return 'From:%s, To:%s, Subject: %s' % (
            self.from_emailaddress, self.to_recipients, self.subject)


class Action(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    enabled = Column(Boolean, default=True)
    run_automatically = Column(Boolean, default=True)

    default_python = "".join([
        "def action( email ):\n\n",
        "   # Do something with the email\n\n",
        "   return True"])
    python_method = Column(Text, default=default_python, nullable=False)


class AppSettings(Model):
    id = Column(Integer, primary_key=True)
    service_account_username = Column(
        String(64), default='username@domain.com', nullable=False)
    service_account_password = Column(
        String(64), default='password', nullable=False)
    enable_auto_processing = Column(Boolean, default=True)
    admin_email_addresses = Column(
        String(128), default='user@domain.com', nullable=False)
    accounts_to_check = Column(
        String(128),
        default='checkme@domain.com',
        nullable=False)
    enable_polling = Column(Boolean, default=False)
    email_polling_interval = Column(Integer, default=60, nullable=False)
    inbox_filter = Column(
        String(128),
        default='IsRead eq false and HasAttachments eq true',
        nullable=False)


class Log(Model):
    id = Column(Integer, primary_key=True)
