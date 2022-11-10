FROM ubuntu:20.04
ARG DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && \
    apt-get -qy full-upgrade && \
    apt-get install -qy curl && \
    apt-get install -y unzip && \
    apt-get -y install jq    
RUN apt-get update && apt-get install -y gnupg wget

RUN wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.com/apt/ubuntu focal/mongodb-enterprise/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-enterprise.list
RUN wget -qO - https://www.mongodb.org/static/pgp/libmongocrypt.asc | gpg --dearmor >/etc/apt/trusted.gpg.d/libmongocrypt.gpg
RUN echo "deb [ arch=amd64,arm64 ] https://libmongocrypt.s3.amazonaws.com/apt/ubuntu focal/libmongocrypt/1.6 universe" | tee /etc/apt/sources.list.d/libmongocrypt.list

RUN apt-get update && apt-get install -y mongodb-enterprise-cryptd python3.8 python3-pip libmongocrypt0
RUN python3 -m pip install -U pip
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN curl https://releases.hashicorp.com/vault/1.10.0-rc1+ent/vault_1.10.0-rc1+ent_linux_arm64.zip --output vault-ent.zip 
RUN unzip -qq vault-ent.zip
RUN cp vault /usr/bin/vault
RUN rm vault-ent.zip
RUN export VAULT_ADDR=http://127.0.0.1:8200

