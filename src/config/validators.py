"""Input validation for deployment configuration."""

from __future__ import annotations

import re

from src.exceptions import DomainValidationError

_LABEL_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$")

_MAX_DOMAIN_LENGTH = 253
_MAX_LABEL_LENGTH = 63
_MIN_LABEL_COUNT = 2


def validate_domain(domain: str) -> None:
    """Validate that a domain is a plausible FQDN.

    Raises:
        DomainValidationError: If the domain is malformed.
    """
    if len(domain) > _MAX_DOMAIN_LENGTH:
        raise DomainValidationError(
            f"Domain too long (max {_MAX_DOMAIN_LENGTH} characters): {domain}"
        )

    labels = domain.split(".")
    if len(labels) < _MIN_LABEL_COUNT:
        raise DomainValidationError(
            f"Domain must contain at least {_MIN_LABEL_COUNT} labels "
            f"(e.g. journal.example.com): {domain}"
        )

    for label in labels:
        if not label or len(label) > _MAX_LABEL_LENGTH or not _LABEL_RE.match(label):
            raise DomainValidationError(f"Invalid domain label '{label}' in: {domain}")


def extract_subdomain(domain: str) -> str:
    """Extract the first label from a FQDN (e.g. 'journal1.example.com' -> 'journal1').

    Raises:
        DomainValidationError: If the subdomain is invalid.
    """
    subdomain = domain.split(".")[0]
    if not subdomain or subdomain in (".", ".."):
        raise DomainValidationError(f"Invalid subdomain extracted from '{domain}'")
    return subdomain
