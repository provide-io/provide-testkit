#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Crypto Testing Fixtures for Foundation.

Provides comprehensive pytest fixtures for testing certificate functionality,
including valid/invalid certificates, keys, chains, and edge cases."""

from pathlib import Path
from urllib.request import pathname2url

import pytest

from provide.foundation import logger
from provide.foundation.crypto import Certificate


@pytest.fixture(scope="module")
def client_cert() -> Certificate:
    """Create a client certificate for testing."""
    cert_pem = """-----BEGIN CERTIFICATE-----
MIIByTCCAU6gAwIBAgIUViyRwlRAQT/9aKhp7pg3PaiVY4YwCgYIKoZIzj0EAwIw
KDESMBAGA1UEAwwJbG9jYWxob3N0MRIwEAYDVQQKDAlIYXNoaUNvcnAwHhcNMjYw
MzIxMjI1NTEzWhcNMzMwMzAzMjI1NTEzWjAoMRIwEAYDVQQDDAlsb2NhbGhvc3Qx
EjAQBgNVBAoMCUhhc2hpQ29ycDB2MBAGByqGSM49AgEGBSuBBAAiA2IABHjtl/ce
3hCcuupZU9PrYnd/yfzFvkI016NbaJw3WUj5kIusbuarhJTnPpDs51OhRu7s50KB
5+SjTEKYoxLbLQyq0ZL89GWjiLYg7vNR3h+czRPNPHmCF84n5PYM3ksZa6M5MDcw
FAYDVR0RBA0wC4IJbG9jYWxob3N0MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/
BAQDAgEGMAoGCCqGSM49BAMCA2kAMGYCMQD4hLWjDkh2McMFetNEkA3ugakBRcAV
eWuh8SZNI8FcrpVzTqK5WXU2zL4X+jOkMAYCMQD90uDgdb5Lu0nMbFOdj9YeLoz4
7T1CZVFOiK5PEoVh36FCKpIwMJmCICWf1DNd0zc=
-----END CERTIFICATE-----"""

    key_pem = """-----BEGIN PRIVATE KEY-----
MIG2AgEAMBAGByqGSM49AgEGBSuBBAAiBIGeMIGbAgEBBDCDH4nvkbjXaAqDrVll
BwYkt3wAuuB9L3vdEjgQlBzUwU58+ddSyHdyrghVSHBYDd+hZANiAAR47Zf3Ht4Q
nLrqWVPT62J3f8n8xb5CNNejW2icN1lI+ZCLrG7mq4SU5z6Q7OdToUbu7OdCgefk
o0xCmKMS2y0MqtGS/PRlo4i2IO7zUd4fnM0TzTx5ghfOJ+T2DN5LGWs=
-----END PRIVATE KEY-----"""

    logger.debug(f"Created CLIENT_CERT fixture: {cert_pem[:30]}...")
    return Certificate.from_pem(cert_pem=cert_pem, key_pem=key_pem)


@pytest.fixture(scope="module")
def server_cert() -> Certificate:
    """Create a server certificate for testing."""
    cert_pem = """-----BEGIN CERTIFICATE-----
MIIBxzCCAU6gAwIBAgIUaselp89UfYM1c2ahi+6sdya8IAkwCgYIKoZIzj0EAwIw
KDESMBAGA1UEAwwJbG9jYWxob3N0MRIwEAYDVQQKDAlIYXNoaUNvcnAwHhcNMjYw
MzIxMjI1NTEzWhcNMzMwMzAzMjI1NTEzWjAoMRIwEAYDVQQDDAlsb2NhbGhvc3Qx
EjAQBgNVBAoMCUhhc2hpQ29ycDB2MBAGByqGSM49AgEGBSuBBAAiA2IABOmgiTWG
tRxhIjCCxesLcd9h3uOjQ7nnmHyHpcx1JTnHWlMj/n4q0MmGQ2P0WWDjWUQRp+GP
yUWQHsldWssM+Rip+2YGyF3Qr8qhhV19B19O6mOrhD1mryoJwWPsBoSyGaM5MDcw
FAYDVR0RBA0wC4IJbG9jYWxob3N0MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/
BAQDAgEGMAoGCCqGSM49BAMCA2cAMGQCMGZDUL1MTtdXBS/jlwI3QDIl2/j7HdZ1
NOkJJ0P5SFnChEWfe1UBQbSuOdVLpGBmVgIwHTd20xKYKTxycH2Lv16YexbNucsP
U8rLvS6Cgml+Hn/O2OUhCN9QvC3vKD8AJEK5
-----END CERTIFICATE-----"""

    key_pem = """-----BEGIN PRIVATE KEY-----
MIG2AgEAMBAGByqGSM49AgEGBSuBBAAiBIGeMIGbAgEBBDCmrYqEfbqUiQyFSeW8
X1AVTFEEsNA+YdiN0KNauS5T0TwhQJdawjTB8157TWDXobqhZANiAATpoIk1hrUc
YSIwgsXrC3HfYd7jo0O555h8h6XMdSU5x1pTI/5+KtDJhkNj9Flg41lEEafhj8lF
kB7JXVrLDPkYqftmBshd0K/KoYVdfQdfTupjq4Q9Zq8qCcFj7AaEshk=
-----END PRIVATE KEY-----"""

    logger.debug(f"Created SERVER_CERT fixture: {cert_pem[:30]}...")
    return Certificate.from_pem(cert_pem=cert_pem, key_pem=key_pem)


@pytest.fixture(scope="module")
def ca_cert() -> Certificate:
    """Create a self-signed CA certificate for testing."""
    return Certificate.create_ca(
        common_name="Test CA", organization_name="Test Organization", validity_days=365
    )


@pytest.fixture(scope="module")
def valid_key_pem(client_cert: Certificate) -> str:
    """Get a valid key PEM from the client cert fixture."""
    result: str = client_cert.key_pem
    return result


@pytest.fixture
def valid_cert_pem(client_cert: Certificate) -> str:
    """Get a valid certificate PEM from the client cert fixture."""
    result: str = client_cert.cert_pem
    return result


@pytest.fixture
def invalid_key_pem() -> str:
    """Returns an invalid PEM key."""
    return "INVALID KEY DATA"


@pytest.fixture
def invalid_cert_pem() -> str:
    """Returns an invalid PEM certificate."""
    return "INVALID CERTIFICATE DATA"


@pytest.fixture
def malformed_cert_pem() -> str:
    """Returns a PEM certificate with incorrect headers."""
    return "-----BEGIN CERT-----\nMALFORMED DATA\n-----END CERT-----"


@pytest.fixture
def empty_cert() -> str:
    """Returns an empty certificate string."""
    return ""


@pytest.fixture
def temporary_cert_file(tmp_path: Path, client_cert: Certificate) -> str:
    """Creates a temporary file containing the client certificate."""
    cert_file = tmp_path / "client_cert.pem"
    cert_file.write_text(client_cert.cert_pem)
    # Handle Windows drive letters in file URIs
    cert_path = Path(cert_file)
    if cert_path.drive:  # Windows path with drive letter
        return f"file:///{pathname2url(str(cert_file))}"
    return f"file://{cert_file}"


@pytest.fixture
def temporary_key_file(tmp_path: Path, client_cert: Certificate) -> str:
    """Creates a temporary file containing the client private key."""
    key_file = tmp_path / "client_key.pem"
    key_file.write_text(client_cert.key_pem)
    # Handle Windows drive letters in file URIs
    key_path = Path(key_file)
    if key_path.drive:  # Windows path with drive letter
        return f"file:///{pathname2url(str(key_file))}"
    return f"file://{key_file}"


@pytest.fixture
def cert_with_windows_line_endings(client_cert: Certificate) -> str:
    """Returns a certificate PEM with Windows line endings."""
    pem: str = client_cert.cert_pem
    return pem.replace("\n", "\r\n")


@pytest.fixture
def cert_with_utf8_bom(client_cert: Certificate) -> str:
    """Returns a certificate PEM with UTF-8 BOM."""
    pem: str = client_cert.cert_pem
    return "\ufeff" + pem


@pytest.fixture
def cert_with_extra_whitespace(client_cert: Certificate) -> str:
    """Returns a certificate PEM with extra whitespace."""
    return f"   {client_cert.cert_pem}   \n\n  "


@pytest.fixture(scope="module")
def external_ca_pem() -> str:
    """Provides an externally generated CA certificate PEM."""
    return """-----BEGIN CERTIFICATE-----
MIIB4TCCAYegAwIBAgIJAPZ9vcVfR8AdMAoGCCqGSM49BAMCMFExCzAJBgNVBAYT
AlVTMQswCQYDVQQIDAJDQTEUMBIGA1UEBwwLU2FuIEZyYW5jaXNjbzEOMAwGA1UE
CgwFTXlPcmcxEzARBgNVBAMMCkV4dGVybmFsIENBMB4XDTI0MDgwMjEwNTgwMVoX
DTM0MDczMDEwNTgwMVowUTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMREwDwYD
VQQHDAhTYW5EaWVnbzEOMAwGA1UECgwFTXlPcmcxEzARBgNVBAMMCkV4dGVybmFs
IENBMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAEgyF5Y8upm+M3ZzO8P4n7q2sS+L4c
mhl5XGg3vIOwFf7lG8XZCgJ6Xy4t1t8oD3zY0m9X8H8Z4YhY7K6b7c8Y7Xv6Y9fV
Q8M7Jg9nJ0x5c1N40zQwZzKjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNVHRMBAf8E
BTADAQH/MB0GA1UdDgQWBBTGX00Gq7b09y/0C9eK0XgJp0mY7DAKBggqhkjOPQQD
AgNJADBGAiEAx1xH/b83/u5t7r29a/THZnFjQ7pvT2N0L4hG4BgGgXACIQD02W2+
MHB78ZWM+JOgikYj99qD6nLp0nkMyGmkSC7RYg==
-----END CERTIFICATE-----"""


# 🧪✅🔚
