import pytest
import os
import json
from unittest.mock import patch, MagicMock
from lib.secret_management import (
    SecretManager,
    AWSSecretManager,
    VaultSecretManager,
    GCPSecretManager
)

class TestSecretManagement:
    @pytest.fixture
    def mock_aws_secrets(self):
        return {
            "SecretString": json.dumps({
                "api_key": "test-key-123",
                "other_secret": "secret-value"
            })
        }

    @pytest.fixture
    def mock_vault_secrets(self):
        return {
            "data": {
                "data": {
                    "api_key": "test-key-123",
                    "other_secret": "secret-value"
                }
            }
        }

    @pytest.fixture
    def mock_gcp_secrets(self):
        return {
            "payload": {
                "data": "dGVzdC1rZXktMTIz"  # base64 encoded "test-key-123"
            }
        }

    @patch('boto3.client')
    def test_aws_secret_manager(self, mock_boto3, mock_aws_secrets):
        mock_secrets = MagicMock()
        mock_secrets.get_secret_value.return_value = mock_aws_secrets
        mock_boto3.return_value = mock_secrets

        manager = AWSSecretManager(region="us-east-1")
        secret = manager.get_secret("test-secret", "api_key")

        assert secret == "test-key-123"
        mock_secrets.get_secret_value.assert_called_once_with(
            SecretId="test-secret"
        )

    @patch('hvac.Client')
    def test_vault_secret_manager(self, mock_hvac, mock_vault_secrets):
        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_vault_secrets
        mock_hvac.return_value = mock_client

        manager = VaultSecretManager(
            vault_addr="http://vault:8200",
            vault_token="test-token"
        )
        secret = manager.get_secret("secret/test", "api_key")

        assert secret == "test-key-123"
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="test"
        )

    @patch('google.cloud.secretmanager.SecretManagerServiceClient')
    def test_gcp_secret_manager(self, mock_client, mock_gcp_secrets):
        mock_instance = MagicMock()
        mock_instance.access_secret_version.return_value = mock_gcp_secrets
        mock_client.return_value = mock_instance

        manager = GCPSecretManager(project_id="test-project")
        secret = manager.get_secret("test-secret", "api_key")

        assert secret == "test-key-123"
        mock_instance.access_secret_version.assert_called_once()

    def test_secret_redaction(self):
        manager = SecretManager()
        log_content = "API key: test-key-123"
        sanitized = manager.sanitize_logs(log_content)

        assert "test-key-123" not in sanitized
        assert "API key: [REDACTED]" in sanitized

    @pytest.mark.parametrize("manager_class,config", [
        (AWSSecretManager, {"region": "us-east-1"}),
        (VaultSecretManager, {"vault_addr": "http://vault:8200", "vault_token": "test-token"}),
        (GCPSecretManager, {"project_id": "test-project"})
    ])
    def test_secret_manager_initialization(self, manager_class, config):
        manager = manager_class(**config)
        assert manager is not None

    @pytest.mark.parametrize("manager_class,error_type", [
        (AWSSecretManager, "botocore.exceptions.ClientError"),
        (VaultSecretManager, "hvac.exceptions.VaultError"),
        (GCPSecretManager, "google.api_core.exceptions.GoogleAPIError")
    ])
    def test_secret_manager_error_handling(self, manager_class, error_type):
        with patch(f"{manager_class.__module__}.{manager_class.__name__}._get_secret") as mock_get:
            mock_get.side_effect = Exception("Secret not found")
            
            manager = manager_class()
            with pytest.raises(Exception) as exc:
                manager.get_secret("test-secret", "api_key")
            assert "Secret not found" in str(exc.value)

    def test_secret_rotation(self):
        manager = SecretManager()
        old_secret = "old-key-123"
        new_secret = "new-key-456"

        # Test secret rotation
        manager.rotate_secret("test-secret", old_secret, new_secret)
        assert manager.get_secret("test-secret", "api_key") == new_secret

    def test_secret_validation(self):
        manager = SecretManager()
        
        # Test valid secret
        assert manager.validate_secret("test-key-123") is True
        
        # Test invalid secret (too short)
        assert manager.validate_secret("short") is False
        
        # Test invalid secret (contains spaces)
        assert manager.validate_secret("test key 123") is False

    def test_secret_encryption(self):
        manager = SecretManager()
        secret = "test-key-123"
        
        # Test encryption
        encrypted = manager.encrypt_secret(secret)
        assert encrypted != secret
        
        # Test decryption
        decrypted = manager.decrypt_secret(encrypted)
        assert decrypted == secret 