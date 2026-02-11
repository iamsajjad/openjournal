"""Tests for domain validation."""

from __future__ import annotations

import pytest

from src.config.validators import extract_subdomain, validate_domain
from src.exceptions import DomainValidationError


class TestValidateDomain:
    """Tests for validate_domain."""

    def test_valid_fqdn(self) -> None:
        validate_domain("ejournal.example.com")

    def test_valid_two_label_domain(self) -> None:
        validate_domain("example.com")

    def test_valid_with_hyphens(self) -> None:
        validate_domain("my-journal.example.com")

    def test_single_label_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="at least"):
            validate_domain("localhost")

    def test_empty_label_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="Invalid domain label"):
            validate_domain("ejournal..com")

    def test_label_too_long_raises(self) -> None:
        domain = "a" * 64 + ".example.com"
        with pytest.raises(DomainValidationError, match="Invalid domain label"):
            validate_domain(domain)

    def test_domain_exceeds_253_chars_raises(self) -> None:
        domain = ".".join(["a" * 50] * 6)
        with pytest.raises(DomainValidationError, match="too long"):
            validate_domain(domain)

    def test_invalid_characters_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="Invalid domain label"):
            validate_domain("ejournal!.example.com")

    def test_leading_hyphen_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="Invalid domain label"):
            validate_domain("-ejournal.example.com")

    def test_trailing_hyphen_raises(self) -> None:
        with pytest.raises(DomainValidationError, match="Invalid domain label"):
            validate_domain("ejournal-.example.com")


class TestExtractSubdomain:
    """Tests for extract_subdomain."""

    def test_extracts_first_label(self) -> None:
        assert extract_subdomain("ejournal.example.com") == "ejournal"

    def test_two_label_domain(self) -> None:
        assert extract_subdomain("example.com") == "example"

    def test_empty_first_label_raises(self) -> None:
        with pytest.raises(DomainValidationError):
            extract_subdomain("..com")
