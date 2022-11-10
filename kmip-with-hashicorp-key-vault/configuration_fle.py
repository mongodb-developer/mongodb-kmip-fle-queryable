encrypted_namespace = "DEMO-KMIP-FLE.users"
key_vault_namespace = "DEMO-KMIP-FLE.datakeys"
connection_uri = "mongodb+srv://<USER>:<PASSWORD>@<CLUSTER-NAME>?retryWrites=true&w=majority"

# Configure the "kmip" provider.
kms_providers = {
    "kmip": {
        "endpoint": "localhost:5697"
    }
}
kms_tls_options = {
    "kmip": {
        "tlsCAFile": "vault/certs/FLE/vv-ca.pem",
        "tlsCertificateKeyFile": "vault/certs/FLE/vv-client.pem"
    }
}
