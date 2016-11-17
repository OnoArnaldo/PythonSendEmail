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
RECIPIENT_FILE = config.RECIPIENT_FILE
RECIPIENT_FILE_SEPARATOR = config.RECIPIENT_FILE_SEPARATOR
ATTACH_DIR = config.ATTACH_DIR

smtp = None


class Log(object):
    @classmethod
    def info(cls, message):
        print message


class Email(object):
    def __init__(self):
        self.sender = ''
        self.recipients = []
        self.subject = ''
        self.preamble = 'Generic usage email\n'
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


class SMTP(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.smtp = None

    def connect(self, user, password):
        Log.info('Connecting to {}:{}'.format(self.host, self.port))
        self.smtp = smtplib.SMTP_SSL(host=self.host, port=self.port)
        self.smtp.login(user, password)

    def disconnect(self):
        Log.info('Disconnecting')
        self.smtp.quit()

    def send(self, email, composed):
        self.smtp.sendmail(email.sender, email.recipients, composed)


class Sender(object):
    def __init__(self, smtp_host=EMAIL_SMTP_HOST, smtp_port=EMAIL_SMTP_PORT,
                 smtp_user=EMAIL_USER, smtp_password=EMAIL_PWD,
                 email_subject=EMAIL_SUBJECT, email_sender=EMAIL_SENDER,
                 attachment_dir=ATTACH_DIR, template_file=TEMPLATE_FILE,
                 recipients_file=RECIPIENT_FILE, recipients_file_separator=RECIPIENT_FILE_SEPARATOR):

        self.smtp = SMTP(smtp_host, smtp_port)
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

        self.email_sender = email_sender
        self.email_subject = email_subject

        self.attachment_dir = attachment_dir

        self.recipients_file = recipients_file
        self.recipients_file_separator = recipients_file_separator

        self.template_file = template_file
        self.template_is_html = os.path.splitext(template_file)[1].upper() == '.HTML'

    def get_body_template(self):
        with open(self.template_file) as f:
            template = f.read()
        f.close()

        return Template(template)

    def get_subject_template(self):
        return Template(self.email_subject)

    def get_recipients(self):
        recipients = []
        with open(self.recipients_file) as f:
            for line in f:
                if line.strip() == '':
                    continue

                line = map(lambda x: x.strip(), line.split(self.recipients_file_separator))
                recipients.append(line)
        f.close()

        fields = recipients[0]
        Recipient = namedtuple('Recipient', ' '.join(fields))
        return [Recipient(*r) for r in recipients[1:]]

    def get_attachments(self):
        return [x for x in glob.glob(os.path.join(self.attachment_dir, '*.*'))]

    def attach_file(self, full_filename, to_email):
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

    def do_send_email(self, email):
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
            self.attach_file(fname, outer)

        self.smtp.send(email, outer.as_string())

    def send_email(self, recipient_email, subject, body, attachments):
        email = Email()
        email.sender = self.email_sender
        email.add_recipient(recipient_email)
        email.preamble = 'Automatic email\n'
        email.subject = subject
        email.files = attachments

        if self.template_is_html:
            email.body_html = body
        else:
            email.body_plain = body

        self.do_send_email(email)

    def run(self):
        Log.info('>>> Start sending emails')
        self.smtp.connect(self.smtp_user, self.smtp_password)

        body_template = self.get_body_template()
        subject_template = self.get_subject_template()
        recipients = self.get_recipients()
        attachments = self.get_attachments()

        for r in recipients:
            Log.info('Send to: {}'.format(r.email))
            args = r._asdict()
            body = body_template.safe_substitute(**args)
            subject = subject_template.safe_substitute(**args)

            self.send_email(r.email, subject, body, attachments)

        self.smtp.disconnect()
        Log.info('<<<< Finished')


def main():
    sender = Sender()
    sender.run()


if __name__ == '__main__':
    main()
