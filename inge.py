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


def sanitize_input(s):
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
        click.echo(click.style(' ', bg='red', fg='black') + click.style(' ' + text, fg='red'))
        sys.exit(1)

    elif message_type is "success":
        click.echo(click.style(' ', bg='green', fg='black') + click.style(' ' + text, fg='green'))

    elif message_type is "debug":
        click.echo(click.style('Debug: ', bold=True) + click.style(text))

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
    p("Credentials file missing, take a look at credentials.ini.example and rename it to credentials.ini", "error")


class Flags(object):
    def __init__(self):
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
    warranty_info = g.offline_warranty(item.get('serial_number')) # get warranty info from pyMacWarranty
    item['est_manufacture_date'] = warranty_info[0].get('EST_MANUFACTURE_DATE')
    item['est_purchase_date'] = warranty_info[0].get('EST_PURCHASE_DATE')
    item['est_warranty_end_date'] = warranty_info[0].get('EST_WARRANTY_END_DATE')


    if flags.debug:
        print(item)


if __name__ == '__main__':
    main()

