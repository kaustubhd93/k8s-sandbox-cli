# Steps required. 

- Settings for ipv4, modprobe and iptables 
```
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system

# Verify modprobe settings
lsmod | grep br_netfilter
lsmod | grep overlay

# verify sysctl settings, values should be set to 1.
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward
```
- prepare container run time and it's dependencies.
- Doc for reference : https://github.com/containerd/containerd/blob/main/docs/getting-started.md
```
# create a folder
mkidr -p /opt/downloads

# download latest release from containerd release page
wget https://github.com/containerd/containerd/releases/download/v1.7.15/containerd-1.7.15-linux-amd64.tar.gz
tar Cxzvf /usr/local containerd-1.7.15-linux-amd64.tar.gz
wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service -O /usr/local/lib/systemd/system/containerd.service
systemctl daemon-reload
systemctl enable --now containerd

# download runc binary
wget https://github.com/opencontainers/runc/releases/download/v1.1.12/runc.amd64 -O /usr/local/sbin/runc
chmod 0755 /usr/local/sbin/runc

# download cni plugins
mkdir -p /opt/cni/bin
wget https://github.com/containernetworking/plugins/releases/download/v1.4.1/cni-plugins-linux-amd64-v1.4.1.tgz
tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.4.1.tgz

# Generate default conf for containerd and change cgroup driver
# https://github.com/containerd/containerd/blob/main/docs/getting-started.md#customizing-containerd
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
systemctl restart containerd
```

- install kubeadm, kubelet and kubectl
```
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg
stat /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
apt-get update
apt-get install -y kubelet kubeadm kubectl
```

- set up k8s cluster with kubeadm
```
kubeadm init --control-plane-endpoint=<private_ip> --apiserver-advertise-address=<private_ip> --pod-network-cidr=192.168.0.0/16
mkdir -p /home/ubuntu/.kube
cp -i /etc/kubernetes/admin.conf /home/ubuntu/.kube/config
chown -R ubuntu. /home/ubuntu/.kube/
```

- deploy cni plugin for pod networking
```
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.2/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.2/manifests/custom-resources.yaml
watch kubectl get pods -n calico-system
```

- Check node status whether ready
```
kubectl get nodes
```

