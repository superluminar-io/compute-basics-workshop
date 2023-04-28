# Setup

## In this lab …

- Setup development environment

## Local development setup

For this workshop, we rely on a basic development setup, including:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [Node.js >= 16.x / NPM](https://nodejs.org/en/)
- [python >= 3.10](http://python.org)
- Editor (e.g. [Visual Studio Code](https://code.visualstudio.com/))
- Terminal (e.g. [iTerm2](https://iterm2.com/) or PowerShell)

Make sure you have installed and configured all dependencies on your computer.

If you can work with your already existing development setup, the AWS CLI needs
access to your AWS account. To not override your default configuration, make
sure you have configured your AWS CLI with a [named
profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-profiles)
for this workshop.

### Configuring a named profile for the AWS CLI

1. Start the configuration by running:
```bash
aws configure --profile serverless-workshop
```
1. You will be one by one asked to provide your credentials for:
```
AWS Access Key ID [None]
AWS Secret Access Key [None]
Default region name [None]
Default output format [None]
```
⚠️ Make sure you use **eu-central-1** as your default region.

1. To easen things in the following labs, set the AWS_PROFILE environment variable to your named profile:
```bash
export AWS_PROFILE=serverless-workshop
```

You should now be able to execute this command:
```bash
aws sts get-caller-identity
```

### AWS SSO 
If you are using an AWS SSO managed account, please follow the instructions for
[short-term credentials for the AWS
CLI](https://aws.amazon.com/blogs/security/aws-single-sign-on-now-enables-command-line-interface-access-for-aws-accounts-using-corporate-credentials/).
