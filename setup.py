from setuptools import setup

setup(
    name='INGE - Inventory Gone Easy',
    version='0.1',
    py_modules=['inge'],
    author='Carsten Wolfram',
    author_email='mail@carstenwolfram.de',
    install_requires=[
        'Click',
        'jira',
        'python-dateutil',
        'prettytable',
        'oauthlib',
        'jwt',
        'cryptography',
        'pyjwt'
    ], entry_points='''
    [console_scripts]
    inge=inge:main
    '''
)
