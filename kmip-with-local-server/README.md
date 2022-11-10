# KMIP Local Server
## Based on
git clone https://github.com/kevinAlbs/pymongo-bootstrap.git# mongodb-csfle-kmip


# Start Container
docker run -p 8200:8200 -it -v ${PWD}:/kmip piepet/mongodb-csfle:latest                   
# From scratch if not data folder exists
vault operator init -key-shares=1 -key-threshold=1

# Start Local KMIP
```
cd ./kmip
python kmip_server.py
```

# Encrypt test
```
python encrypt_with_kmip.py
```



