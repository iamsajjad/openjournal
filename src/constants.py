"""Constants for OJS deployment."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Process exit codes."""

    SUCCESS = 0
    USER_ERROR = 1
    PERMISSION_ERROR = 2


TEMPLATE_DIR = "journal"

# OJS runs as www-data (uid 33, gid 33)
WWW_DATA_UID = 33
WWW_DATA_GID = 33

# MariaDB runs as mysql (uid 999, gid 999)
MYSQL_UID = 999
MYSQL_GID = 999

# Placeholder tokens used in template files
TOKEN_DOMAIN = "{{DOMAIN}}"
TOKEN_JOURNAL = "{{JOURNAL}}"
TOKEN_DATABASE = "{{DATABASE}}"
TOKEN_DB_HOST = "{{DB_HOST}}"
TOKEN_ACME_EMAIL = "{{ACME_EMAIL}}"
TOKEN_LOCALE = "{{LOCALE}}"
TOKEN_DB_PASSWORD = "{{DB_PASSWORD}}"
TOKEN_DB_ROOT_PASSWORD = "{{DB_ROOT_PASSWORD}}"
TOKEN_SALT = "{{SALT}}"
TOKEN_API_KEY_SECRET = "{{API_KEY_SECRET}}"

# Secret generation defaults
DEFAULT_DB_SECRET_LENGTH = 24
DEFAULT_SALT_LENGTH = 32
DEFAULT_API_KEY_LENGTH = 32
