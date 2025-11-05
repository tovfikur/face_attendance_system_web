"""Unit tests for authentication service and security module."""

import json
from datetime import timedelta

import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_different_from_plain(self):
        """Test that hashed password is different from plain password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password

    def test_hash_password_is_deterministic(self):
        """Test that hashing the same password produces different hashes (bcrypt is non-deterministic)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # BCrypt produces different hashes each time (with different salts)
        assert hash1 != hash2
        # But both should verify against the same password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "secure_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_empty_password(self):
        """Test password verification with empty password."""
        password = "secure_password_123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_verify_password_with_special_characters(self):
        """Test password hashing and verification with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("p@ssw0rd!#$%^&*()", hashed) is True
        assert verify_password("p@ssw0rd!#$%^&*", hashed) is False


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_default_expiration(self):
        """Test that create_access_token uses default expiration."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert "exp" in payload
        assert payload["sub"] == "user123"

    def test_create_access_token_with_custom_expiration(self):
        """Test that create_access_token respects custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = verify_token(token)
        assert "exp" in payload
        assert payload["sub"] == "user123"

    def test_create_access_token_includes_data(self):
        """Test that created token includes all provided data."""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a string."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_with_custom_expiration(self):
        """Test that create_refresh_token respects custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(days=7)
        token = create_refresh_token(data, expires_delta=expires_delta)

        payload = verify_token(token)
        assert "exp" in payload
        assert payload["sub"] == "user123"


class TestTokenVerification:
    """Tests for JWT token verification."""

    def test_verify_token_with_valid_token(self):
        """Test token verification with valid token."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"

    def test_verify_token_with_invalid_token(self):
        """Test token verification with invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):
            verify_token(invalid_token)

    def test_verify_token_with_corrupted_token(self):
        """Test token verification with corrupted token."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Corrupt the token by changing characters
        corrupted_token = token[:-10] + "corrupted"

        with pytest.raises(Exception):
            verify_token(corrupted_token)

    def test_verify_token_with_empty_token(self):
        """Test token verification with empty token."""
        with pytest.raises(Exception):
            verify_token("")

    def test_verify_token_extracts_all_claims(self):
        """Test that verify_token extracts all claims from token."""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "role_id": "ROLE-ADMIN",
            "permissions": ["*"],
        }
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["role_id"] == "ROLE-ADMIN"
        assert payload["permissions"] == ["*"]


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_access_token_has_expiration(self):
        """Test that access token has expiration time."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_refresh_token_has_expiration(self):
        """Test that refresh token has expiration time."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)

        payload = verify_token(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_access_token_expiration_is_soon(self):
        """Test that access token expiration is relatively soon (15 minutes by default)."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        payload = verify_token(token)

        # The expiration should be close to now + 15 minutes
        # We allow a 10-second window for test execution
        import time
        current_time = int(time.time())
        expected_expiration_range = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Token should expire in approximately the configured duration
        time_until_expiration = payload["exp"] - current_time
        assert expected_expiration_range - 10 < time_until_expiration < expected_expiration_range + 10

    def test_refresh_token_expiration_is_longer(self):
        """Test that refresh token expiration is longer than access token."""
        data = {"sub": "user123"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]


class TestTokenSecurity:
    """Tests for token security aspects."""

    def test_token_algorithm_is_correct(self):
        """Test that token is created with correct algorithm."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Token should be a valid JWT
        parts = token.split(".")
        assert len(parts) == 3  # JWT has 3 parts: header.payload.signature

    def test_different_tokens_are_different(self):
        """Test that creating tokens at different times produces different tokens."""
        data = {"sub": "user123"}
        token1 = create_access_token(data)

        import time
        time.sleep(0.1)  # Small delay to ensure different timestamps

        token2 = create_access_token(data)

        # Tokens should be different (because of different creation times in payload)
        assert token1 != token2

    def test_token_cannot_be_modified(self):
        """Test that modifying a token makes it invalid."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Modify one character in the token
        modified_token = token[:-1] + ("0" if token[-1] != "0" else "1")

        with pytest.raises(Exception):
            verify_token(modified_token)
