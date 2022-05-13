# Security architecture

## Encryption

Pinakes uses encryption to protect sensitive data stored in the database.

Pinakes uses [Fernet](https://github.com/fernet/spec/) algorithm provided
by the [cryptography](https://cryptography.io/) package for authenticated encryption (AE)
of the sensitive data stored in the database.

Fernet uses Encrypt-then-MAC (EtM) scheme based on `AES-128-CBC` for encryption with `PKCS7` padding
and `HMAC-SHA256` for authentication. 

### Configuration

Pinakes uses `PINAKES_DB_ENCRYPTION_KEYS` environment variable to set encryption keys for the application.

The environment variable is a colon (`:`) separated string of one or more encryption keys. 
The first key is a primary key used for decryption and encryption of saved data and the following keys are
secondary keys, used for decryption of existing data only.

```
PINAKES_DB_ENCRYPTION_KEYS={PRIMARY_KEY}[(:{SECONDARY_KEY})...]
```

### Generating encryption key

Before running the application you need to generate a database encryption key. 
It is a URL-safe base64 encoded 32-byte key. 
Pinakes provides a convenient tool to generate one:

```shell
$ python manage.py generate_encryption_key
5DU16...
```

Copy this key and use it to set `PINAKES_DB_ENCRYPTION_KEYS` environment variable.

Or you can generate it programmatically:

Python:
```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
```

Shell:
```shell
$ head -c32 /dev/urandom | base64 | tr '+/' '-_'
```

### Rotating encryption key

In some cases you may want to generate a new encryption key and replace with it the old one.

First generate a new key:

```shell
$ python manage.py generate_encryption_key
```

Then amend your application configuration. Put the new key to the front of
`PINAKES_DB_ENCRYPTION_KEYS` environment variable and restart or redeploy the application:

```
PINAKES_DB_ENCRYPTION_KEYS={NEW_KEY}:{OLD_KEY}
```

Now any new data or updates to existing data are encrypted with the new key when saved to the database. 
An old key is still used for existing data that is read from the database.

:warning: Do not delete an old encryption key if any data exists in the database that was encrypted with it,
otherwise the data is not recoverable. To ensure all the data is encrypted follow the instruction below.

### Re-encrypting the database

To re-encrypt all relevant database records with the new (primary) encryption key run:

```shell
$ python manage.py reencrypt_database
```

Now any secondary encryption keys may be deleted.