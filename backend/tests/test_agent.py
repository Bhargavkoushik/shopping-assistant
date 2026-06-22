# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from app.agent import (
    DISCOUNT_CODES,
    REGISTERED_USERS,
    redeem_discount_code,
    register_user,
)


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Resets the mutable global variables in the agent module to ensure test isolation."""
    DISCOUNT_CODES.clear()
    DISCOUNT_CODES.update(
        {
            "WELCOME50": {"discount": 50, "used": False},
            "SUMMER20": {"discount": 20, "used": False},
        }
    )
    REGISTERED_USERS.clear()
    REGISTERED_USERS.update({"user123", "shopper_jane", "buyer_bob"})


def test_redeem_unregistered_user() -> None:
    """Verifies that an unregistered user cannot redeem a discount code."""
    res = redeem_discount_code("unknown_user", "WELCOME50")
    assert "not registered" in res.lower()
    assert not DISCOUNT_CODES["WELCOME50"]["used"]


def test_redeem_valid_code_success() -> None:
    """Verifies that a registered user can successfully redeem a valid code."""
    res = redeem_discount_code("shopper_jane", "WELCOME50")
    assert "success" in res.lower()
    assert DISCOUNT_CODES["WELCOME50"]["used"]


def test_redeem_invalid_code() -> None:
    """Verifies that an invalid discount code is rejected."""
    res = redeem_discount_code("shopper_jane", "INVALID99")
    assert "invalid" in res.lower()
    assert not DISCOUNT_CODES["WELCOME50"]["used"]
    assert not DISCOUNT_CODES["SUMMER20"]["used"]


def test_redeem_already_used_code() -> None:
    """Verifies the single-use constraint.

    Once a code is redeemed, it cannot be redeemed again by the same or a different user.
    """
    # First redemption should succeed
    res1 = redeem_discount_code("shopper_jane", "WELCOME50")
    assert "success" in res1.lower()

    # Second redemption by same user should fail
    res2 = redeem_discount_code("shopper_jane", "WELCOME50")
    assert "already been redeemed" in res2.lower()

    # Third redemption by different user should also fail
    res3 = redeem_discount_code("buyer_bob", "WELCOME50")
    assert "already been redeemed" in res3.lower()


def test_register_empty_user() -> None:
    """Verifies that registering an empty user ID fails."""
    res = register_user("   ")
    assert "failed" in res.lower()
    assert "   " not in REGISTERED_USERS
    assert "" not in REGISTERED_USERS


def test_redeem_empty_user_id() -> None:
    """Verifies that redemption fails for empty/whitespace user IDs."""
    res = redeem_discount_code("   ", "WELCOME50")
    assert "not registered" in res.lower()
