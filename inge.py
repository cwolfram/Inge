#!/usr/bin/env python3

"""
INGE - Inventory Gone Easy
A tool for adding inventory items to an inventory project in JIRA.
More information here: https://carstenwolfram.de/inventory-management-with-jira/
"""
import os
import configparser
import inspect
import sys
import datetime, time, dateutil.parser
import re

try:
    import click
    from jira.client import JIRA
    from prettytable import PrettyTable
    import lib.getwarranty as g
    from lib.macmodelshelf import model, model_code
    from oauthlib.oauth1 import SIGNATURE_RSA
    from requests_oauthlib import OAuth1Session
except ImportError as e:
    print('Error: you should run "pip install -e ." first\n')
    print(e)
    sys.exit(1)


VERSION = "0.1"

scriptpath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


logo = """
 d8,
 `8P

  88b  88bd88b  d888b8b   d8888b
  88P  88P' ?8bd8P' ?88  d8b_,dP
 d88  d88   88P88b  ,88b 88b
d88' d88'   88b`?88P'`88b`?888P'
                      )88
                     ,88P
                 `?8888P

====  Inventory Gone Easy  ====
"""


def sanitize_apple_serial(s):
    """
    Checks if an Apple Serial begins with an S and cuts it off brutally
    :param s: The serial to check
    :return: Sanitized string
    """
    s = s.upper().strip()
    if s[:1] == "S" and len(s) == 13:
        return s[1:]
    else:
        return s


def p(text, message_type="normal"):
    """ Prints text via click.echo()
    :param text: the text to print
    :param message_type: controls how text is displayed, can be either "normal", "warning", "error" or "success"
    :return:
    """
    if message_type is "warning":
        click.echo(click.style(' ', bg='yellow', fg='black') + click.style(' ' + text, fg='yellow'))

    elif message_type is "error":
        click.echo(click.style(' ', bg='red', fg='black') + click.style(' ' + text, fg='red'), err=True)

    elif message_type is "success":
        click.echo(click.style(' ', bg='green', fg='black') + click.style(' ' + text, fg='green'))

    elif message_type is "debug":
        click.echo(click.style('Debug: ', bold=True) + click.style(str(text)))

    else:
        click.echo(text)


def new_item():
    return {u'serial_number': u'',
            u'inventory_number': u'',
            u'model': u'',
            u'est_manufacture_date': u'',
            u'est_purchase_date': u'',
            u'est_warranty_end_date': u'',
            }


config = configparser.ConfigParser()
if not config.read('{}/config.ini'.format(scriptpath)):
    p("Config file missing, take a look at config.ini.example and rename it to config.ini", "error")

secrets = configparser.ConfigParser()
if not secrets.read('{}/secrets.ini'.format(scriptpath)):
    p("Secretsfile missing, I'm going to create it. ", "warning")
    try:
        secretsfile = open('secrets.ini', 'w')
        secretsfile.close()
    except BaseException as e:
        p('Error at creating secrets.ini: {}'.format(e),'error')


def read(file_path):
    """ Read a file and return it's contents. """
    with open(file_path) as f:
        return f.read()

# OAUTH #
# The contents of the rsa.pem file generated (the private RSA key)
try:
    RSA_KEY = read(config.get('jira', 'rsa-private-key'))
except BaseException as e:
    p('Error loading the key file. Did you create a key pair? {}'.format(e), 'error')

# The URLs for the JIRA instance
JIRA_SERVER = config.get('jira','server')
REQUEST_TOKEN_URL = JIRA_SERVER + '/plugins/servlet/oauth/request-token'
AUTHORIZE_URL = JIRA_SERVER + '/plugins/servlet/oauth/authorize'
ACCESS_TOKEN_URL = JIRA_SERVER + '/plugins/servlet/oauth/access-token'


# Step 1: Get a request token

try:
    CONSUMER_KEY = secrets.get('jira', 'consumer_key')
    ACCESS_TOKEN = secrets.get('jira', 'access_token')
    ACCESS_TOKEN_SECRET = secrets.get('jira', 'access_token_secret')
except (configparser.NoOptionError, configparser.NoSectionError) as e:
    p('JIRA OAuth Token not found yet. Let\'s set it up.\n','warning')
    print('We\'ll assume two things:')
    print('1. You have already generated a RSA key pair.')
    print('2. You have already configured an application link.')
    print('If you didn\'t yet, go here and read how to do this:')
    print('https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples')
    print('')
    print('STEP 1: Enter the Consumer Key\n(You probably set this when you configured the Application link in JIRA)')
    CONSUMER_KEY = click.prompt(click.style('Consumer Key', bold=True))
    print("\n")

    oauth = OAuth1Session(CONSUMER_KEY, signature_type='auth_header',
                          signature_method=SIGNATURE_RSA, rsa_key=RSA_KEY)
    request_token = oauth.fetch_request_token(REQUEST_TOKEN_URL)

    # Step 2: Get the end-user's authorization
    print("STEP 2: Authorization")
    print("  Visit to the following URL to provide authorization:")
    print("  {}?oauth_token={}".format(AUTHORIZE_URL, request_token['oauth_token']))
    print("\n")

    while input("Press any key to continue..."):
        pass

    # XXX: This is an ugly hack to get around the verfication string
    # that the server needs to supply as part of authorization response.
    # But we hard code it.
    oauth._client.client.verifier = u'verified-RepudvejOuHyawdoddEd'

    # Step 3: Get the access token
    access_token = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    # Step 4: Write it all to the secrets.ini
    try:
        secretsfile = open("secrets.ini", 'w')
        secrets.add_section('jira')
        secrets.set('jira', 'consumer_key', CONSUMER_KEY)
        secrets.set('jira', 'access_token', access_token['oauth_token'])
        secrets.set('jira', 'access_token_secret', access_token['oauth_token_secret'])
        secrets.write(secretsfile)
        secretsfile.close()
    except BaseException as e:
        p('Error writing to secrets.ini: {}'.format(e))

    ACCESS_TOKEN = secrets.get('jira', 'access_token')
    ACCESS_TOKEN_SECRET = secrets.get('jira', 'access_token_secret')


def connect_to_jira():
    try:
        return JIRA(options={'server': JIRA_SERVER}, oauth={
            'access_token': ACCESS_TOKEN,
            'access_token_secret': ACCESS_TOKEN_SECRET,
            'consumer_key': CONSUMER_KEY,
            'key_cert': RSA_KEY
        })
    except BaseException as e:
        p('Error connecting to JIRA.\n{}'.format(e), 'error')


# "myt-$inventory_number" should become "myt-1337" if inventory_number is "1337"
# "myt-$serialnumber" should become "myt-C02PQB5VG8WP" if serialnumber is "C02PQB5VG8WP"
def build_summary_string(item, devicetype):
    """
    Builds a summary string from the template defined in the config.ini
    :param item: The item dictionary
    :param devicetype: The devicetype (like "macbook") from the config.ini input key
    :return:
    """
    r = re.compile('\$(\w*)')
    summary = config['input.{}'.format(devicetype)]['summary']
    m = r.findall(summary)
    for x in m:
        summary = summary.replace('$'+x,item[x])
    return summary


class Flags(object):
    def __init__(self):
        """ Helper class for flags like verbose, simulate and debug """
        self.verbose = False
        self.simulate = False
        self.debug = False


pass_flags = click.make_pass_decorator(Flags, ensure=True)

@click.group()
@click.version_option(version=VERSION)
@click.option('-v', '--verbose', is_flag=True, help='Shows more information')
@click.option('-d', '--debug', is_flag=True, help='Prints debug information')
@click.option('-s', '--simulate', is_flag=True, help='Simulates run, nothing will be written')
@pass_flags
def main(flags, verbose, debug, simulate):
    """A tool for adding inventory items to an inventory project in JIRA"""
    flags.verbose = verbose
    flags.simulate = simulate
    flags.debug = debug
    if flags.verbose:
        p(logo)
    if flags.simulate:
        p("Simulation mode, nothing will be written", 'warning')

    print(connect_to_jira())


@main.command()
@click.option('--inventory_number', prompt='Enter or scan the inventory number')
@click.option('--serial_number', prompt='Enter or scan the serial number')
@pass_flags
def new(flags, inventory_number, serial_number):
    """Creates a new inventory ticket"""
    item = new_item()
    item['inventory_number'] = inventory_number
    item['serial_number'] = sanitize_input(serial_number)
    item['model'] = model(model_code(sanitize_input(serial_number))) # get model string from macmodelshelf
    item['serial_number'] = sanitize_apple_serial(serial_number)
    item['model'] = model(model_code(sanitize_apple_serial(serial_number))) # get model string from macmodelshelf
    warranty_info = g.offline_warranty(item.get('serial_number')) # get warranty info from pyMacWarranty
    item['est_manufacture_date'] = warranty_info[0].get('EST_MANUFACTURE_DATE')
    item['est_purchase_date'] = warranty_info[0].get('EST_PURCHASE_DATE')
    item['est_warranty_end_date'] = warranty_info[0].get('EST_WARRANTY_END_DATE')

    if flags.debug:
        print(item)


if __name__ == '__main__':
    main()

