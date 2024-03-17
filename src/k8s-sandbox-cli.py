import os
import sys
import shlex
import subprocess
import json
import argparse

ssh_key_name = "k8s-sandbox"
supported_clouds = ["aws"]

parser = argparse.ArgumentParser()
parser.add_argument("--action", type=str, choices=["create", "destroy"], help="The action to perform: create or destroy")
parser.add_argument("--cloud", type=str, choices=["aws"], help="The cloud provider to use")
parser.add_argument("--vpc-cidr", type=str, default="10.10.0.0/16", help="New VPC CIDR to use")
parser.add_argument("--region", type=str, default="us-east-1", help="The cloud provider region to use")
args = parser.parse_args()

def run_in_bash(cmd):
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    for line in iter(process.stdout.readline, ''):
        print(line.strip())
    process.wait()
    if process.returncode != 0:
        print(f"Command: {cmd} failed with error code {process.returncode}")
        print(f"Error: {process.stderr.read()}")
        sys.exit(process.returncode)
    return None

def create_tf_vars_aws():
    tf_vars_aws = {
        "credentials_profile": "sandbox",
        "environment_tag": "sandbox",
        "project_tag": "k8s-sandbox",
        "region": args.region,
        "vpc_cidr": args.vpc_cidr,
        "user_ip": "0.0.0.0/0",
        "host_os": "linux",
        "ssh_config_location": "~/.ssh/config",
        "public_key_location": f"{ssh_key_name}.pub",
        "private_key_location": f"{ssh_key_name}",
        "key_name": "k8s-sandbox",
        "instance_type": "t3a.medium",
        "ec2_user": "ubuntu",
        "instance_storage": 20
    }
    file_data = json.dumps(tf_vars_aws)
    with open ("../aws-deployment/terraform.tfvars.json", "w") as file:
        file.write(file_data)
    return None

if __name__ == "__main__":
    if args.cloud not in supported_clouds:
        print("Unsupported cloud provider. Exiting...")
        sys.exit(1)
    if args.action == "create":
        print("Creating SSH key pair...")
        run_in_bash(f'ssh-keygen -t rsa -N "" -f ../{args.cloud}-deployment/{ssh_key_name}')
        if args.cloud == "aws":
            print("Generating tfvar file...")
            create_tf_vars_aws()
            main_work_dir=os.getcwd()
            os.chdir(f"../{args.cloud}-deployment")
            print(f"Currently in {os.getcwd()}")
            run_in_bash("terraform init")
            run_in_bash("terraform plan")
            run_in_bash("terraform apply -auto-approve")
    elif args.action == "destroy":
        if args.cloud == "aws":
            print("Destroying AWS resources...")
            os.chdir(f"../{args.cloud}-deployment")
            run_in_bash("terraform destroy -auto-approve")
            run_in_bash(f"rm -f {ssh_key_name}*")
    else:
        print("Invalid action. Nothing to do.")

