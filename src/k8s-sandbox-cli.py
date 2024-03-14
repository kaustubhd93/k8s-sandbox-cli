import os
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--action", type=str, choices=["create", "destroy"], help="The action to perform: create or destroy")
parser.add_argument("--cloud", type=str, choices=["aws"], help="The cloud provider to use")
parser.add_argument("--vpc-cidr", type=str, default="10.10.0.0/16", help="New VPC CIDR to use")
parser.add_argument("--region", type=str, default="us-east-1", help="The cloud provider region to use")
args = parser.parse_args()

tf_vars_aws = {
    "credentials_profile": "sandbox",
    "environment_tag": "sandbox",
    "project_tag": "k8s-sandbox",
    "region": args.region,
    "vpc_cidr": args.vpc_cidr,
    "user_ip": "0.0.0.0/0",
    "host_os": "linux",
    "ssh_config_location": "~/.ssh/config",
    "public_key_location": "",
    "private_key_location": "",
    "key_name": "k8s-sandbox",
    "instance_type": "t3a.medium",
    "ec2_user": "ubuntu",
    "instance_storage": 20
}

def create_tf_vars_aws():
    file_data = json.dumps(tf_vars_aws)
    with open ("../aws-deployment/terraform.tfvars.json", "w") as file:
        file.write(file_data)
    return None

if __name__ == "__main__":
    if args.action == "create":
        if args.cloud == "aws":
            print("Generating tfvar file...")
            create_tf_vars_aws()
    elif args.action == "destroy":
        if args.cloud == "aws":
            print("Destroying AWS resources...")
    else:
        print("Invalid action. Nothing to do.")

