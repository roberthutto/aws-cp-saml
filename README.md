# aws-cp-saml
AWS External Credential Process for Windows SSO (Integrated Windows Auth)

# AWS Credentials Configuration with Single Sign On (SSO)
* [Overview](#overview)
* [Benefits](#benefits)
* [Setup](#setup)
* [Future Work](#future-work)
* [Authenticating Proxy Setup](#authenticating-proxy-setup)

<a name="overview"></a>
### Overview
This package provides an interface for providing AWS temporary credentials using IWA (Integrated Windows Authentication) 
aka Windows SSO. It allows the user to configure the standard AWS CLI using the 
[external credential process](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html) while
retaining the security benefit of using password-less SSO using the user current session to authenticate with a SAML provider.
Users can configure profiles for different AWS accounts and Roles to seamlessly provide AWS temp creds to any process that 
uses the AWS SDK. The result is a credential process that is similar to the Role based access provided by running on AWS EC2.

<a name="benefits"></a>
### Benefits
Because this works with the default credential provider chain it allows an application that uses any of the AWS SDK 
[languages](https://aws.amazon.com/tools/) to transparently get credentials necessary to make signed AWS api calls. The
result is that the AWS cli, Terraform, etc. all work with this process.

1. Single Sign On (SS0) using Integrated Windows Authentication (IWA) thanks to 
   [requests-negotiate-sspi](https://github.com/brandond/requests-negotiate-sspi)
2. Integrates natively with [aws/config](https:/docs.aws.amazon.com/cli/latest/userguide/cli-configure files.html)
3. Provides credential caching to avoid excessive traffic on SAML provider, reduce Latency of AWS api calls and refresh 
   expired credentials. This eliminates the problem of Terraform stacks that fail if credentials expire for a stack that 
   takes longer to create than the temp creds duration.
4. Integrates seamlessly with any application Using AWS SDK Similar to Ec2 role based credentials.
   
<a name="setup"></a>
### Setup
#### Prerequisites
1. Python 3.x with pip installed
2. Aws CLi preferably V2
3. Windows Environment with SSO

#### Optional
3. Internet proxy configured if on a corporate network behind and authenticating proxy. See below 
   [Authenticating Proxy Setup](#authenticating-proxy-setup)
4. pip configured with private pypi mirror

#### Steps
1. Install aws-cp-saml `pip install aws-cp-saml`
2. Setup `~/.aws/config` with profiles using aws-cp-saml as explained in 
   [external credential process](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.htm).
   An example config:
   ```shell
   [default]
   region = us-east-1
   credential_process = awscp --account aws_account_alias --role aws_role --endpoint https://samlprovider
   
   [profile foo]
   region = us-east-1
   credential_process = awscp --account diff_alias --role aws_role --endpoint https://samlprovider
   ```
The aws-cp-saml credentials process takes 3 required parameters: 
* `--account` the AWS account alias as configured in the AWS Account
* `--role` the AWS Role to be assumed
* `--endpoint` the endpoint of the corporate SAML provider

More details with `awscp -help`  //TODO test help

3. Test Configuration with aws no-verify-ssl s3 ls

<a name="future-work"></a>
## Future Work

* Integrate the AWS credentials caching with Windows credentials manager similar to AWS vault
* Make caching threadsafe if needed
* Provide command to patch aws cli and python with Corporate certs from Windows-ROOT certificate store
* Refactor to support multiple SAML providers
* Add config .ini for reused configuration such as `--endpoint`


<a name="authenticating-proxy-setup"></a>
## Authenticating Proxy Setup
Some users in a corporate environment may be behind an authenticating proxy. This causes the problem of users needing to
place UserId and Password into environment variables `HTTP_PROXY and HTTPS_PROXY` as outlined in the AWS 
[documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-proxy.html). The worst example of this 
would be placing the proxy settings into windows envs or git bash `.bash_profile` and better case would be load them aws shell
envs as needed using a password prompt that hides the password when entered. The whole point of aws-cp-saml is to utilize 
SSO and avoid dealing with passwords once logged into the Windows domain. The AWS documentation above mentions using the 
[Cntlm proxy](http://cntlm.sourceforge.net/) that does not support SSO and still requires the user to store the NTLM 
hash in and .ini or pass the username and password on the commandline when starting.

Fortunately [px-proxy](https://pypi.org/project/px-proxy/) provides a better solution that utilizes Windows SSO. 
Below are quickstart steps and refer for the documentation for more configuration options

1. Install with `pip install px-proxy`
2. Start with `px`
3. Set proxy envs

Windows create users environment variables. Preferred solution which provides this globally to all shells
```shell
HTTP_PROXY=http://localhost:3128
HTTPS_PROXY=http://localhost:3128
```

Gitbash
```shell
export HTTP_PROXY=http://localhost:3128
export HTTPS_PROXY=http://localhost:3128
```

That's it there is very little configuration with px-proxy. It dynamically queries Windows Internet Options for the .pac file
to configure the proxy and uses Windows SSO to negotiate with the corporate authenticating proxy. Optionally you 
can install this as a Windows service per the docs or start it some other way. If your internet options don't have the .pac
file then the corporate proxy information can be provided via the commandline on start or saved to .ini config file  



