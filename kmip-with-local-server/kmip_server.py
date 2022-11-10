"""
Start a development KMIP server.
Run from the kmip directory.
"""
from kmip.services.server import KmipServer
import logging

if __name__ == "__main__":
    server = KmipServer(
        hostname="localhost",
        port=5696,
        certificate_path="certs/server.pem",
        ca_path="certs/ca.pem",
        config_path=None,
        log_path='pykmip.log',
        logging_level=logging.DEBUG,
    )

    with server:
        print ("Starting KMS KMIP server")
        server.serve()
