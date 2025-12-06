"""Unit tests for domain validators."""

import pytest
from uuid import UUID, uuid4

from tenant_service.domain.validators import (
    validate_email,
    validate_folder_name,
    validate_folder_path,
    validate_pagination,
    validate_retention_period,
    validate_storage_provider,
    validate_subscription_plan,
    validate_tenant_name,
    validate_uuid,
)
from tenant_service.domain.enums.subscription_plan import SubscriptionPlan
from tenant_service.domain.enums.retention_types import RetentionUnit
from tenant_service.exceptions import ValidationError


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Valid emails should not raise."""
        validate_email("user@example.com")
        validate_email("user.name@example.co.uk")
        validate_email("user+tag@example.org")

    def test_none_email_valid(self):
        """None is valid for optional emails."""
        validate_email(None)

    def test_invalid_email_format(self):
        """Invalid email formats should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid-email")
        assert "email format" in exc_info.value.message.lower()

    def test_invalid_email_no_domain(self):
        """Email without domain should raise."""
        with pytest.raises(ValidationError):
            validate_email("user@")

    def test_invalid_email_no_at(self):
        """Email without @ should raise."""
        with pytest.raises(ValidationError):
            validate_email("userexample.com")


class TestValidateSubscriptionPlan:
    """Tests for subscription plan validation."""

    def test_valid_plans(self):
        """Valid plan names should return enum value."""
        assert validate_subscription_plan("starter") == SubscriptionPlan.STARTER
        assert validate_subscription_plan("professional") == SubscriptionPlan.PROFESSIONAL
        assert validate_subscription_plan("enterprise") == SubscriptionPlan.ENTERPRISE

    def test_case_insensitive(self):
        """Plan validation should be case-insensitive."""
        assert validate_subscription_plan("STARTER") == SubscriptionPlan.STARTER
        assert validate_subscription_plan("Professional") == SubscriptionPlan.PROFESSIONAL

    def test_invalid_plan(self):
        """Invalid plan should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_plan("free")
        assert "valid_plans" in exc_info.value.details


class TestValidateTenantName:
    """Tests for tenant name validation."""

    def test_valid_names(self):
        """Valid tenant names should pass."""
        assert validate_tenant_name("acme-corp") == "acme-corp"
        assert validate_tenant_name("company_123") == "company_123"
        assert validate_tenant_name("MyCompany") == "MyCompany"

    def test_too_short(self):
        """Names under 4 chars should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_tenant_name("abc")
        assert "at least 4" in exc_info.value.message

    def test_too_long(self):
        """Names over 64 chars should raise."""
        with pytest.raises(ValidationError):
            validate_tenant_name("a" * 65)

    def test_invalid_characters(self):
        """Names with invalid chars should raise."""
        with pytest.raises(ValidationError):
            validate_tenant_name("company@name")


class TestValidateFolderName:
    """Tests for folder name validation."""

    def test_valid_names(self):
        """Valid folder names should pass."""
        assert validate_folder_name("Documents") == "Documents"
        assert validate_folder_name("My Files") == "My Files"
        assert validate_folder_name("2024-invoices") == "2024-invoices"

    def test_empty_name(self):
        """Empty name should raise."""
        with pytest.raises(ValidationError):
            validate_folder_name("")

    def test_path_separator(self):
        """Names with path separators should raise."""
        with pytest.raises(ValidationError):
            validate_folder_name("folder/subfolder")
        with pytest.raises(ValidationError):
            validate_folder_name("folder\\subfolder")

    def test_invalid_characters(self):
        """Names with invalid chars should raise."""
        for char in ':*?"<>|':
            with pytest.raises(ValidationError):
                validate_folder_name(f"folder{char}name")


class TestValidateFolderPath:
    """Tests for folder path validation."""

    def test_valid_paths(self):
        """Valid paths should pass."""
        assert validate_folder_path("/Documents") == "/Documents"
        assert validate_folder_path("/Documents/Invoices") == "/Documents/Invoices"

    def test_missing_leading_slash(self):
        """Path without leading slash should raise."""
        with pytest.raises(ValidationError):
            validate_folder_path("Documents")

    def test_normalize_double_slash(self):
        """Double slashes should be normalized."""
        assert validate_folder_path("/Documents//Invoices") == "/Documents/Invoices"


class TestValidateUuid:
    """Tests for UUID validation."""

    def test_valid_uuid_object(self):
        """UUID object should pass through."""
        test_uuid = uuid4()
        assert validate_uuid(test_uuid) == test_uuid

    def test_valid_uuid_string(self):
        """Valid UUID string should be converted."""
        uuid_str = "12345678-1234-1234-1234-123456789abc"
        result = validate_uuid(uuid_str)
        assert isinstance(result, UUID)
        assert str(result) == uuid_str

    def test_invalid_uuid_string(self):
        """Invalid UUID string should raise."""
        with pytest.raises(ValidationError):
            validate_uuid("not-a-uuid")

    def test_invalid_uuid_type(self):
        """Invalid type should raise."""
        with pytest.raises(ValidationError):
            validate_uuid(12345)


class TestValidateRetentionPeriod:
    """Tests for retention period validation."""

    def test_valid_days(self):
        """Valid day-based period should return days."""
        assert validate_retention_period(30, RetentionUnit.DAYS) == 30

    def test_valid_months(self):
        """Months should be converted to days."""
        assert validate_retention_period(12, RetentionUnit.MONTHS) == 360

    def test_valid_years(self):
        """Years should be converted to days."""
        assert validate_retention_period(7, RetentionUnit.YEARS) == 2555

    def test_period_too_short(self):
        """Period below minimum should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_retention_period(0, RetentionUnit.DAYS)
        assert "at least" in exc_info.value.message

    def test_period_too_long(self):
        """Period above maximum should raise."""
        with pytest.raises(ValidationError):
            validate_retention_period(200, RetentionUnit.YEARS)


class TestValidatePagination:
    """Tests for pagination validation."""

    def test_valid_pagination(self):
        """Valid pagination should pass."""
        skip, limit = validate_pagination(0, 100)
        assert skip == 0
        assert limit == 100

    def test_custom_pagination(self):
        """Custom valid values should pass."""
        skip, limit = validate_pagination(50, 25)
        assert skip == 50
        assert limit == 25

    def test_negative_skip(self):
        """Negative skip should raise."""
        with pytest.raises(ValidationError):
            validate_pagination(-1, 100)

    def test_zero_limit(self):
        """Zero limit should raise."""
        with pytest.raises(ValidationError):
            validate_pagination(0, 0)

    def test_exceed_max_limit(self):
        """Limit exceeding max should raise."""
        with pytest.raises(ValidationError):
            validate_pagination(0, 2000)


class TestValidateStorageProvider:
    """Tests for storage provider validation."""

    def test_valid_providers(self):
        """Valid providers should pass."""
        assert validate_storage_provider("s3") == "s3"
        assert validate_storage_provider("azure_blob") == "azure_blob"
        assert validate_storage_provider("gcs") == "gcs"
        assert validate_storage_provider("local") == "local"

    def test_case_insensitive(self):
        """Provider should be case-insensitive."""
        assert validate_storage_provider("S3") == "s3"
        assert validate_storage_provider("AZURE_BLOB") == "azure_blob"

    def test_invalid_provider(self):
        """Invalid provider should raise."""
        with pytest.raises(ValidationError) as exc_info:
            validate_storage_provider("dropbox")
        assert "valid_providers" in exc_info.value.details
