import argparse
import requests
import logging
import xml.etree.ElementTree as ET
from os.path import expanduser
from os.path import join as pathjoin
from collections import defaultdict
import os
import pathlib
import sys
import json
from dateutil import parser
from datetime import datetime, timezone
from requests_negotiate_sspi import HttpNegotiateAuth
from bs4 import BeautifulSoup
import boto3
import base64
from botocore import UNSIGNED
from botocore.config import Config

# Enable debugging
logging.basicConfig(level=logging.DEBUG)
# Write warnings to logger, instead of printing them to stdout directly
logging.captureWarnings(True)

def get_saml_assertion(html):
    # Decode the response and extract the SAML assertion
    soup = BeautifulSoup(html, features="html.parser")
    assertion = ''
    # Look for the SAMLResponse attribute of the input tag (determined by
    # analyzing the debug print lines above)
    for inputtag in soup.find_all('input'):
        if inputtag.get('name') == 'SAMLResponse':
            assertion = inputtag.get('value')
    return assertion


def get_saml_role(assertion, role):
    root = ET.fromstring(base64.b64decode(assertion))
    for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
        if saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role':
            for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                ##todo throw exception if role does not exists
                if role in saml2attributevalue.text:
                    return saml2attributevalue.text


def xml2dict(xml):
    """Hello"""
    return etree2dict(ET.XML(xml))


def etree2dict(element):
    newdict = {element.tag: {} if element.attrib else None}
    children = list(element)
    if children:
        childdict = defaultdict(list)
        for dc in map(etree2dict, children):
            for key, value in dc.items():
                childdict[key].append(value)
        newdict = {element.tag: {key: value[0] if len(value) == 1 else value for key, value in childdict.items()}}
    if element.text:
        text = element.text.strip()
        if text:
            newdict[element.tag] = text
        return newdict


def cached_credentials():
    jsonfile = expanduser(pathjoin('~', 'aws', 'credential_process', 'cache.json'))

    def has_valid_token(data, key):
        return key in data and not is_expired(data[key])

    def is_expired(creds):
        expiration = parser.parse(creds['Expiration'])
        now = datetime.now(timezone.utc)
        delta = (expiration - now).total_seconds()
        return delta <= 0

    def create_file_does_not_exist():
        if not os.path.isfile(jsonfile):
            pathlib.Path(os.path.dirname(jsonfile)).mkdir(parents=True, exist_ok=True)
            with open(jsonfile, 'w') as f:
                json.dump({}, f)

    def get_credentials_from_file(key):
        with open(jsonfile) as f:
            data = json.load(f)
            if has_valid_token(data, key):
                return data.get(key)

    def save_credentials_to_file(credentials, key):
        with open(jsonfile, 'r') as json_file:
            data = json.load(json_file)
            data[key] = credentials
        with open(jsonfile, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def decorator(fn):
        def wrapped(*args, **kwargs):
            create_file_does_not_exist()
            key = args[0].account + '_' + args[0].role
            credentials = get_credentials_from_file(key)
            if credentials:
                return credentials
            response = fn(*args, **kwargs)
            save_credentials_to_file(response, key)
            return response

        return wrapped

    return decorator


@cached_credentials()
def get_credentials(args):
    session = requests.Session()
    ##TODO default to wincertstore
    session.verify = args.sslverify
    path = '/' + args.account
    b64_account = base64.b64encode(path.encode('ascii')).decode('utf-8')
    saml_response = session.get(args
                                .endpoint, auth=HttpNegotiateAuth(), cookies={'dp-org-uri': b64_account})
    saml_assertion = get_saml_assertion(saml_response.text)
    saml_role = get_saml_role(saml_assertion, args.role)
    role_arn = saml_role.split(',')[0]
    principal_arn = saml_role.split(',')[1]
    client = boto3.client('sts', region_name=args.region, config=Config(signature_version=UNSIGNED))
    creds = client.assume_role_with_saml(RoleArn=role_arn, PrincipalArn=principal_arn, SAMLAssertion=saml_assertion)[
        'Credentials']
    creds['Expiration'] = creds['Expiration'].isoformat()
    return creds


#######################################################
###################
# Start
def main():

    cli = argparse.ArgumentParser()
    cli.add_argument('-a', '--account', type=str, dest='account', default='account', help='AWS account alias')
    cli.add_argument('-r', '--role', type=str, dest='role', default='role', help='AWS Role to assume')
    cli.add_argument('-e', '--endpoint', type=str, dest='endpoint', help='Https SAML endpoint')
    awscli = cli.add_argument_group('aws')
    awscli.add_argument('-region', type=str, dest='region', help='AWS Region', default='us-east-1')
    sslcli = cli.add_argument_group('ssl').add_mutually_exclusive_group()
    ##TODO test and fix semantics
    sslcli.add_argument('--disable-ssl', dest='sslverify', default=False,
                        help='Disable SSL verfication (not recommended)',
                        action='store_const', const=False)
    sslcli.add_argument('--sslcert', type=str, dest='sslcert', help='CA Certificate for SSL verification')
    args = cli.parse_args()

    credentials = get_credentials(args)

    dict_response = {
        "Version": 1,
        "AccessKeyId": credentials['AccessKeyId'],
        "SecretAccessKey": credentials['SecretAccessKey'],
        "SessionToken": credentials['SessionToken'],
        "Expiration": credentials['Expiration'],
    }
    sys.stdout.write(json.dumps(dict_response))


if __name__ == "__main__":
    main()
