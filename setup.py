import os
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

# The directory containing this file
HERE = here = os.path.abspath(os.path.dirname(__file__))

# The text of the README file
README = ""
with open(os.path.join(HERE, "README.md")) as f:
    README = f.read()

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    "Environment :: Win32 (MS Windows)",
    'Intended Audience :: Developers',
    'Topic :: Internet',
    'License :: OSI Approved :: Apache Software License',
    "Natural Language :: English",
    "Operating System :: Microsoft :: Windows",
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
]

setup(
    name='aws-cp-saml',
    version='0.0.5',
    author='Robert Hutto',
    author_email='rdhutto1@gmail.com',
    url='https://github.com/roberthutto/aws-cp-saml',
    description='AWS SAML Credentials Process CLI that uses Windows SSO (Integrated Windows Authentication)',
    long_description=README,
    long_description_content_type="text/markdown",
    license='Apache 2',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'awscp=awscpsaml.awscp:main'
        ]
    },
    platforms="Windows",
    classifiers=CLASSIFIERS,
    keywords='SAML SSO IWA AWS credentials ntlm kerberos windows',
    install_requires=requirements,
    zip_safe=False
)
