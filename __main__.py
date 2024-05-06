import sys, os.path, hashlib
import smtplib, ssl
import json
import apischema
import asyncio

from atef.config import ConfigurationFile, PreparedFile
from atef.enums import Severity
import oauth2
from email.message import EmailMessage
from email.utils import make_msgid
import optparse

client_id_path = "/reg/g/pcds/epics-dev/nrw/ATEF/atefics/client.json"

"""Performs an ATEF check given a config file and sends a corresponding
email to a list of recepients. 

"""
devices = ['SP1K1 MONO', 'MR1K1 BEND', 'MR2K2 FLAT', 'MR3K2 KBH']

def FilePathUtil(config_file):
    if os.path.isfile(config_file):
        return config_file
    elif os.path.isfile("./atefics/checkouts/" + config_file):
        return "./atefics/checkouts/" + config_file
    else:
        print(f"{config_file} does not exist")
        sys.exit(-1)

def RequireOptions(options, *args):
  missing = [arg for arg in args if getattr(options, arg) is None]
  if missing:
    print('Missing options: %s' % ' '.join(missing))
    sys.exit(-1)


def SetupOptionParser():
    parser = optparse.OptionParser(usage=__doc__)
    parser.add_option('--run_atefics',
                    action='store_true',
                    dest="run_atefics",
                    help='run an atef check on a configuratin file')
    parser.add_option('--config_file',
                    dest='config_file',
                    help='absolute path or filename in checkouts')
    parser.add_option('--hash_checkout',
                    action='store_true',
                    help="print the hash of config file")
    parser.add_option('--get_verification_token',
                    action='store_true',
                    help="get a new refresh token")
    return parser

def get_verification_token():
    with open(client_id_path, 'r') as fd:
        client_details = json.loads(fd.read())
    client_id = client_details['web']['client_id']
    client_secret = client_details['web']['client_secret']

    token = oauth2.main(["oauth2.py","--generate_oauth2_token", 
        f"--client_id={client_id}", f"--client_secret={client_secret}"])
    return token

def refresh_token():
    with open(client_id_path, 'r') as fd:
        client_details = json.loads(fd.read())
    client_id = client_details['web']['client_id']
    client_secret = client_details['web']['client_secret']
    refresh_token = client_details['web']['refresh_token']

    result = oauth2.main(["oauth2.py", 
        f"--client_id={client_id}", 
        f"--client_secret={client_secret}",
        f"--refresh_token={refresh_token}"])
    return result['access_token']    


def run_optics_atef(config_file):
    fn = FilePathUtil(config_file)

    recipients = ['nrw@slac.stanford.edu', 'awallace@slac.stanford.edu', 'aaprinz@slac.stanford.edu']
    msg = EmailMessage()    
    msg['From'] = "lclsoptics@gmail.com"
    msg['to'] = ", ".join(recipients)
    msg['Content-Type'] = "text/plain"
    content = ""

    with open(client_id_path, 'r') as fd:
        client_details = json.loads(fd.read())
    current_hash = hash_config(config_file)
    saved_hash = client_details['web']['rix_config_hash']

    if current_hash != saved_hash:
        msg['Subject'] = f'FAILED Optics Configuration'
        content += f"The current hash: {current_hash}"
        content += f"Does not Match saved hash: {current_hash}"
        msg.set_content(content)
        send_email(msg)
        print("Config File failed hash control")
        sys.exit(-1)
    else:
        content += f"Valid Hash {current_hash} unchanged."
        content += "\r\n\r\n"
    
    with open(fn, 'r') as fd:
        serialized = json.load(fd)
    deser = apischema.deserialize(ConfigurationFile, serialized)

    # Prepare file for running
    file = PreparedFile.from_config(deser)

    # run checkout (comparison)
    top_level_result = asyncio.run(file.compare())

    top_group = True
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
            if group.config.name not in devices:
                content += f'    {group.config.name}\r\n'
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

def hash_config(config_file):
    fn = FilePathUtil(config_file)
    with open(fn, 'r') as fd:
        return hashlib.sha256(bytes(fd.read(), 'utf-8')).hexdigest()

def main(argv):
    options_parser = SetupOptionParser()
    (options, args) = options_parser.parse_args()

    if options.run_atefics:
        RequireOptions(options, 'config_file')
        run_optics_atef(options.config_file)
    elif options.hash_checkout:
        RequireOptions(options, 'config_file')
        print(hash_config(options.config_file))
    elif options.get_verification_token:
        print(get_verification_token())
    else:
        options_parser.print_help()
        return

main(sys.argv)
