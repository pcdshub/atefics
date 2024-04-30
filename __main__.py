import smtplib, ssl
import json
import apischema
import asyncio

from atef.config import ConfigurationFile, PreparedFile
from atef.enums import Severity
import oauth2
from email.message import EmailMessage
from email.utils import make_msgid

def get_verification_token():
    f = open("./atefics/client.json", 'r')
    client_details = json.loads(f.read())
    f.close()
    client_id = client_details['web']['client_id']
    client_secret = client_details['web']['client_secret']

    token = oauth2.main(["oauth2.py","--generate_oauth2_token", 
        f"--client_id={client_id}", f"--client_secret={client_secret}"])

def refresh_token():
    f = open("./atefics/client.json", 'r')
    client_details = json.loads(f.read())
    f.close()
    client_id = client_details['web']['client_id']
    client_secret = client_details['web']['client_secret']
    refresh_token = client_details['web']['refresh_token']

    result = oauth2.main(["oauth2.py", 
        f"--client_id={client_id}", 
        f"--client_secret={client_secret}",
        f"--refresh_token={refresh_token}"])
    return result['access_token']    


def run_optics_atef():
    # load (checkout) config file of choice
    fn = './atefics/PLC-Limits-Prototype.json'
    with open(fn, 'r') as fd:
        serialized = json.load(fd)
    deser = apischema.deserialize(ConfigurationFile, serialized)

    # Prepare file for running
    file = PreparedFile.from_config(deser)

    # run checkout (comparison)
    top_level_result = asyncio.run(file.compare())

    recipients = ['nrw@slac.stanford.edu', 'lclsoptics@gmail.com']
    msg = EmailMessage()    
    msg['From'] = "lclsoptics@gmail.com"
    msg['to'] = ", ".join(recipients)
    msg['Content-Type'] = "text/plain"

    top_group = True
    content = ""

    for group in file.walk_groups():
        if top_group and top_level_result.severity == Severity.success:
            msg['Subject'] = f'{group.config.name} Valid Optics Configuration'
            content += "These Devices have been successfully validated by ATEF:\r\n"
            content += "\r\n"
            top_group = False
        elif top_group and top_level_result.severity == Severity.error:
            msg['Subject'] = f'{group.config.name} FAILED Optics Configuration'
            content += "These Devices have FAILED check out by ATEF:\r\n"
            content += "\r\n"
            top_group = False
        else:
            content += f'{group.config.name}\r\n'

    if top_level_result.severity == Severity.error:
        for comp in file.walk_comparisons():
            if comp.result.severity == Severity.error:
                content += f'{comp.identifier} had result: {comp.result}\r\n'

    msg.set_content(content)
    send_email(msg)


def send_email(msg=None):

    smtp_conn = oauth2.main(["oauth2.py", 
        f"--access_token={refresh_token()}", 
        f"--user=lclsoptics@gmail.com",
        f"--smtp_authentication"])

    smtp_conn.send_message(msg)
    smtp_conn.quit()
    return

run_optics_atef()
