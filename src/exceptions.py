"""Custom exceptions for OJS deployment operations."""


class DeploymentError(Exception):
    """Base exception for all deployment-related errors."""


class DomainValidationError(DeploymentError):
    """Raised when a domain name fails validation."""


class TemplateError(DeploymentError):
    """Raised when template operations fail."""


class OwnershipError(DeploymentError):
    """Raised when file ownership operations fail."""


class ConfigurationError(DeploymentError):
    """Raised when configuration is invalid or incomplete."""


class SecretGenerationError(DeploymentError):
    """Raised when cryptographic secret generation fails."""
