import os
import sys
import shlex
import shutil
import subprocess
import json
import argparse
import traceback
import io
import time
import re
import requests

from pathlib import Path
from configparser import ConfigParser

from ruamel.yaml import YAML

ssh_key_name = "k8s-sandbox"
supported_clouds = ["aws"]
user_data_wait_time = 300
# if using kubespray
kubespray_src_dir = f"{os.environ['HOME']}/workspace/poc/kubespray"
inventory_dir = f"{kubespray_src_dir}/inventory/k8s-sandbox"

parser = argparse.ArgumentParser()
parser.add_argument("--action", type=str, choices=["create", "destroy"], help="The action to perform: create or destroy")
parser.add_argument("--cloud", type=str, choices=["aws"], help="The cloud provider to use")
parser.add_argument("--vpc-cidr", type=str, default="10.10.0.0/16", help="New VPC CIDR to use")
parser.add_argument("--region", type=str, default="us-east-1", help="The cloud provider region to use")
parser.add_argument("--kube-pods-cidr", type=str, default="192.168.0.0/16", help="The CIDR to use for k8s pods")
parser.add_argument("--kube-service-cidr", type=str, default="10.96.0.0/16", help="The CIDR to use for k8s service endpoints")
parser.add_argument("--cloud-credentials", type=str, default= '{"creds":"none"}', help="Cloud provider credentials in json format")
args = parser.parse_args()

def run_in_bash(cmd):
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=os.environ.copy())
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

def create_credentials_file(cloud, credentials):
    print(f"Creating credentials file for {cloud}...")
    if cloud == "aws":
        home_dir = os.environ["HOME"]
        os.mkdir(f"{home_dir}/.aws")
        credentials_file = f"{home_dir}/.aws/credentials"
        credentials_data = json.loads(credentials)
        credentials_data = {"sandbox": credentials_data}
        config = ConfigParser()
        with open(credentials_file, "w") as file:
            for section, options in credentials_data.items():
                config.add_section(section)
                for key, value in options.items():
                    config.set(section, key, str(value))
            config.write(file)
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

def get_release_version(repo_uri):
    response = requests.get(f'https://api.github.com/repos/{repo_uri}/tags')
    tags = json.loads(response.text)
    for tag in tags:
        if re.match(r'^v\d+\.\d+\.\d+$', tag['name']):
            latest_tag = tag['name'].replace('v', '')
            return latest_tag
        continue
    return None

def prepare_user_data():
    print("Preparing user data...")
    print("Getting latest release versions of k8s dependencies...")
    containerd_version = get_release_version('containerd/containerd')
    runc_version = get_release_version('opencontainers/runc')
    cni_plugins_version = get_release_version('containernetworking/plugins')
    calico_version = get_release_version('projectcalico/calico')
    nerdctl_version = get_release_version('containerd/nerdctl')
    print("Done getting latest release versions...")
    # Adding escape character for sed command
    pod_cidr = args.kube_pods_cidr.replace('/', '\/')
    run_in_bash(f"cp setup-k8s-cluster.sh ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/containerd_version=placeholder/containerd_version={containerd_version}/g' ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/runc_version=placeholder/runc_version={runc_version}/g' ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/cni_plugins_version=placeholder/cni_plugins_version={cni_plugins_version}/g' ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/calico_version=placeholder/calico_version={calico_version}/g' ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/pod_cidr=placeholder/pod_cidr={pod_cidr}/g' ../{args.cloud}-deployment/userdata.tpl")
    run_in_bash(f"sed -i 's/nerdctl_version=placeholder/nerdctl_version={nerdctl_version}/g' ../{args.cloud}-deployment/userdata.tpl")
    return None

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
    if os.path.exists("/.dockerenv"):
        print("Running inside docker.")
        create_credentials_file(args.cloud, args.cloud_credentials)
    else:
        print("Not running inside docker.")
    if args.action == "create":
        print("Creating SSH key pair...")
        run_in_bash(f'ssh-keygen -t rsa -N "" -f ../{args.cloud}-deployment/{ssh_key_name}')
        if args.cloud == "aws":
            print("Generating tfvar file...")
            create_tf_vars_aws()
            prepare_user_data()
            main_work_dir=os.getcwd()
            os.chdir(f"../{args.cloud}-deployment")
            print(f"Currently in {os.getcwd()}")
            tf_create()
        print("*****************************************************************")
        print("Waiting for single node k8s cluster to be ready...")
        print("*****************************************************************")
        time.sleep(user_data_wait_time)
        print("*****************************************************************")
        print("Log into the node using ssh and run below command to check the status of the cluster:")
        print("kubectl get nodes")
    elif args.action == "destroy":
        if args.cloud == "aws":
            print("Destroying AWS resources...")
            os.chdir(f"../{args.cloud}-deployment")
            run_in_bash("terraform destroy -auto-approve")
            os.remove(f"{ssh_key_name}.pub")
            os.remove(f"{ssh_key_name}")
    else:
        print("Invalid action. Nothing to do.")

