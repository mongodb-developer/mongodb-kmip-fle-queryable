# Start Vault and unseal Vault providing config containing reference to HashiCorp license.txt
reset()
{
    pkill -9 vault
    /kmip/cleanup.sh
}
startAndInitializeKeyVault()
{
    reset
    export VAULT_ADDR=http://127.0.0.1:8200
    vault server -config=kmip-with-hashicorp-key-vault/vault/config.hcl &
    sleep 5
    vault operator init -key-shares=1 -key-threshold=1 -format=json > init.json
    unseal_keys=$(jq -r .unseal_keys_b64[0] < init.json)
    root_token=$(jq -r .root_token < init.json)
    vault operator unseal $unseal_keys
    vault login token=$root_token
    # Configure KMIP Secrets Engine for FLE
    vault secrets enable -path=demo/kmip kmip
    vault write demo/kmip/config listen_addrs=0.0.0.0:5697 default_tls_client_key_type=rsa default_tls_client_key_bits=2048 server_ips=127.0.0.1 tls_ca_key_type=rsa tls_ca_key_bits=2048
    # Configure Role and Scope and Certs
    vault read demo/kmip/ca
    vault write -f demo/kmip/scope/mongodb
}
configureRolesAndScopes()
{
    EncryptionMode=$1
    vault write demo/kmip/scope/mongodb/role/${EncryptionMode} tls_client_key_bits=2048 tls_client_key_type=rsa operation_all=true
    vault write -format=json \
        demo/kmip/scope/mongodb/role/${EncryptionMode}/credential/generate \
        format=pem > ${EncryptionMode}_credential.json
    serial_number=$(jq -r .data.serial_number < ${EncryptionMode}_credential.json)
    jq -r .data.certificate < ${EncryptionMode}_credential.json > kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-ca.pem
    jq -r .data.private_key < ${EncryptionMode}_credential.json > kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-key.pem    
    cat kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-ca.pem kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-key.pem > kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-client.pem
    vault read demo/kmip/scope/mongodb/role/${EncryptionMode}/credential/lookup \serial_number=$serial_number -format=json > ${EncryptionMode}_ca_chain.json
    jq -r .data.certificate < ${EncryptionMode}_ca_chain.json > kmip-with-hashicorp-key-vault/vault/certs/${EncryptionMode}/vv-ca.pem    
    rm -rf *.json
    echo "==========================================="
    echo "Access vault console http://localhost:8200/"
    echo "Root Token: ${root_token}"
    echo "==========================================="    
}

option="${1}"
case ${option} in -f) 
echo "Configuring Roles and Scopes for FLE Encryption"
startAndInitializeKeyVault
configureRolesAndScopes FLE;;
-q) 
echo "Configuring Roles and Scopes for Queryable Encryption"
startAndInitializeKeyVault
configureRolesAndScopes QUERYABLE;;
-a) 
echo "Configuring Roles and Scopes for FLE and Queryable Encryption"
startAndInitializeKeyVault
configureRolesAndScopes FLE
configureRolesAndScopes QUERYABLE;;
*)
echo ""
echo "To start and configure Hashicorp Key Vault with KMIP Secrets Engine"
echo -e "\033[1mstart_and_configure [options]\033[0m"
echo ""
echo "-a Configure KMIP Secrets Engine for Queryable and FLE encryption"
echo "-f Configure KMIP Secrets Engine for FLE encryption"
echo "-q Configure KMIP Secrets Engine for Queryable encryption"
echo "";;
esac
