# Steps required to launch a single k8s node using kubespray
- `cp -rfp inventory/sample inventory/k8-single-node-poc`
- `declare -a IPS=(public_ip_here)`
- install ruamel lib from pip for generating hosts.yaml file
```
ModuleNotFoundError: No module named 'ruamel'
```
- `CONFIG_FILE=inventory/k8s-single-node-poc/hosts.yaml python3 contrib/inventory_builder/inventory.py ${IPS[@]}`
- Files needed to be modified = hosts.yaml, inventory.ini, group_vars/k8s_cluster/k8s-cluster.yml
- make ip and access_ip private in hosts.yaml
- Add `node1 ansible_host=<public_ip>` under `[all]` in inventory.ini
- Add `node1` under `[kube_control_plane]`, `[etcd]`, `[kube_node]` in inventory.ini
- Change `kube_service_addresses` and `kube_pods_subnet`, ensure they have different ip ranges completely.
