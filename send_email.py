from __future__ import unicode_literals

import os
import glob
import mimetypes
import smtplib

from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart

from string import Template
from collections import namedtuple

import config

COMMASPACE = ', '

EMAIL_USER = config.EMAIL_SMTP_USER
EMAIL_PWD = config.EMAIL_SMTP_PWD
EMAIL_SMTP_HOST = config.EMAIL_SMTP_HOST
EMAIL_SMTP_PORT = config.EMAIL_SMTP_PORT
EMAIL_SENDER = config.EMAIL_SENDER
EMAIL_SUBJECT = config.EMAIL_SUBJECT
TEMPLATE_FILE = config.TEMPLATE_FILE
TEMPLATE_IS_HTML = os.path.splitext(TEMPLATE_FILE)[1].upper() == '.HTML'
RECIPIENT_FILE = config.RECIPIENT_FILE
RECIPIENT_FILE_SEPARATOR = config.RECIPIENT_FILE_SEPARATOR
ATTACH_DIR = config.ATTACH_DIR

smtp = None


def connect_smtp():
    global smtp
    smtp = smtplib.SMTP_SSL(host=EMAIL_SMTP_HOST, port=EMAIL_SMTP_PORT)
    smtp.login(EMAIL_USER, EMAIL_PWD)


def disconnect_smtp():
    global smtp
    smtp.quit()


def send_smtp(email, composed):
    smtp.sendmail(email.sender, email.recipients, composed)


class Email(object):
    def __init__(self):
        self.sender = ''
        self.recipients = []
        self.subject = ''
        self.preamble = 'Automatic email\n'
        self.files = []
        self.body_plain = ''
        self.body_html = ''

    def __repr__(self):
        return '<Email sender={}, recipients={}, subject={}>'.format(
            self.sender, self.recipients, self.subject
        )

    def add_recipient(self, recipient):
        self.recipients.append(recipient)

    def add_file(self, filename):
        self.files.append(filename)


def attach_file(full_filename, to_email):
    [path, filename] = os.path.split(full_filename)

    if not os.path.isfile(full_filename):
        raise Exception('"{}" is not a file.'.format(full_filename))

    ctype, encoding = mimetypes.guess_type(path)

    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'

    maintype, subtype = ctype.split('/', 1)

    if maintype == 'text':
        fp = open(full_filename)
        msg = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'image':
        fp = open(full_filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'audio':
        fp = open(full_filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(full_filename, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        encoders.encode_base64(msg)

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    to_email.attach(msg)


def do_send_email(email):
    outer = MIMEMultipart()
    outer['Subject'] = email.subject
    outer['To'] = COMMASPACE.join(email.recipients)
    outer['From'] = email.sender
    outer.preamble = email.preamble

    if email.body_plain != '':
        outer.attach(MIMEText(email.body_plain, 'plain'))
    if email.body_html != '':
        outer.attach(MIMEText(email.body_html, 'html'))

    for fname in email.files:
        attach_file(fname, outer)

    send_smtp(email, outer.as_string())


def get_template():
    with open(TEMPLATE_FILE) as f:
        template = f.read()
    f.close()

    return Template(template)


def get_recipients():
    recipients = []
    with open(RECIPIENT_FILE) as f:
        for line in f:
            if line.strip() == '':
                continue

            line = map(lambda x: x.strip(), line.split(RECIPIENT_FILE_SEPARATOR))
            recipients.append(line)
    f.close()

    fields = recipients[0]
    Recipient = namedtuple('Recipient', ' '.join(fields))
    return [Recipient(*r) for r in recipients[1:]]


def send_email(recipient_email, subject, body, attachments):
    email = Email()
    email.sender = EMAIL_SENDER
    email.add_recipient(recipient_email)
    email.preamble = 'Automatic email\n'
    email.subject = subject
    email.files = attachments

    if TEMPLATE_IS_HTML:
        email.body_html = body
    else:
        email.body_plain = body

    do_send_email(email)


def main():
    print '>>>> Start sending emails'
    connect_smtp()

    body_template = get_template()
    subject_template = Template(EMAIL_SUBJECT)
    recipients = get_recipients()
    attachments = [x for x in glob.glob(os.path.join(ATTACH_DIR, '*.*'))]

    for r in recipients:
        print 'Send to: {}'.format(r.email)
        args = r._asdict()
        body = body_template.safe_substitute(**args)
        subject = subject_template.safe_substitute(**args)

        send_email(r.email, subject, body, attachments)

    disconnect_smtp()
    print '<<<< Finished'


if __name__ == '__main__':
    main()
