import json
from fastapi.testclient import TestClient
from app.fast_api_app import app

client = TestClient(app)


def test_product_discovery_routing():
    # 20 phrasings for product discovery routing to search_products
    phrasings = [
        ("find laptops", "search_products", "Laptops"),
        ("search laptops", "search_products", "Laptops"),
        ("show laptops", "search_products", "Laptops"),
        ("list laptops", "search_products", "Laptops"),
        ("what laptops are available", "search_products", "Laptops"),
        ("which laptops do you sell", "search_products", "Laptops"),
        ("what laptops do you have", "search_products", "Laptops"),
        ("show all laptops", "search_products", "Laptops"),
        ("available laptops", "search_products", "Laptops"),
        ("laptop catalog", "search_products", "Laptops"),
        ("find mobiles", "search_products", "Mobiles"),
        ("search phones", "search_products", "Mobiles"),
        ("show wearables", "search_products", "Wearables"),
        ("list smartwatches", "search_products", "Wearables"),
        ("what audio devices are available", "search_products", "Audio"),
        ("which smart home products do you sell", "search_products", "Smart Home"),
        ("what smartwatches do you have", "search_products", "Wearables"),
        ("show all smart home products", "search_products", "Smart Home"),
        ("available audio", "search_products", "Audio"),
        ("phone catalog", "search_products", "Mobiles"),
    ]
    
    for query, expected_tool, expected_cat in phrasings:
        response = client.post("/chat", json={"message": query, "user_id": "demo_user_001"})
        assert response.status_code == 200
        events = response.text.split("\n\n")
        tool_call_found = False
        for event in events:
            if event.startswith("data:"):
                data = json.loads(event[5:].strip())
                text = data.get("text", "")
                if f"tool_call: {expected_tool}" in text:
                    tool_call_found = True
                    if expected_cat:
                        assert expected_cat.lower() in text.lower()
                    break
        assert tool_call_found, f"Query '{query}' failed to route to {expected_tool} with category {expected_cat}"


def test_coupon_routing():
    # 10 phrasings for coupon routing to get_best_coupon
    phrasings = [
        ("best coupon for HP Pavilion 14", "get_best_coupon", "HP Pavilion 14"),
        ("which coupon is best for Dell Inspiron 15", "get_best_coupon", "Dell Inspiron 15"),
        ("coupon for Apple Watch Series 10", "get_best_coupon", "Apple Watch Series 10"),
        ("best coupon for Samsung S25", "get_best_coupon", "Samsung S25"),
        ("which coupon is best for Sony WH-1000XM5", "get_best_coupon", "Sony WH-1000XM5"),
        ("coupon for Acer Nitro 5 Gaming", "get_best_coupon", "Acer Nitro 5 Gaming"),
        ("best coupon for Fitbit Charge 6", "get_best_coupon", "Fitbit Charge 6"),
        ("coupon for iPhone 17", "get_best_coupon", "iPhone 17"),
        ("best coupon for OnePlus Buds 3", "get_best_coupon", "OnePlus Buds 3"),
        ("which coupon is best for Echo Dot 5th Gen", "get_best_coupon", "Echo Dot 5th Gen"),
    ]
    
    for query, expected_tool, expected_prod in phrasings:
        response = client.post("/chat", json={"message": query, "user_id": "demo_user_001"})
        assert response.status_code == 200
        events = response.text.split("\n\n")
        tool_call_found = False
        for event in events:
            if event.startswith("data:"):
                data = json.loads(event[5:].strip())
                text = data.get("text", "")
                if f"tool_call: {expected_tool}" in text:
                    tool_call_found = True
                    assert expected_prod.lower() in text.lower()
                    break
        assert tool_call_found, f"Query '{query}' failed to route to {expected_tool} with product {expected_prod}"


def test_recommendation_routing():
    # 10 phrasings for recommendation routing to recommend_products
    phrasings = [
        ("recommend a laptop", "recommend_products", "Laptops"),
        ("recommend gaming laptop under 80000", "recommend_products", "Laptops"),
        ("best phone for photography under 90000", "recommend_products", "Mobiles"),
        ("best laptop under 70000 for AI/ML", "recommend_products", "Laptops"),
        ("best smartwatch for fitness", "recommend_products", "Wearables"),
        ("recommend audio devices", "recommend_products", "Audio"),
        ("best smart home products under 10000", "recommend_products", "Smart Home"),
        ("recommend a wearable", "recommend_products", "Wearables"),
        ("best mobiles for gaming", "recommend_products", "Mobiles"),
        ("recommend a phone under 50000", "recommend_products", "Mobiles"),
    ]
    
    for query, expected_tool, expected_cat in phrasings:
        response = client.post("/chat", json={"message": query, "user_id": "demo_user_001"})
        assert response.status_code == 200
        events = response.text.split("\n\n")
        tool_call_found = False
        for event in events:
            if event.startswith("data:"):
                data = json.loads(event[5:].strip())
                text = data.get("text", "")
                if f"tool_call: {expected_tool}" in text:
                    tool_call_found = True
                    assert expected_cat.lower() in text.lower()
                    break
        assert tool_call_found, f"Query '{query}' failed to route to {expected_tool} with category {expected_cat}"
