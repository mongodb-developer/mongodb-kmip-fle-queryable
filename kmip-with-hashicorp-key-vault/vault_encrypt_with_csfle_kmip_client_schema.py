"""
Automatically encrypt and decrypt a field with a KMIP KMS provider.
Example modified from https://pymongo.readthedocs.io/en/stable/examples/encryption.html#providing-local-automatic-encryption-rules
"""
import json
from multiprocessing import connection
import os
import configuration_fle as configuration
from pprint import pprint
from bson.codec_options import CodecOptions
from bson import json_util

from pymongo import MongoClient
from pymongo.encryption import (Algorithm,
                                ClientEncryption)
from pymongo.encryption_options import AutoEncryptionOpts

def configure_data_keys(kmip_configuration):
    client_encryption = ClientEncryption(
    kmip_configuration["kms_providers"],
    configuration.key_vault_namespace,
    MongoClient(configuration.connection_uri),
    # The CodecOptions class used for encrypting and decrypting.
    # This should be the same CodecOptions instance you have configured
    # on MongoClient, Database, or Collection. We will not be calling
    # encrypt() or decrypt() in this example so we can use any
    # CodecOptions.
    CodecOptions(),
    kms_tls_options=kmip_configuration["kms_tls_options"])

    # Create a new data key and json schema for the encryptedField.
    # https://dochub.mongodb.org/core/client-side-field-level-encryption-automatic-encryption-rules
    data_key_id_1 = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_1'])

    data_key_id_2 = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_2'])
    encryption_data_keys = {"key1": data_key_id_1,"key2":data_key_id_2}
    return encryption_data_keys

def configure_csfle_schema(data_keys):
    schema = {
    "bsonType": "object",
    "properties": {
        "firstName": { "bsonType": "string" }, 
        "lastName":  { "bsonType": "string" },
        "ssn": {
            "encrypt": {
                "bsonType": "string",
                "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                "keyId": [ data_keys["key1"] ]
            }
        },
        "address": {
            "bsonType": "object",
            "properties": {
                "street" : { "bsonType": "string"  },
                "city"   : { "bsonType": "string"  },
                "state"  : { "bsonType": "string"  },
                "zip"    : { "bsonType": "string" }
            }
        },
        "contact": {
            "bsonType": "object",
            "properties": {
                "email"   : {
                "encrypt": {
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
                    "keyId": [ data_keys["key2"] ]
                }
                },
                "mobile"  : {
                "encrypt": {
                    "bsonType": "string",
                    "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
                    "keyId": [ data_keys["key2"] ]
                }
                }
            },
        },
    }
    }
    return schema
def configure_csfle_session(schema):
    # Load the JSON Schema and construct the local schema_map option.    
    schema_map = {configuration.encrypted_namespace: schema}

    auto_encryption_opts = AutoEncryptionOpts(
        configuration.kms_providers, configuration.key_vault_namespace, schema_map=schema_map, kms_tls_options=configuration.kms_tls_options)
    return auto_encryption_opts

def reset():    
    db_name, coll_name = configuration.encrypted_namespace.split(".", 1)
    mongo_client = MongoClient(configuration.connection_uri)
    mongo_client.drop_database(db_name)

def create_user(csfle_options):
    mongo_client_csfle = MongoClient(configuration.connection_uri,auto_encryption_opts=csfle_options)    
    db_name, coll_name = configuration.encrypted_namespace.split(".", 1)
    coll = mongo_client_csfle[db_name][coll_name]
    # Clear old data
    coll.insert_one({
        "firstName": 'Alan',
        "lastName":  'Turing',
        "ssn":       '901-01-0001',
        "address": {
            "street": '123 Main',
            "city": 'Omaha',
            "zip": '90210'
        },
        "contact": {
            "mobile": '202-555-1212',
            "email":  'alan@example.com'
        }
    })
    print("CSFLE Encryption: Decrypted document:")
    print("===================")    
    pprint((coll.find_one({"ssn":"901-01-0001"})))
    unencrypted_coll = MongoClient(configuration.connection_uri)[db_name][coll_name]
    print("CSFLE Encryption: Encrypted document:")
    print("===================")    
    pprint((unencrypted_coll.find_one()))
        
def configure_kmip_provider():
    return {"kms_providers":configuration.kms_providers,"kms_tls_options":configuration.kms_tls_options}

def main():
    reset()
    #1,2 Configure your KMIP Provider and Certificates
    kmip_provider_config = configure_kmip_provider()
    #3 Configure Encryption Data Keys
    data_keys_config = configure_data_keys(kmip_provider_config)
    #4 Configure JSON Schema
    schema_config = configure_csfle_schema(data_keys_config)
    #5 Run Query
    create_user(configure_csfle_session(schema_config))
if __name__ == "__main__":
    main()