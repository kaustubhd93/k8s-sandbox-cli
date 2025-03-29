# k8s-sandbox-cli
A command line interface to launch a kubernetes sandbox instance on your preferred cloud provider.

## Supported Cloud providers
- AWS
- GCP

## Instructions (if you have docker)

- `wget https://raw.githubusercontent.com/kaustubhd93/k8s-sandbox-cli/main/src/gen-ssh-keys.sh -O /tmp/gen-ssh-keys.sh`

- `bash /tmp/gen-ssh-keys.sh`

- create a s3 bucket to store the Terraform state.

- Create k8s-sandbox single-node cluster on aws
```
docker run --name k8s-sandbox-cli-create -v /tmp/k8s-sandbox-cli/keys/:/opt/keys/ \
-it kaustubhdesai/k8s-sandbox-cli:0.5.0  \
--action create --cloud aws --vpc-cidr <cidr> \
--region <region> --tf-state-bucket <bucket_name> \
--cloud-credentials '{"region":"region","aws_access_key_id":"access_key","aws_secret_access_key":"secret_key"}'
```

- Create k8s-sandbox single-node cluster on GCP
```
docker run --name k8s-sandbox-cli-create -v /tmp/k8s-sandbox-cli/keys/:/opt/keys/ \
-it kaustubhdesai/k8s-sandbox-cli:0.5.0  \
--action create --cloud gcp --vpc-cidr <cidr> \
--region <region> --tf-state-bucket <bucket_name> \
--cloud-credentials '{}' \
--gcp-project-id <gcp-project-id>
```

- Log into the server using public ip displayed in the output of the previous command `ssh -i /tmp/k8s-sandbox-cli/keys/k8s-sandbox ubuntu@<public_ip>`

- Once you are done with your POC you can now destroy the infra.  
```
docker run --name k8s-sandbox-cli-destroy -v /tmp/k8s-sandbox-cli/keys/:/opt/keys/ \
-it kaustubhdesai/k8s-sandbox-cli:0.5.0 --action destroy \
--region <region> --tf-state-bucket <bucket_name> \
--cloud-credentials '{"region":"region","aws_access_key_id":"access_key","aws_secret_access_key":"secret_key"}'
```

## Pre-requisites (Running without docker)
- python3 installed
- terraform binary installed 
- A credentials profile with name sandbox in ~/.aws/credentials which will look like below:
```
[sandbox]
region = <region>
aws_access_key_id = <access_key_id>
aws_secret_access_key = <secret_access_key>
```

## Instructions  (Running without docker)
- Clone the code on your system using `git clone https://github.com/kaustubhd93/k8s-sandbox-cli.git`
- `pip install src/requirements.txt`
- `cd src`
- `python3 k8s-sandbox-cli.py --action create --cloud aws --vpc-cidr <cidr> --region <region> --tf-state-bucket <bucket_name>`
- `ssh -i ../aws-deployment/k8s-sandbox <public_ip_displayed_in_output>`
- When you are done working: `python3 k8s-sandbox-cli.py --action destroy --cloud aws --tf-state-bucket <bucket_name>`

### Initially forked from [morethancertified/kubernetes-sandbox](https://github.com/morethancertified/kubernetes-sandbox)
