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
import unidecode
from flask import jsonify
import json

root = environ.Path(__file__)
env = environ.Env(DEBUG=(bool, False), )
environ.Env.read_env()

sg = sendgrid.SendGridAPIClient(apikey=env('SENDGRID_API_KEY'))

app = Flask(__name__)
app.secret_key = env('SECRET_KEY')
csrf = CSRFProtect(app)

log = open('log', 'a')


class EssayForm(Form):
    password = PasswordField('password', [
        validators.DataRequired(),
        validators.Regexp(env('ESSAY_PASSWORD'), 0, 'wrong password')
    ])
    essay = TextAreaField('essay', widget=TextArea())


def send_email(to_email, from_name):

    from_name = unidecode.unidecode(from_name)
    to_email = unidecode.unidecode(to_email)
    from_email = Email(email=from_name.replace(' ', '.') + '@howdoesitfeeltobeafiction.org')
    to_email = Email(email=to_email)
    subject_english = "How does it feel to be a fiction?"
    # subject_spanish = "¿Cómo se siente ser una ficción?"
    body_english = '''This is an invitation to participate in a 
    performance—of which you are now the 
    audience.  This performance is textual and takes place via email 
    dissemination.  To participate in the work, 
    click <a href="https://howdoesitfeeltobeafiction.org/">
    https://www.howdoesitfeeltobeafiction.org/</a>.  
    The email address you received this from was generated as a result of this 
    performance.  
    It repeats the name of the person who last participated and thus marks the 
    path of 
    this work's viral circulation.  
    If you reply to this email, your message will be routed to the author 
    of the 
    performance.'''
    footer_english = '''\n\n This piece by Aliza Shvarts is part of the&nbsp;<a href="https://www.artidea.org/event/2018/3419" target="_blank">2018 International Festival of Arts &amp; Ideas</a>&nbsp;(presented by Nasty Women CT) as well as the exhibition&nbsp;<a href="https://artspacenewhaven.org/exhibitions/aliza-shvarts-off-scene/" target="_blank">"Off Scene"</a>&nbsp;on view at Artspace, New Haven, CT until <span class="aBn" data-term="goog_1043318215" tabindex="0"><span class="aQJ">June 30</span></span>.'''
    content = Content("text/html",
                      body_english + "<br><br><p> </p>" + footer_english)
    mail = Mail(from_email, subject_english, to_email, content)
    response = None
    try:
        response = sg.client.mail.send.post(request_body=mail.get())
    except Exception as e:
        log.write(str(mail.get()))
        log.write(str(e.body))
        log.write(str(e))
    if response:
        log.write(str(response.status_code))
        log.write(str(response.body))
        log.write(str(response.headers))
    log.flush()


def get_gmail_contacts(access_token):
    credentials = AccessTokenCredentials(access_token, 'my-user-agent/1.0')
    http = httplib2.Http()
    http = credentials.authorize(http)
    resp, content = http.request(
            'https://www.google.com/m8/feeds/contacts/default/full?max-results=1000')
    soup = BeautifulSoup(content, 'html.parser')
    return map(lambda x: x.attrs['address'],
               soup.find_all(attrs={'address': True}))


@app.route("/api/email", methods=['GET'])
def root():
    from_name = request.args.get('from_name')
    access_token = request.args.get('access_token')
    if from_name and access_token:
        email_contacts = list(get_gmail_contacts(access_token))
        print(email_contacts)
        log.write(str(email_contacts))
        for email in email_contacts:
            send_email(email, from_name)
    return make_response("aok")


@app.route("/api/change_essay", methods=['POST', 'GET'])
def change_essay():
    form = EssayForm(request.form)
    if request.method == 'POST' and form.validate():
        essay = form.essay
        with open('essay.html', 'w') as essay_html:
            essay_html.write(essay.data)
        return redirect('/')
    with open('essay.html', 'r') as essay_html:
        essay = essay_html.read()
        form.essay.data = essay
        return render_template('essay_form.html', form=form,
                               essay=essay)


@app.route("/api/essay", methods=['GET'])
def essay_get():
    return jsonify([open('first_essay.html').read(), open('second_essay.html').read(), open('essay.html').read()])
