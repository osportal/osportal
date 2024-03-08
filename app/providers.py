import smtplib
from app.admin.models import Settings, Email
from flask import current_app
from email.message import EmailMessage
from email.utils import formataddr
from socket import timeout
from unittest import TestCase


def get_email(obj_id):
    with current_app.app_context():
        email = Email.query.get_or_404(obj_id)
        return email


def get_settings_value(attr):
    with current_app.app_context():
        settings = Settings.query.first_or_404()
        return getattr(settings, attr)


class SMTPEmailProvider(TestCase):
    def get_smtp_data(self, obj_id):
        email = get_email(obj_id)
        data = {
            "host": email.server,
            "port": email.port,
            "username": email.username,
            "password": email.password,
            "SSL": email.ssl,
            "STARTTLS": email.starttls,
            "auth": email.auth,
            "sender": email.email
                }
        return data

    def sendmail(self, email_id, addr, text, subject):
        try:
            data = self.get_smtp_data(email_id)
            smtp = get_smtp(**data)

            msg = EmailMessage()
            msg.set_content(text, subtype='html')

            msg["Subject"] = subject
            msg["From"] = data['sender']
            msg["To"] = addr

            resp = smtp.send_message(msg, from_addr=data['sender'])

            smtp.quit()
            return True, "Email sent"
        except smtplib.SMTPException as e:
            return False, str(e)
        except timeout:
            return False, "SMTP server connection timed out"
        except Exception as e:
            return False, str(e)

    def test_smtp_connection(self, obj_id):
        try:
            data = self.get_smtp_data(obj_id)
            smtp = get_smtp(**data)
        except Exception as e:
            return str(e)

        # check we have an open socket
        #self.assertIsNotNone(smtp.sock)
        try:
            smtp.sock
        except Exception as e:
            return str(e)

        #self.assertEqual(smtp.noop(), (250, b'2.0.0 Ok'))
        try:
            ok_status = smtp.noop()
        except Exception as e:
            return str(e)

        # assert disconnected
        smtp.quit()
        #self.assertEqual(smtp.quit(), (221, '2.0.0 Service closing transmission channel'))
        self.assertIsNone(smtp.sock)

        return str(ok_status)


def get_smtp(host, port, username=None, password=None, STARTTLS=None, SSL=None, auth=None, sender=None):
    smtp = smtplib.SMTP(host, port, timeout=10)

    if SSL:
        smtp = smtplib.SMTP_SSL(host, port, timeout=10)

    if STARTTLS:
        smtp.starttls()

    if auth:
        try:
            smtp.login(username, password)
        except Exception as e:
            raise Exception(f'SMTP login issue - check server credentials. {e}')
    return smtp
