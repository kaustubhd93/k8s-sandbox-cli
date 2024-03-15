# k8s-sandbox-cli
A command line interface to launch a kubernetes sandbox on your preferred cloud provider

## Instructions  
- Clone the code to your terminal running VS Code.  
- Create an ssh key: `ssh-keygen -t rsa`  
- Install the Remote-SSH extension in VS Code: https://code-visualstudio-com/docs/remote/ssh  
- Modify the `terraform-tfvars` file with your values, including `host_os` which will be `windows` or `linux` (for MacOS or Linux)- Minikube will run best with a t3a-medium or higher EC2 instance with at least 20Gib of storage- **This will cost money!**  
- *Optional*: Modify the `userdata-tpl` script to provide any custom userdata to your instance.  
- `terraform init`  
- `terraform plan`  
- `terraform apply`  
- Use `CTRL+P` in VS Code, search for the `Remote-SSH` extension, and then choose the IP address output from the Terraform script.  
- Follow the prompts to open a new VS Code window that will connect to your instance and provide your very own K8s Sandbox.  
- Run `minikube start` to start Minikube and get your Kubernetes cluster up and running.  
- `terraform destroy` to destroy your infrastructure when you're finished.  

> Initially forked from [morethancertified/kubernetes-sandbox](https://github.com/morethancertified/kubernetes-sandbox)