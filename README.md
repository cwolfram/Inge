INGE
====
_Inventory Gone Easy_

### Warning 

INGE is currently still heavy in development and will likely break. 
To fix this, send bug reports and pull requests.

### About

INGE is designed to work together with a JIRA Inventory Project, as described here: 
<https://carstenwolfram.de/inventory-management-with-jira/> 

It let's you define own inventory workflows with your own existing custom fields that will be used during the scan
of the inventory items. It can automatically fill in warranty and model information based on the serial number
of an apple device. 

### Requirements

Python 3. 
        
Python modules: *Click*, *jira*, *python-dateutil*, *prettytable*, *oauthlib*, *jwt*, *cryptography*, *pyjwt*.


### Installation

1. Clone Repo and run `pip install -e .` to install all the requirements.
2. Copy or Rename `config.ini.example` to `config.ini`

### Configuration

Take a look into the `config.ini` to learn about the configuration. Set your server URL, the project key 

First, you have to configure your JIRA instance for OAuth1, if not yet done. 
Atlassian has a good step-by-step tutorial with code examples here: 
<https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples>.
Follow this tutorial. You should end up with a keyfile that you have to reference in the `config.ini`

If you start INGE the first time using `inge new`, it should prompt you for the consumer key that you
defined in JIRA. Enter it and follow the next instructions. If you don't get an error, you have successfully
logged in to JIRA using OAuth.

Now the workflows: 
for every workflow you need, create a section in the config.ini with a title named `[input.workflowname]`.
There you can define the fields which should be used. There are examples in the `config.ini`

Match the fields that you define with your existing custom fields in JIRA in the `[fields]` section.

### Usage

`inge new`: adds a device to the inventory system.

I recommend starting INGE with the `-v` option.

Parameters:

`--help`
Shows help. All you need basically

`-t`, `--itemtype`
Specifies the type of inventory item you want to import. Defaults to `macbook`.

`-s`, `--simulate`
Simulates Execution - nothing will be written

`-d`, `--debug`
Debug Mode - outputs contents of lists, dicts and lots of other debug information. Useful for ... debugging

`-v`, `--verbose`
Verbose Mode - if set, shows more information (and a pretty table)

Inge currently features only an interactive mode. 
It is not yet possible to pass arguments on the command line because I don't know how to do that in a modular way.

### Usage with a barcode scanner

INGE should work great with a barcode scanner.

Some tips:

1. Set your scanner to end a line with a <CR> if you don't want to press Enter after every scan
2. INGE will automatically strip the leading *S* from Apple serial numbers


### To do

- ~~import custom input options from config~~

- write checks to see if a serial number / inventory number already exists

- ~~implement linked issues~~

- if the config file gets any more complicated, maybe I should use JSON or YAML

- Flask-based Web interface

- Unit tests via a CI system

- multiple linked issues (if that is needed)