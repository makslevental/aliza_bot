from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
from urllib.parse import parse_qs, urlsplit
from oauth2client.client import AccessTokenCredentials
import httplib2
import sendgrid
from sendgrid.helpers.mail import *
from bs4 import BeautifulSoup
import environ

root = environ.Path(__file__)
env = environ.Env(DEBUG=(bool, False), )
environ.Env.read_env()

sg = sendgrid.SendGridAPIClient(apikey=env('SENDGRID_API_KEY'))


def send_email(to_email, from_name):
    from_email = Email(
        email=from_name.replace(' ', '.') + '@howdoesitfeeltobeafiction.org')
    to_email = Email(email=to_email)
    subject = "How does it feel to be a fiction?"
    content = Content("text/html", '''This is an invitation to participate in a 
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
    performance.''')
    mail = Mail(from_email, subject, to_email, content)
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


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        params = parse_qs(urlsplit(self.path).query)
        if params and 'from_name' in params and 'access_token' in params:
            email_contacts = get_gmail_contacts(params['access_token'])
            for email in email_contacts:
                send_email(email, params['from_name'])

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


httpd = HTTPServer(('localhost', 1443), Handler)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='server.pem',
                               server_side=True)
# httpd.serve_forever()
# print(list(get_gmail_contacts(
#     'ya29.GlvJBN9Alr03TltXRHfRzoLrFPeTmXALk_CwAQWw_dfGwM3_LFT25ILo_orw8aA34OzXVdu1cYnx4vGsFO1Is4Jx2TMtxxTa4yD67w-naa89xjMcma_yCvvdo0So')))
# send_email('maksim@preview.tech', 'max bob')
