"""
Automatically encrypt and decrypt a field with a KMIP KMS provider.
"""
import configuration_queryable as configuration
from pprint import pprint
from bson.codec_options import CodecOptions
from pymongo import MongoClient
from pymongo.encryption import ClientEncryption
from pymongo.encryption_options import AutoEncryptionOpts

def configure_data_keys(kmip_configuration):
    db_name, coll_name = configuration.key_vault_namespace.split(".", 1)
    key_vault_client = MongoClient(configuration.connection_uri)
    key_vault_client[db_name][coll_name].create_index(
        [("keyAltNames", 1)],unique=True,partialFilterExpression={"keyAltNames": {"$exists": True}}
    )
    client_encryption = ClientEncryption(
        kmip_configuration["kms_providers"],
        configuration.key_vault_namespace,
        MongoClient(configuration.connection_uri),
        CodecOptions(),
        kms_tls_options=kmip_configuration["kms_tls_options"]
    )

    # Create a new data key and json schema for the encryptedField.
    data_key_id_1 = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_1'])

    data_key_id_2 = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_2'])

    data_key_id_3 = client_encryption.create_data_key(
        'kmip', key_alt_names=['pymongo_encryption_example_3'])

    encryption_data_keys = {"key1": data_key_id_1,"key2":data_key_id_2, "key3":data_key_id_3}

    return encryption_data_keys

def configure_queryable_session(encrypted_fields_schema):
    auto_encryption = AutoEncryptionOpts(
        configuration.kms_providers,
        configuration.key_vault_namespace,
        encrypted_fields_map=encrypted_fields_schema,
        kms_tls_options=configuration.kms_tls_options,
        schema_map=None
        
    )
    secure_client = MongoClient(configuration.connection_uri,auto_encryption_opts=auto_encryption)
    return secure_client;

def create_schema(data_keys):
    # We are creating a encrypted_fields_map that has an validation schema attached, 
    # that uses the encrypt attribute to define which fields should be encrypted.
    encrypted_db_name, encrypted_coll_name = configuration.encrypted_namespace.split(".", 1)
    encrypted_fields_map = {
        f"{encrypted_db_name}.{encrypted_coll_name}": {
            "fields": [
                {
                    "keyId": data_keys["key1"],
                    "path": "contact.email",
                    "bsonType": "string",
                    "queries": {"queryType": "equality"},
                },
                {
                    "keyId": data_keys["key2"],
                    "path": "contact.mobile",
                    "bsonType": "string",
                    "queries": {"queryType": "equality"},
                },
                {
                    "keyId": data_keys["key3"],
                    "path": "ssn",
                    "bsonType": "string",
                    "queries": {"queryType": "equality"},
                }
            ],
        },
    }
    return encrypted_fields_map

def reset():    
    db_name, coll_name = configuration.encrypted_namespace.split(".", 1)
    mongo_client = MongoClient(configuration.connection_uri)
    mongo_client.drop_database(db_name)

def create_user(secure_client):
    # Create Encrypted Collection
    db_name, coll_name = configuration.encrypted_namespace.split(".", 1)
    db=secure_client[db_name]
    db.create_collection(coll_name)

    # Insert encrypted record
    coll = secure_client[db_name][coll_name]
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
    print("Queryable Encryption: Decrypted document:")
    print("===================")    
    pprint((coll.find_one({"ssn":"901-01-0001"})))
    unencrypted_coll = MongoClient(configuration.connection_uri)[db_name][coll_name]
    print("Queryable Encryption: Encrypted document:")
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
    #4 Create Schema for Queryable Encryption, will be stored in database
    encrypted_fields_map = create_schema(data_keys_config)
    #5 Configure Encrypted Client
    secure_client = configure_queryable_session(encrypted_fields_map)
    #6 Run Query
    create_user(secure_client)
if __name__ == "__main__":
    main()