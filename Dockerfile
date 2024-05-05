FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip wget gpg zip unzip openssh-client && \
    apt-get clean

RUN wget https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip && \
    unzip terraform_1.7.5_linux_amd64.zip && \
    mv terraform /usr/bin/ && \
    rm terraform_1.7.5_linux_amd64.zip

WORKDIR /app/src/

COPY . /app

RUN pip install -r /app/src/requirements.txt

ENTRYPOINT ["python3", "k8s-sandbox-cli.py"]