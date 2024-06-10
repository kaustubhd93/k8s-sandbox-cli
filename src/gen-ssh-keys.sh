#!/bin/bash
base_dir="/tmp/k8s-sandbox-cli"
ssh_keys_dir="$base_dir/keys"
ssh_key_name="k8s-sandbox"

create_ssh_keys () {
    if [ ! -d $ssh_keys_dir ]; then
        mkdir -p $ssh_keys_dir
    fi
    if [ ! -f $ssh_keys_dir/$ssh_key_name ]; then
        ssh-keygen -t rsa -b 4096 -C "k8s-sandbox" -f $ssh_keys_dir/$ssh_key_name -N ""
    else
        echo "SSH key file already exists"
    fi
}

create_ssh_keys