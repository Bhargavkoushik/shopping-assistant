import json

import pytest

from app.agent import (
    CARTS,
    DISCOUNT_CODES,
    REGISTERED_USERS,
    USER_PREFERENCES,
    add_to_cart,
    clear_cart,
    get_best_coupon,
    recommend_products,
    remove_from_cart,
    set_user_preference,
    shopping_advisor,
    view_cart,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Resets global in-memory state before each test to ensure isolation."""
    CARTS.clear()
    USER_PREFERENCES.clear()
    DISCOUNT_CODES.clear()
    DISCOUNT_CODES.update({
        "WELCOME50": {"discount": 50, "used": False},
        "SUMMER20": {"discount": 20, "used": False},
    })
    REGISTERED_USERS.clear()
    REGISTERED_USERS.update({"user123", "shopper_jane", "buyer_bob"})

    from app.chat_db import clear_messages
    clear_messages("user123")
    clear_messages("shopper_jane")
    clear_messages("buyer_bob")
    clear_messages("demo_user_001")
    clear_messages("test_persist_user")


def test_cart_operations():
    # 1. Add valid product
    res = add_to_cart("user123", "lap_001", 2)
    data = json.loads(res)
    assert data["status"] == "success"
    assert data["cart_item"]["product_id"] == "lap_001"
    assert data["cart_item"]["quantity_added"] == 2
    assert data["cart_item"]["total_quantity"] == 2

    # 2. Add same product to check duplicate cart corruption prevention
    res = add_to_cart("user123", "Dell Inspiron 15", 3)
    data = json.loads(res)
    assert data["status"] == "success"
    assert data["cart_item"]["total_quantity"] == 5
    assert CARTS["user123"]["lap_001"] == 5

    # 3. Add invalid product
    res = add_to_cart("user123", "invalid_prod_123", 1)
    data = json.loads(res)
    assert data["status"] == "error"

    # 4. Add negative quantity
    res = add_to_cart("user123", "lap_001", -1)
    data = json.loads(res)
    assert data["status"] == "error"

    # 5. View cart
    res = view_cart("user123")
    data = json.loads(res)
    assert data["status"] == "success"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5
    assert data["subtotal"] == 45000 * 5

    # 6. Remove product
    res = remove_from_cart("user123", "Dell Inspiron 15")
    data = json.loads(res)
    assert data["status"] == "success"
    assert "lap_001" not in CARTS["user123"]

    # 7. Clear cart
    add_to_cart("user123", "lap_001", 1)
    res = clear_cart("user123")
    data = json.loads(res)
    assert data["status"] == "success"
    assert len(CARTS["user123"]) == 0


def test_get_best_coupon():
    # Test WELCOME50 vs SUMMER20 on HP Pavilion 14 (Price: 62000)
    res = get_best_coupon("HP Pavilion 14", "user123")
    assert "HP Pavilion 14 price: ₹62,000" in res
    assert "WELCOME50:\nSavings = ₹31,000" in res
    assert "SUMMER20:\nSavings = ₹12,400" in res
    assert "Best Coupon:\nWELCOME50" in res
    assert "Reason:\nProvides highest discount amount." in res


def test_recommend_products_with_scoring():
    # Test query-based scoring like "Best laptop under ₹70000 for AI/ML"
    res = recommend_products(category="Laptops", budget=70000.0, requirements="AI/ML")
    # HP Pavilion 14 has 16GB RAM and Ryzen 5 processor, price is 62000, so it fits and should be high ranked
    assert "HP Pavilion 14" in res
    assert "16GB RAM" in res
    assert "Ryzen 5" in res

    # Smartwatch for fitness
    res_wearable = recommend_products(category="Wearables", budget=None, requirements="fitness")
    assert "Fitbit Charge 6" in res_wearable or "Galaxy Watch" in res_wearable


def test_shopping_advisor():
    # Test dilemma HP Pavilion 14 vs Dell Inspiron 15 for AI/ML
    res = shopping_advisor("Should I buy HP Pavilion 14 or Dell Inspiron 15 for AI/ML?", "user123")
    assert "Recommendation: HP Pavilion 14" in res
    assert "16GB RAM" in res
    assert "Better multitasking" in res
    assert "Coupon:\nWELCOME50" in res
    assert "Final Effective Cost:\n₹31,000" in res


def test_agent_memory():
    # Save a preference: brand Samsung
    set_user_preference("brand", "Samsung", "user123")

    # Recommend a phone (Mobiles category)
    res = recommend_products(category="Mobiles", budget=None, requirements="Recommend a phone", user_id="user123")

    # Prioritizes Samsung products (Samsung S25 or Samsung S25 Ultra)
    # The output should show the Samsung product first or highlight that it matches the user preference
    assert "Samsung" in res
    assert "Prioritized" in res


def test_db_persistence():
    from app.chat_db import clear_messages, get_messages, save_message
    clear_messages("test_persist_user")

    # Check initially empty
    msgs = get_messages("test_persist_user")
    assert len(msgs) == 0

    # Save messages
    save_message("test_persist_user", "user", "Hello")
    save_message("test_persist_user", "assistant", "World")

    # Retrieve and check
    msgs = get_messages("test_persist_user")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "World"

    # Clear
    clear_messages("test_persist_user")
    msgs = get_messages("test_persist_user")
    assert len(msgs) == 0
