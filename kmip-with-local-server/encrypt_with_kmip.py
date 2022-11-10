"""
Automatically encrypt and decrypt a field with a KMIP KMS provider.
Example modified from https://pymongo.readthedocs.io/en/stable/examples/encryption.html#providing-local-automatic-encryption-rules
"""
import os

from bson.codec_options import CodecOptions
from bson import json_util

from pymongo import MongoClient
from pymongo.encryption import (Algorithm,
                                ClientEncryption)
from pymongo.encryption_options import AutoEncryptionOpts

def create_json_schema_file(kms_providers, key_vault_namespace,
                            key_vault_client, kms_tls_options=None):
    client_encryption = ClientEncryption(
        kms_providers,
        key_vault_namespace,
        key_vault_client,
        # The CodecOptions class used for encrypting and decrypting.
        # This should be the same CodecOptions instance you have configured
        # on MongoClient, Database, or Collection. We will not be calling
        # encrypt() or decrypt() in this example so we can use any
        # CodecOptions.
        CodecOptions(),
        kms_tls_options=kms_tls_options)

    # Create a new data key and json schema for the encryptedField.
    # https://dochub.mongodb.org/core/client-side-field-level-encryption-automatic-encryption-rules
    data_key_id = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_1'])
    schema = {
        "properties": {
            "encryptedField": {
                "encrypt": {
                    "keyId": [data_key_id],
                    "bsonType": "string",
                    "algorithm":
                        Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic
                }
            }
        },
        "bsonType": "object"
    }
    # Use CANONICAL_JSON_OPTIONS so that other drivers and tools will be
    # able to parse the MongoDB extended JSON file.
    json_schema_string = json_util.dumps(
        schema, json_options=json_util.CANONICAL_JSON_OPTIONS)

    with open('jsonSchema.json', 'w') as file:
        file.write(json_schema_string)


def main():
    # The MongoDB namespace (db.collection) used to store the
    # encrypted documents in this example.
    encrypted_namespace = "test.coll"

    # Configure the "kmip" provider.
    kms_providers = {
        "kmip": {
            "endpoint": "localhost:5696"
        }
    }

    kms_tls_options = {
        "kmip": {
            "tlsCAFile": "certs/ca.pem",
            "tlsCertificateKeyFile": "certs/client.pem"
        }
    }
    # The MongoDB namespace (db.collection) used to store
    # the encryption data keys.
    key_vault_namespace = "keyvault.datakeys"
    key_vault_db_name, key_vault_coll_name = key_vault_namespace.split(".", 1)

    # The MongoClient used to access the key vault (key_vault_namespace).
    key_vault_client = MongoClient("mongodb+srv://<USER>:<PWD>@<CLUSTER-NAME>?retryWrites=true&w=majority")
    key_vault = key_vault_client[key_vault_db_name][key_vault_coll_name]
    # Ensure that two data keys cannot share the same keyAltName.
    key_vault.drop()
    key_vault.create_index(
        "keyAltNames",
        unique=True,
        partialFilterExpression={"keyAltNames": {"$exists": True}})

    create_json_schema_file(
        kms_providers, key_vault_namespace, key_vault_client, kms_tls_options=kms_tls_options)

    # Load the JSON Schema and construct the local schema_map option.
    with open('jsonSchema.json', 'r') as file:
        json_schema_string = file.read()
    json_schema = json_util.loads(json_schema_string)
    schema_map = {encrypted_namespace: json_schema}

    auto_encryption_opts = AutoEncryptionOpts(
        kms_providers, key_vault_namespace, schema_map=schema_map, kms_tls_options=kms_tls_options)

    client = MongoClient("mongodb+srv://<USER>:<PASSWORD>@<CLUSTER>?retryWrites=true&w=majority",auto_encryption_opts=auto_encryption_opts)
    db_name, coll_name = encrypted_namespace.split(".", 1)
    coll = client[db_name][coll_name]
    # Clear old data
    coll.drop()

    coll.insert_one({"encryptedField": "123456789"})
    print('Decrypted document: %s' % (coll.find_one(),))
    unencrypted_coll = MongoClient("mongodb+srv://<USER>:<PASSWORD>@<CLUSTER>?retryWrites=true&w=majority")[db_name][coll_name]
    print('Encrypted document: %s' % (unencrypted_coll.find_one(),))


if __name__ == "__main__":
    main()