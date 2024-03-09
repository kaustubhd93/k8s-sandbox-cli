# kubernetes-sandbox
A command line interface to launch a kubernetes sandbox on your preferred cloud provider

## Instructions  
1. Clone the code to your terminal running VS Code.  
3. Create an ssh key: `ssh-keygen -t rsa`  
4. Install the Remote-SSH extension in VS Code: https://code.visualstudio.com/docs/remote/ssh   
5. Modify the `terraform.tfvars` file with your values, including `host_os` which will be `windows` or `linux` (for MacOS or Linux). Minikube will run best with a t3.medium or higher EC2 instance with at least 20Gib of storage. **This will cost money!**  
6. *Optional*: Modify the `userdata.tpl` script to provide any custom userdata to your instance.   
7. `terraform init`  
8. `terraform plan`  
9. `terraform apply`  
10. Use `CTRL+P` in VS Code, search for the `Remote-SSH` extension, and then choose the IP address output from the Terraform script.  
11. Follow the prompts to open a new VS Code window that will connect to your instance and provide your very own K8s Sandbox.
12. Once you're connected, you may need to add your user to the Docker group: `sudo usermod -aG docker $USER && newgrp docker`
13. Run `minikube start` to start Minikube and get your Kubernetes cluster up and running. 
14. `terraform destroy` to destroy your infrastructure when you're finished.  
