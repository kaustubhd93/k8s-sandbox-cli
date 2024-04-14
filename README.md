# k8s-sandbox-cli
A command line interface to launch a kubernetes sandbox on your preferred cloud provider

## Supported Cloud providers
- AWS

## Pre-requisites
- python3
- terraform
- A credentials profile with name sandbox in ~/.aws/credentials which will look like below:
```
[sandbox]
region = <region>
aws_access_key_id = <access_key_id>
aws_secret_access_key = <secret_access_key>
```

## Instructions  
- Clone the code on your system
- `cd src`
- `python3 k8s-sandbox-cli.py --action create --cloud aws --vpc-cidr <cidr> --region <region>`
- `ssh -i ../aws-deployment/k8s-sandbox <public_ip_displayed_in_output>`
- When you are done working: `python3 k8s-sandbox-cli.py --action destroy --cloud aws`

### Initially forked from [morethancertified/kubernetes-sandbox](https://github.com/morethancertified/kubernetes-sandbox)