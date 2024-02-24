from app.celery import celery
from app.extensions import mail
from app.event.models import Event
from datetime import datetime
import email
from email.mime.image import MIMEImage
from flask import render_template, url_for, current_app
from flask_mail import Message
from os.path import join
from app.providers import SMTPEmailProvider, get_settings_value



def test_email(obj_id):
    EmailProvider = SMTPEmailProvider()
    return EmailProvider.test_smtp_connection(obj_id)


@celery.task(bind=True)
def send_alert_email(self, subject, html_body, sync=True):
    EmailProvider = SMTPEmailProvider()
    if EmailProvider is None:
        return False, "No mail settings configured"
    email = get_settings_value('alert_email')
    if email is None:
        return False, "No mail settings configured"
    try:
        EmailProvider.sendmail(email.id, [email.email], html_body, subject)
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


def send_email(subject, recipients, html_body,
               attachments=None, sync=True):
    #msg = Message(subject, sender=sender, recipients=recipients)
    ##msg.body = text_body
    #msg.html = html_body
    #msg.attach(*attachments, content_type='image/gif', data=open(*attachments, 'rb').read(), headers=[('Content-ID', '<image1>')])
    # send mail
    ##mail.send(msg)
    EmailProvider = SMTPEmailProvider()
    if EmailProvider is None:
        return False, "No mail settings configured"
    email = get_settings_value('system_email')
    return EmailProvider.sendmail(email.id, recipients, html_body, subject)


@celery.task(bind=True)
def send_event_request_status_update_email(self, event_id):
    #token = user.serialize_token()
    try:
        event = Event.query.get(event_id)
        send_email(('Update on Your Request'),
                   recipients=[event.user.email],
                   #text_body=render_template('email/password_reset.txt',
                   #                          user=user, token=token),
                   html_body=render_template('email/event_request_status_update.html', event=event))
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


@celery.task(bind=True)
def send_event_request_email(self, event_id):
    #token = user.serialize_token()
    try:
        event = Event.query.get(event_id)
        send_email(('Event Request'),
                   recipients=[event.user.authoriser.email],
                   #text_body=render_template('email/password_reset.txt',
                   #                          user=user, token=token),
                   html_body=render_template('email/event_request.html', event=event))
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


@celery.task(bind=True)
def send_password_reset_email(self, user):
    token = user.serialize_token()
    try:
        send_email(('Reset Your Password'),
                   recipients=[user.email],
                   #text_body=render_template('email/password_reset.txt',
                   #                          user=user, token=token),
                   html_body=render_template('email/password_reset.html',
                                             user=user, token=token))
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


@celery.task()
def send_activation_email(user):
    token = user.serialize_token()
    send_email(('Welcome to osPortal'),
               recipients=[user.email],
               html_body=render_template('email/account_creation.html',
                                         user=user, token=token))
    return None
