encrypted_namespace = "DEMO-KMIP-QUERYABLE.users"
key_vault_namespace = "DEMO-KMIP-QUERYABLE.datakeys"
connection_uri = "mongodb+srv://<USER>:<PASSWORD>@<CLUSTER-NAME>?retryWrites=true&w=majority"

# Configure the "kmip" provider.
kms_providers = {
    "kmip": {
        "endpoint": "localhost:5697"
    }
}
kms_tls_options = {
    "kmip": {
        "tlsCAFile": "vault/certs/QUERYABLE/vv-ca.pem",
        "tlsCertificateKeyFile": "vault/certs/QUERYABLE/vv-client.pem"
    }
}
