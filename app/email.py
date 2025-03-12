from app.celery import celery
from app.extensions import mail
from app.leave.models import Leave
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
def send_leave_request_status_update_email(self, leave_id):
    osportal_name = get_settings_value('osportal_name')
    try:
        leave = Leave.query.get(leave_id)
        send_email((f'Update on Your {leave.ltype} Request - {osportal_name}'),
                   recipients=[leave.user.email],
                   #text_body=render_template('email/password_reset.txt',
                   #                          user=user, token=token),
                   html_body=render_template('email/leave_request_status_update.html', leave=leave))
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


@celery.task(bind=True)
def send_leave_request_email(self, leave_id):
    #token = user.serialize_token()
    osportal_name = get_settings_value('osportal_name')
    try:
        leave = Leave.query.get(leave_id)
        send_email((f'{leave.ltype} Request - {leave.user} - {osportal_name}'),
                   recipients=[leave.user.authoriser.email],
                   #text_body=render_template('email/password_reset.txt',
                   #                          user=user, token=token),
                   html_body=render_template('email/leave_request.html', leave=leave))
    except Exception as e:
        #logger.error('exception raised, it would be retry after 5 seconds')
        raise self.retry(exc=e, countdown=5)
    else:
        return None


@celery.task(bind=True)
def send_password_reset_email(self, user):
    token = user.serialize_token()
    osportal_name = get_settings_value('osportal_name')
    try:
        send_email((f'Reset Your Password - {osportal_name}'),
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
    osportal_name = get_settings_value('osportal_name')
    send_email((f'Welcome to {osportal_name}'),
               recipients=[user.email],
               html_body=render_template('email/account_creation.html',
                                         user=user, token=token))
    return None
