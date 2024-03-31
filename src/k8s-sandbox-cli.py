import os
import sys
import shlex
import shutil
import subprocess
import json
import argparse
import traceback
import io
from pathlib import Path
from ruamel.yaml import YAML

ssh_key_name = "k8s-sandbox"
supported_clouds = ["aws"]
kubespray_src_dir = f"{os.environ['HOME']}/workspace/poc/kubespray"
inventory_dir = f"{kubespray_src_dir}/inventory/k8s-sandbox"


parser = argparse.ArgumentParser()
parser.add_argument("--action", type=str, choices=["create", "destroy"], help="The action to perform: create or destroy")
parser.add_argument("--cloud", type=str, choices=["aws"], help="The cloud provider to use")
parser.add_argument("--vpc-cidr", type=str, default="10.10.0.0/16", help="New VPC CIDR to use")
parser.add_argument("--region", type=str, default="us-east-1", help="The cloud provider region to use")
parser.add_argument("--kube-pods-cidr", type=str, default="192.168.0.0/16", help="The CIDR to use for k8s pods")
parser.add_argument("--kube-service-cidr", type=str, default="10.96.0.0/16", help="The CIDR to use for k8s service endpoints")
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
    return True

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

def tf_create():
    run_in_bash("terraform init")
    run_in_bash("terraform plan")
    run_in_bash("terraform apply -auto-approve")
    return None

def get_ip_details():
    tf_state_file = "terraform.tfstate"
    with open(tf_state_file, "r") as file:
        data = json.load(file)
        try:
            public_ip = data["outputs"]["instance_public_ip"]["value"]
            private_ip = data["outputs"]["instance_private_ip"]["value"]
        except KeyError:
            print(traceback.format_exc())
            return None
    return {"public_ip": public_ip, "private_ip": private_ip}

def prepare_inventory_files(ip_config):
    hosts_file = f"{inventory_dir}/hosts.yaml"
    inventory_file = f"{inventory_dir}/inventory.ini"
    k8s_yml_file = f"{inventory_dir}/group_vars/k8s_cluster/k8s-cluster.yml"
    with open(hosts_file, "r") as file:
        import yaml
        hosts_data = yaml.load(file, Loader=yaml.FullLoader)
        hosts_data["all"]["hosts"]["node1"]["ip"] = ip_config["instance_ip_details"]["private_ip"]
        hosts_data["all"]["hosts"]["node1"]["access_ip"] = ip_config["instance_ip_details"]["private_ip"]
    with io.open(hosts_file, "w", encoding="utf8") as out_file:
        yaml.dump(hosts_data, out_file, default_flow_style=False, allow_unicode=True)

    inventory_str = f"""[all]
node1 ansible_host={ip_config["instance_ip_details"]["public_ip"]}

[kube_control_plane]
node1

[etcd]
node1

[kube_node]
node1

[calico_rr]

[k8s_cluster:children]
kube_control_plane
kube_node
calico_rr
"""
    with open(inventory_file, "w+") as file:
        file.write(inventory_str)

    with open(k8s_yml_file, "r") as file:
        yaml = YAML()
        yaml.default_flow_style = False
        k8s_data = yaml.load(file)
        k8s_data["kube_service_addresses"] = ip_config["kube_service_cidr"]
        k8s_data["kube_pods_subnet"] = ip_config["kube_pods_cidr"]
    with io.open(k8s_yml_file, "w", encoding="utf8") as out_file:
         yaml.dump(k8s_data, out_file)
    return None

def prepare_inventory_dir():
    ip_details = get_ip_details()
    if ip_details is not None:
        shutil.copytree(f"{kubespray_src_dir}/inventory/sample", inventory_dir)
        os.chdir(kubespray_src_dir)
        print(f"Changed dir to ******************* {os.getcwd()}")
        Path(f"{inventory_dir}/hosts.yaml").touch()
        os.environ["CONFIG_FILE"] = f"{inventory_dir}/hosts.yaml"
        if run_in_bash(f'python3 contrib/inventory_builder/inventory.py {ip_details["public_ip"]}'):
            ip_config = {
                "instance_ip_details": ip_details,
                "kube_pods_cidr": args.kube_pods_cidr,
                "kube_service_cidr": args.kube_service_cidr
                }
            if prepare_inventory_files(ip_config):
                return True
            return False
    else:
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
            tf_create()
            prepare_inventory_dir()
    elif args.action == "destroy":
        if args.cloud == "aws":
            print("Destroying AWS resources...")
            os.chdir(f"../{args.cloud}-deployment")
            run_in_bash("terraform destroy -auto-approve")
            os.remove(f"{ssh_key_name}.pub")
            os.remove(f"{ssh_key_name}")
    else:
        print("Invalid action. Nothing to do.")

