# coding=utf-8
from oauth2client.client import AccessTokenCredentials
import httplib2
import sendgrid
from sendgrid.helpers.mail import *
from bs4 import BeautifulSoup
import environ
from flask import Flask, request, render_template, redirect, make_response
from wtforms import Form, TextAreaField, PasswordField, validators
from wtforms.widgets import TextArea
from flask_wtf.csrf import CSRFProtect

root = environ.Path(__file__)
env = environ.Env(DEBUG=(bool, False), )
environ.Env.read_env()

sg = sendgrid.SendGridAPIClient(apikey=env('SENDGRID_API_KEY'))

app = Flask(__name__)
app.secret_key = env('SECRET_KEY')
csrf = CSRFProtect(app)


class EssayForm(Form):
    password = PasswordField('password', [
        validators.DataRequired(),
        validators.Regexp(env('ESSAY_PASSWORD'), 0,'wrong password')
    ])
    essay = TextAreaField('essay', widget=TextArea())


def send_email(to_email, from_name):
    from_email = Email(
        email=from_name.replace(' ', '.') + '@howdoesitfeeltobeafiction.org')
    to_email = Email(email=to_email)
    subject_english = "How does it feel to be a fiction?"
    subject_spanish = "¿Cómo se siente ser una ficción?"
    body_english = '''This is an invitation to participate in a 
    performance—of which you are now the 
    audience.  This performance is textual and takes place via email 
    dissemination.  To participate in the work, 
    click <a href="https://www.howdoesitfeeltobeafiction.org/">
    https://www.howdoesitfeeltobeafiction.org/</a>.  
    The email address you received this from was generated as a result of this 
    performance.  
    It repeats the name of the person who last participated and thus marks the 
    path of 
    this work's viral circulation.  
    If you reply to this email, your message will be routed to the author 
    of the 
    performance.'''
    body_spanish = '''Esta es una invitación a participar de un performance del cual Ud. es, ahora, la
    audiencia.  Se trata de un performance textual que ocurre a través de la
    diseminación en línea de correos electrónicos.  Para participar, visite
    <a href="https://www.howdoesitfeeltobeafiction.org/">
    https://www.howdoesitfeeltobeafiction.org/</a>.  La dirección que le envía este correo
    se generó como resultado de este performance y repite el nombre de la persona
    que participó más recientemente del proyecto.  Como consecuencia, marca el
    camino de circulación viral de la obra.  Si Ud. responde a este correo, su
    mensaje lo recibirá el autor del performance y no la persona cuyo nombre
    aparece en esta dirección de correo.'''
    content = Content("text/html", body_spanish)
    mail = Mail(from_email, subject_english, to_email, content)
    mail = Mail(from_email, subject, to_email, content)
    if env('DEBUG'):
        print(mail)
    try:
        response = sg.client.mail.send.post(request_body=mail.get())
    except Exception as e:
        print(mail.get())
        print(e.body)
        print(str(e))
    if env('DEBUG'):
        print(response.status_code)
        print(response.body)
        print(response.headers)


def get_gmail_contacts(access_token):
    credentials = AccessTokenCredentials(access_token, 'my-user-agent/1.0')
    http = httplib2.Http()
    http = credentials.authorize(http)
    resp, content = http.request(
        'https://www.google.com/m8/feeds/contacts/default/full?max-results=10')
    soup = BeautifulSoup(content, 'html.parser')
    return map(lambda x: x.attrs['address'],
               soup.find_all(attrs={'address': True}))


@app.route("/api/email", methods=['GET'])
def root():
    from_name = request.args.get('from_name')
    access_token = request.args.get('access_token')
    if from_name and access_token:
        email_contacts = get_gmail_contacts(access_token)
        for email in email_contacts:
            send_email(email, from_name)
    return make_response("")


@app.route("/api/change_essay", methods=['POST', 'GET'])
def change_essay():
    form = EssayForm(request.form)
    if request.method == 'POST' and form.validate():
        essay = form.essay
        with open('essay.html', 'w') as essay_html:
            essay_html.write(essay.data)
        return redirect('/')
    with open('essay.html', 'r') as essay_html:
        print(form.errors)
        return render_template('essay_form.html', form=form,
                               essay=essay_html.read())


@app.route("/api/essay", methods=['GET'])
def essay_get():
    return open('essay.html').read()

