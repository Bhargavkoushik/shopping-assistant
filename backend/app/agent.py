# ruff: noqa
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

from functools import cached_property
from typing import Any, Optional, List, Dict
import os
import google.auth
import json

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini as ADKGemini
from google.genai import Client, types

try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "mock-project-id"

os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or "mock-project-id"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# In-memory store for discount codes and their status.
DISCOUNT_CODES = {
    "WELCOME50": {"discount": 50, "used": False},
    "SUMMER20": {"discount": 20, "used": False},
}

# Registered user IDs
REGISTERED_USERS = {"user123", "shopper_jane", "buyer_bob"}

# Shopping Cart memory
CARTS = {}  # maps user_id -> {product_id: quantity}

# User preference memory
USER_PREFERENCES = {}  # maps user_id -> {"brands": set(), "categories": set(), "budget": float}

# In-memory product catalog containing at least 20 products
PRODUCTS_CATALOG = [
    # Laptops
    {"id": "lap_001", "name": "Dell Inspiron 15", "category": "Laptops", "price": 45000, "description": "15.6-inch FHD laptop, Intel i3, 8GB RAM, 512GB SSD. Perfect for students and daily work.", "specs": {"RAM": "8GB", "Storage": "512GB SSD", "Processor": "Intel Core i3", "Display": "15.6\" FHD"}},
    {"id": "lap_002", "name": "HP Pavilion 14", "category": "Laptops", "price": 62000, "description": "14-inch compact laptop, AMD Ryzen 5, 16GB RAM, 512GB SSD. Great for productivity.", "specs": {"RAM": "16GB", "Storage": "512GB SSD", "Processor": "AMD Ryzen 5", "Display": "14\" FHD"}},
    {"id": "lap_003", "name": "Lenovo IdeaPad Slim 3", "category": "Laptops", "price": 55000, "description": "Intel i5 laptop with 16GB RAM, 512GB SSD, thin and light design.", "specs": {"RAM": "16GB", "Storage": "512GB SSD", "Processor": "Intel Core i5", "Display": "15.6\" FHD"}},
    {"id": "lap_004", "name": "ASUS TUF Gaming A15", "category": "Laptops", "price": 68000, "description": "Entry-level gaming laptop, AMD Ryzen 5, NVIDIA RTX 3050, 144Hz screen.", "specs": {"RAM": "8GB", "Storage": "512GB SSD", "Processor": "AMD Ryzen 5", "Graphics": "RTX 3050", "Display": "15.6\" 144Hz"}},
    {"id": "lap_005", "name": "Acer Nitro 5 Gaming", "category": "Laptops", "price": 75000, "description": "High performance gaming laptop, Intel i5, NVIDIA RTX 4050, 16GB RAM, 1TB SSD.", "specs": {"RAM": "16GB", "Storage": "1TB SSD", "Processor": "Intel Core i5", "Graphics": "RTX 4050", "Display": "15.6\" 144Hz"}},
    {"id": "lap_006", "name": "Apple MacBook Air M2", "category": "Laptops", "price": 95000, "description": "Super thin and light MacBook Air with powerful M2 chip, 8GB unified memory, 256GB SSD.", "specs": {"RAM": "8GB", "Storage": "256GB SSD", "Processor": "Apple M2", "Display": "13.6\" Liquid Retina"}},
    {"id": "lap_007", "name": "Apple MacBook Pro M3", "category": "Laptops", "price": 169000, "description": "Professional notebook with M3 chip, 16GB RAM, 512GB SSD, extreme battery life.", "specs": {"RAM": "16GB", "Storage": "512GB SSD", "Processor": "Apple M3", "Display": "14.2\" Liquid Retina XDR"}},
    
    # Mobiles
    {"id": "mob_001", "name": "iPhone 17", "category": "Mobiles", "price": 89000, "description": "Apple's latest flagship smartphone featuring A19 chip, 120Hz ProMotion display, and advanced dual-lens camera system.", "specs": {"RAM": "8GB", "Storage": "128GB", "Processor": "Apple A19", "Screen": "6.1\" OLED"}},
    {"id": "mob_002", "name": "Samsung S25", "category": "Mobiles", "price": 85000, "description": "Samsung's premier flagship with Snapdragon 8 Gen 4, dynamic AMOLED 2X, and 50MP triple camera system.", "specs": {"RAM": "12GB", "Storage": "256GB", "Processor": "Snapdragon 8 Gen 4", "Screen": "6.2\" AMOLED"}},
    {"id": "mob_003", "name": "iPhone 17 Pro", "category": "Mobiles", "price": 129000, "description": "Premium Apple flagship with Titanium frame, triple-camera system, A19 Pro chip, and action button.", "specs": {"RAM": "12GB", "Storage": "256GB", "Processor": "Apple A19 Pro", "Screen": "6.3\" OLED"}},
    {"id": "mob_004", "name": "Samsung S25 Ultra", "category": "Mobiles", "price": 134000, "description": "Ultimate Samsung flagship with built-in S-Pen, 200MP camera, titanium build, and extreme battery life.", "specs": {"RAM": "16GB", "Storage": "512GB", "Processor": "Snapdragon 8 Gen 4", "Screen": "6.8\" AMOLED"}},
    {"id": "mob_005", "name": "OnePlus 13", "category": "Mobiles", "price": 64000, "description": "Flagship killer featuring Snapdragon 8 Gen 4, 100W superfast charging, and Hasselblad camera tuning.", "specs": {"RAM": "16GB", "Storage": "256GB", "Processor": "Snapdragon 8 Gen 4", "Screen": "6.82\" 2K AMOLED"}},
    {"id": "mob_006", "name": "Redmi Note 14 Pro", "category": "Mobiles", "price": 28000, "description": "Budget flagship with 120Hz curved display, 200MP main camera, and massive 5000mAh battery.", "specs": {"RAM": "8GB", "Storage": "256GB", "Processor": "MediaTek Dimensity 7300", "Screen": "6.67\" AMOLED"}},
    
    # Audio & Wearables
    {"id": "aud_001", "name": "Sony WH-1000XM5", "category": "Audio", "price": 29000, "description": "Industry-leading active noise canceling wireless over-ear headphones.", "specs": {"Battery": "30 Hours", "ANC": "Yes", "Connectivity": "Bluetooth 5.2"}},
    {"id": "aud_002", "name": "Apple AirPods Pro 2", "category": "Audio", "price": 24000, "description": "Premium wireless earbuds with active noise cancellation and personalized spatial audio.", "specs": {"Battery": "6 Hours (Earbuds)", "ANC": "Yes", "Chip": "Apple H2"}},
    {"id": "aud_003", "name": "OnePlus Buds 3", "category": "Audio", "price": 5000, "description": "Affordable wireless earbuds with dual drivers and high-res audio certification.", "specs": {"Battery": "10 Hours (Earbuds)", "ANC": "Yes"}},
    {"id": "wear_001", "name": "Apple Watch Series 10", "category": "Wearables", "price": 46000, "description": "Smartwatch with advanced health sensors, crash detection, and fitness tracking.", "specs": {"OS": "watchOS", "Display": "Always-On Retina", "Water Resistance": "50m"}},
    {"id": "wear_002", "name": "Samsung Galaxy Watch 7", "category": "Wearables", "price": 32000, "description": "Android-focused smartwatch with BioActive health sensor and sleep coaching.", "specs": {"OS": "WearOS", "Display": "Super AMOLED", "Water Resistance": "IP68"}},
    {"id": "wear_003", "name": "Fitbit Charge 6", "category": "Wearables", "price": 15000, "description": "Advanced fitness tracker with built-in GPS and continuous heart rate tracking.", "specs": {"Battery": "7 Days", "Display": "Color Touchscreen", "Water Resistance": "50m"}},
    
    # Smart Home
    {"id": "home_001", "name": "Echo Dot 5th Gen", "category": "Smart Home", "price": 5500, "description": "Compact smart speaker with Alexa featuring deeper bass and clearer vocals.", "specs": {"Voice Assistant": "Alexa", "Connectivity": "WiFi, Bluetooth"}},
    {"id": "home_002", "name": "Google Nest Hub 2nd Gen", "category": "Smart Home", "price": 8000, "description": "Smart display with Google Assistant and gesture controls.", "specs": {"Voice Assistant": "Google Assistant", "Display": "7\" Touchscreen"}}
]


def register_user(user_id: str) -> str:
    """Registers a new user ID so they can redeem discount codes.

    Args:
        user_id: The user ID to register.

    Returns:
        A message confirming registration.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return "Registration failed: User ID cannot be empty."
    REGISTERED_USERS.add(user_clean)
    return f"User '{user_clean}' successfully registered."


def redeem_discount_code(user_id: str, code: str) -> str:
    """Redeems a single-use discount code for a registered user.

    Args:
        user_id: The registered user ID of the customer.
        code: The discount code to redeem (e.g., WELCOME50, SUMMER20).

    Returns:
        A string indicating the result of the redemption process.
    """
    user_clean = user_id.strip()
    if user_clean not in REGISTERED_USERS:
        return f"Redemption failed: User ID '{user_clean}' is not registered. Please register first."

    code_upper = code.upper().strip()
    if code_upper not in DISCOUNT_CODES:
        return f"Redemption failed: Discount code '{code}' is invalid."

    code_data = DISCOUNT_CODES[code_upper]
    if code_data["used"]:
        return f"Redemption failed: Discount code '{code_upper}' has already been redeemed."

    # Mark as used
    code_data["used"] = True
    return f"Success! {code_data['discount']}% discount code '{code_upper}' has been successfully redeemed for user '{user_clean}'."


def search_products(query: str, max_price: Optional[float] = None, category: Optional[str] = None) -> str:
    """Searches the product catalog for matching products.
    
    Args:
        query: The search term or keywords to filter by (e.g., laptop, iPhone).
        max_price: Optional maximum price filter in Indian Rupees (₹).
        category: Optional category filter (e.g., Laptops, Mobiles, Audio, Wearables, Smart Home).
        
    Returns:
        A formatted markdown string listing the search results.
    """
    query_lower = query.lower().strip()
    results = []
    
    for prod in PRODUCTS_CATALOG:
        # Filter by category if specified
        if category and prod["category"].lower() != category.lower().strip():
            continue
        # Filter by max price if specified
        if max_price is not None and prod["price"] > max_price:
            continue
            
        # Match query in name, category, description, specs
        match = (
            query_lower in prod["name"].lower() or
            query_lower in prod["category"].lower() or
            query_lower in prod["description"].lower() or
            any(query_lower in str(val).lower() for val in prod.get("specs", {}).values())
        )
        if match:
            results.append(prod)
            
    if not results:
        filters_str = ""
        if max_price:
            filters_str += f" under ₹{max_price}"
        if category:
            filters_str += f" in category '{category}'"
        return f"No products found matching '{query}'{filters_str}."
        
    res_str = f"Found {len(results)} matching product(s):\n\n"
    res_str += "| Product ID | Name | Category | Price | Description |\n"
    res_str += "| --- | --- | --- | --- | --- |\n"
    for p in results:
        res_str += f"| {p['id']} | **{p['name']}** | {p['category']} | ₹{p['price']:,} | {p['description']} |\n"
    return res_str


def compare_products(product_a: str, product_b: str) -> str:
    """Compares two products from the catalog side-by-side.
    
    Args:
        product_a: Name or ID of the first product.
        product_b: Name or ID of the second product.
        
    Returns:
        A structured markdown table comparing both products' key features, prices, and specs.
    """
    pa_match = None
    pb_match = None
    
    a_clean = product_a.lower().strip()
    b_clean = product_b.lower().strip()
    
    for prod in PRODUCTS_CATALOG:
        p_name = prod["name"].lower()
        p_id = prod["id"].lower()
        if a_clean == p_id or a_clean in p_name:
            pa_match = prod
            break
            
    for prod in PRODUCTS_CATALOG:
        p_name = prod["name"].lower()
        p_id = prod["id"].lower()
        if b_clean == p_id or b_clean in p_name:
            # Make sure it's not the exact same match object if they query the same product name
            if pa_match and prod["id"] == pa_match["id"]:
                continue
            pb_match = prod
            break

    # If first match is still none, try matching any word
    if not pa_match:
        for prod in PRODUCTS_CATALOG:
            for word in a_clean.split():
                if word in prod["name"].lower() and len(word) > 2:
                    pa_match = prod
                    break
            if pa_match:
                break
                
    if not pb_match:
        for prod in PRODUCTS_CATALOG:
            if pa_match and prod["id"] == pa_match["id"]:
                continue
            for word in b_clean.split():
                if word in prod["name"].lower() and len(word) > 2:
                    pb_match = prod
                    break
            if pb_match:
                break

    if not pa_match or not pb_match:
        missing = []
        if not pa_match:
            missing.append(f"'{product_a}'")
        if not pb_match:
            missing.append(f"'{product_b}'")
        return f"Could not find catalog products matching: {', '.join(missing)} for comparison."

    # Build comparison table
    res_str = f"### Product Comparison: {pa_match['name']} vs {pb_match['name']}\n\n"
    res_str += "| Feature | " + f"{pa_match['name']} | {pb_match['name']} |\n"
    res_str += "| --- | --- | --- |\n"
    res_str += f"| **Price** | ₹{pa_match['price']:,} | ₹{pb_match['price']:,} |\n"
    res_str += f"| **Category** | {pa_match['category']} | {pb_match['category']} |\n"
    res_str += f"| **Description** | {pa_match['description']} | {pb_match['description']} |\n"
    
    # Merge specs
    all_spec_keys = set(pa_match.get("specs", {}).keys()).union(set(pb_match.get("specs", {}).keys()))
    for key in sorted(all_spec_keys):
        val_a = pa_match.get("specs", {}).get(key, "N/A")
        val_b = pb_match.get("specs", {}).get(key, "N/A")
        res_str += f"| **{key}** | {val_a} | {val_b} |\n"
        
    return res_str

def find_product_by_id_or_name(product_id_or_name: str) -> Optional[dict]:
    p_clean = product_id_or_name.strip().lower()
    if not p_clean:
        return None
    for p in PRODUCTS_CATALOG:
        if p["id"].lower() == p_clean:
            return p
    for p in PRODUCTS_CATALOG:
        if p["name"].lower() == p_clean:
            return p
    for p in PRODUCTS_CATALOG:
        if p_clean in p["name"].lower():
            return p
    words = [w for w in p_clean.split() if len(w) > 2]
    if words:
        for p in PRODUCTS_CATALOG:
            for w in words:
                if w in p["name"].lower():
                    return p
    return None


def recommend_products(category: str, budget: Optional[float] = None, requirements: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """Recommends products from the catalog based on category, budget, requirements, and user preferences.
    
    Args:
        category: Product category (e.g. Laptops, Mobiles, Audio, Wearables, Smart Home).
        budget: Optional maximum budget in Indian Rupees (₹).
        requirements: Optional user requirements or keywords (e.g. gaming, titanium, ANC, AI/ML, photography).
        user_id: Optional user ID to retrieve stored preferences.
        
    Returns:
        A markdown recommendation list with explanations.
    """
    import re
    
    req_str = requirements or ""
    req_lower = req_str.lower().strip()
    
    # Try to extract budget from requirements if not explicitly provided
    if budget is None:
        budget_match = re.search(r'(?:under|below|budget of|max|less than|up to)\s*(?:rs\.?|inr|₹)?\s*(\d+)(?:\s*(k|thousand))?', req_lower)
        if budget_match:
            val = float(budget_match.group(1))
            if budget_match.group(2) in ('k', 'thousand'):
                val *= 1000
            budget = val
            
    # Try to resolve category if not explicitly provided
    cat_lower = category.lower().strip() if category else ""
    if not cat_lower:
        for possible_cat in ["laptop", "mobile", "phone", "audio", "wearable", "smart home", "watch", "headphone", "earbud"]:
            if possible_cat in req_lower:
                if possible_cat in ("phone", "mobile"):
                    cat_lower = "mobiles"
                elif possible_cat == "laptop":
                    cat_lower = "laptops"
                elif possible_cat in ("watch", "wearable"):
                    cat_lower = "wearables"
                elif possible_cat in ("audio", "headphone", "earbud"):
                    cat_lower = "audio"
                else:
                    cat_lower = possible_cat
                break
                
    # Normalize category to match catalog
    target_category = ""
    if "laptop" in cat_lower:
        target_category = "laptops"
    elif "mobile" in cat_lower or "phone" in cat_lower:
        target_category = "mobiles"
    elif "wearable" in cat_lower or "watch" in cat_lower:
        target_category = "wearables"
    elif "audio" in cat_lower or "headphone" in cat_lower or "earbud" in cat_lower:
        target_category = "audio"
    elif "smart home" in cat_lower or "home" in cat_lower:
        target_category = "smart home"
        
    # Retrieve user preferences
    pref_brands = set()
    pref_categories = set()
    pref_budget = None
    
    if user_id:
        user_clean = user_id.strip()
        pref = USER_PREFERENCES.get(user_clean, {})
        pref_brands = pref.get("brands", set())
        pref_categories = pref.get("categories", set())
        pref_budget = pref.get("budget", None)
        
    # Find candidates
    candidates = []
    for prod in PRODUCTS_CATALOG:
        prod_cat = prod["category"].lower()
        if target_category:
            if prod_cat == target_category:
                candidates.append(prod)
        else:
            if pref_categories:
                if prod_cat in [c.lower() for c in pref_categories]:
                    candidates.append(prod)
            else:
                candidates.append(prod)
                
    if not candidates:
        candidates = list(PRODUCTS_CATALOG)
        
    # Apply budget filter
    active_budget = budget if budget is not None else pref_budget
    if active_budget is not None:
        candidates = [p for p in candidates if p["price"] <= active_budget]
        
    if not candidates:
        budget_str = f" under ₹{active_budget:,}" if active_budget else ""
        cat_str = f" in category '{category}'" if category else ""
        return f"No products found{cat_str}{budget_str} to recommend."
        
    scored_candidates = []
    
    for prod in candidates:
        score = 0
        reasons = []
        
        prod_text = (
            prod["name"].lower() + " " +
            prod["description"].lower() + " " +
            " ".join(str(v).lower() for v in prod.get("specs", {}).values())
        )
        
        # User preference scores (Feature 5)
        prod_brand = prod["name"].split()[0].lower()
        if prod_brand in [b.lower() for b in pref_brands]:
            score += 15
            reasons.append(f"Prioritized: Matches your preferred brand '{prod_brand.title()}' (from memory)")
            
        if prod["category"].lower() in [c.lower() for c in pref_categories]:
            score += 5
            reasons.append("Matches your preferred shopping categories (from memory)")
            
        if pref_budget is not None and prod["price"] <= pref_budget:
            score += 5
            reasons.append(f"Fits within your preferred budget of ₹{pref_budget:,} (from memory)")
            
        # Keyword / requirement matching
        if "ai/ml" in req_lower:
            ram_val = prod.get("specs", {}).get("RAM", "")
            processor = prod.get("specs", {}).get("Processor", "")
            if "16gb" in ram_val.lower() or "12gb" in ram_val.lower():
                score += 10
                reasons.append(f"Equipped with {ram_val} RAM for memory-intensive AI/ML workflows.")
            if any(p in processor.lower() for p in ["ryzen 5", "core i5", "m2", "m3"]):
                score += 8
                reasons.append(f"Powered by a capable processor ({processor}) suitable for running models and code execution.")
            if "ai/ml" in prod_text:
                score += 10
                reasons.append("Specifically optimized/designed for AI/ML workloads.")
                
        if "photography" in req_lower or "camera" in req_lower:
            description = prod["description"].lower()
            if "camera" in description or "sensor" in description:
                score += 8
                reasons.append("Features advanced lens/camera specs for high-quality photography.")
            if "200mp" in description or "200mp" in str(prod.get("specs", {}).values()).lower():
                score += 10
                reasons.append("Equipped with a flagship 200MP camera system for extreme details.")
            elif "50mp" in description or "50mp" in str(prod.get("specs", {}).values()).lower():
                score += 8
                reasons.append("Includes a high-quality 50MP triple-camera system.")
                
        if "gaming" in req_lower:
            specs = prod.get("specs", {})
            if "Graphics" in specs or "rtx" in str(specs.values()).lower():
                score += 12
                reasons.append(f"Has dedicated graphics ({specs.get('Graphics', 'RTX GPU')}) required for gaming.")
            if "144hz" in str(specs.values()).lower():
                score += 6
                reasons.append("Features a high refresh rate 144Hz display for smooth gameplay.")
            if "gaming" in prod_text:
                score += 8
                reasons.append("Specifically built and designed as a gaming system.")
                
        if "fitness" in req_lower or "health" in req_lower:
            description = prod["description"].lower()
            if "fitness" in description or "sensor" in description or "heart rate" in description:
                score += 10
                reasons.append("Includes robust fitness trackers, heart rate monitoring, and activity sensors.")
            if "gps" in description or "gps" in str(prod.get("specs", {}).values()).lower():
                score += 8
                reasons.append("Features built-in GPS for mapping runs and workouts without a phone.")
                
        if "anc" in req_lower or "noise cancel" in req_lower:
            specs = prod.get("specs", {})
            if "ANC" in specs and specs["ANC"] == "Yes":
                score += 12
                reasons.append("Includes Active Noise Cancellation (ANC) to block external noise.")
                
        query_words = [w for w in req_lower.split() if len(w) > 2 and w not in ["best", "under", "phone", "laptop", "smartwatch", "fitness"]]
        matched_words = []
        for w in query_words:
            if w in prod_text:
                score += 3
                matched_words.append(w)
        if matched_words:
            reasons.append(f"Matches search query terms: {', '.join(matched_words)}")
            
        if not reasons:
            reasons.append("Provides solid baseline catalog performance and specifications.")
            
        scored_candidates.append({
            "product": prod,
            "score": score,
            "reasons": reasons
        })
        
    scored_candidates.sort(key=lambda x: (-x["score"], x["product"]["price"]))
    
    res_str = f"### 🌟 Recommended {target_category.title() or 'Products'} based on your requirements:\n\n"
    for i, item in enumerate(scored_candidates[:3], 1):
        p = item["product"]
        res_str += f"{i}. **{p['name']}** (₹{p['price']:,})\n"
        res_str += f"   - *Specs*: {', '.join(f'{k}: {v}' for k, v in p.get('specs', {}).items())}\n"
        res_str += f"   - *Selection Reasoning*:\n"
        for r in item["reasons"]:
            res_str += f"     - {r}\n"
        res_str += f"   - *Description*: {p['description']}\n\n"
        
    return res_str


def add_to_cart(user_id: str, product_id: str, quantity: int = 1) -> str:
    """Adds a specified quantity of a product to the user's shopping cart.
    
    Args:
        user_id: The ID of the user.
        product_id: The ID or name of the product to add.
        quantity: The quantity to add (must be greater than 0).
        
    Returns:
        A JSON string containing the operation status and cart details.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return json.dumps({
            "status": "error",
            "message": "User ID cannot be empty."
        })
        
    product = find_product_by_id_or_name(product_id)
    if not product:
        return json.dumps({
            "status": "error",
            "message": f"Failed to add to cart: Product '{product_id}' is not in the catalog."
        })
        
    try:
        qty_int = int(quantity)
    except (ValueError, TypeError):
        return json.dumps({
            "status": "error",
            "message": f"Quantity must be a valid integer, got {quantity}."
        })
        
    if qty_int <= 0:
        return json.dumps({
            "status": "error",
            "message": "Failed to add to cart: Quantity must be greater than 0."
        })
        
    if user_clean not in CARTS:
        CARTS[user_clean] = {}
        
    prod_id = product["id"]
    current_qty = CARTS[user_clean].get(prod_id, 0)
    new_qty = current_qty + qty_int
    CARTS[user_clean][prod_id] = new_qty
    
    return json.dumps({
        "status": "success",
        "message": f"Successfully added {qty_int} x '{product['name']}' to your cart. Total in cart: {new_qty}.",
        "cart_item": {
            "product_id": prod_id,
            "product_name": product["name"],
            "quantity_added": qty_int,
            "total_quantity": new_qty
        }
    })


def remove_from_cart(user_id: str, product_id: str) -> str:
    """Removes a product completely from the user's shopping cart.
    
    Args:
        user_id: The ID of the user.
        product_id: The ID or name of the product to remove.
        
    Returns:
        A JSON string confirming the removal.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return json.dumps({
            "status": "error",
            "message": "User ID cannot be empty."
        })
        
    if user_clean not in CARTS or not CARTS[user_clean]:
        return json.dumps({
            "status": "success",
            "message": "Your cart is already empty.",
            "cart_empty": True
        })
        
    product = find_product_by_id_or_name(product_id)
    if not product:
        prod_clean = product_id.strip().lower()
        target_id = None
        for k in CARTS[user_clean].keys():
            if k.lower() == prod_clean:
                target_id = k
                break
        if not target_id:
            return json.dumps({
                "status": "error",
                "message": f"Product '{product_id}' was not found in your cart."
            })
    else:
        target_id = product["id"]
        
    if target_id not in CARTS[user_clean]:
        found_key = None
        for k in CARTS[user_clean].keys():
            catalog_item = next((p for p in PRODUCTS_CATALOG if p["id"] == k), None)
            if catalog_item and catalog_item["name"].lower() == product_id.strip().lower():
                found_key = k
                break
        if found_key:
            target_id = found_key
        else:
            return json.dumps({
                "status": "error",
                "message": f"Product '{product_id}' was not found in your cart."
            })
            
    catalog_item = next((p for p in PRODUCTS_CATALOG if p["id"] == target_id), None)
    product_name = catalog_item["name"] if catalog_item else target_id
    
    del CARTS[user_clean][target_id]
    
    return json.dumps({
        "status": "success",
        "message": f"Removed '{product_name}' from your cart.",
        "removed_item": {
            "product_id": target_id,
            "product_name": product_name
        }
    })


def view_cart(user_id: str) -> str:
    """Views the current items, quantities, and subtotal in the user's shopping cart.
    
    Args:
        user_id: The ID of the user.
        
    Returns:
        A JSON string representing the cart contents.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return json.dumps({
            "status": "error",
            "message": "User ID cannot be empty."
        })
        
    if user_clean not in CARTS or not CARTS[user_clean]:
        return json.dumps({
            "status": "success",
            "user_id": user_clean,
            "items": [],
            "subtotal": 0,
            "message": "Your shopping cart is currently empty."
        })
        
    items = []
    subtotal = 0
    for p_id, qty in CARTS[user_clean].items():
        product = next((p for p in PRODUCTS_CATALOG if p["id"] == p_id), None)
        if product:
            item_total = product["price"] * qty
            subtotal += item_total
            items.append({
                "product_id": p_id,
                "product_name": product["name"],
                "quantity": qty,
                "price": product["price"],
                "total_price": item_total
            })
        else:
            items.append({
                "product_id": p_id,
                "product_name": p_id,
                "quantity": qty,
                "price": 0,
                "total_price": 0
            })
            
    return json.dumps({
        "status": "success",
        "user_id": user_clean,
        "items": items,
        "subtotal": subtotal
    })


def clear_cart(user_id: str) -> str:
    """Clears all items from the user's shopping cart.
    
    Args:
        user_id: The ID of the user.
        
    Returns:
        A JSON string confirming the cart has been cleared.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return json.dumps({
            "status": "error",
            "message": "User ID cannot be empty."
        })
        
    if user_clean in CARTS:
        CARTS[user_clean] = {}
        
    return json.dumps({
        "status": "success",
        "message": "Your shopping cart has been cleared.",
        "cart_cleared": True
    })


def get_best_coupon(product_name: str, user_id: str) -> str:
    """Recommends the best available coupon code for a product based on maximum savings.
    
    Args:
        product_name: Name or ID of the product.
        user_id: The user ID checking the coupons.
        
    Returns:
        A structured string detailing coupon savings and recommending the best one.
    """
    user_clean = user_id.strip()
    if not user_clean:
        return "Error: User ID cannot be empty."
        
    product = find_product_by_id_or_name(product_name)
    if not product:
        return f"Could not find product '{product_name}' in the catalog to calculate savings."
        
    price = product["price"]
    
    used = set()
    try:
        import streamlit as st
        if st.session_state and "used_codes" in st.session_state:
            used = st.session_state["used_codes"].get(user_clean, set())
    except Exception:
        pass
        
    savings = {}
    for code, info in DISCOUNT_CODES.items():
        is_used = code in used or info["used"]
        if not is_used:
            discount_val = (price * info["discount"]) / 100
            savings[code] = discount_val
            
    if not savings:
        return f"{product['name']} price: ₹{price:,}\n\nNo coupons available (all redeemed or invalid).\n\nBest Coupon: None\n\nReason: No active coupons found for user '{user_clean}'."
        
    best_code = max(savings, key=savings.get)
    best_discount = savings[best_code]
    
    res_lines = [f"{product['name']} price: ₹{price:,}\n"]
    for code, amt in savings.items():
        res_lines.append(f"{code}:\nSavings = ₹{amt:,.0f}\n")
        
    res_lines.append(f"Best Coupon:\n{best_code}\n")
    res_lines.append(f"Reason:\nProvides highest discount amount.")
    
    return "\n".join(res_lines)


def set_user_preference(preference_type: str, value: str, user_id: str) -> str:
    """Stores a user preference in memory (e.g., preferred brand, category, or budget).
    
    Args:
        preference_type: The type of preference ('brand', 'category', 'budget').
        value: The value to store (e.g. 'Samsung', 'Laptops', '70000').
        user_id: The ID of the active user.
        
    Returns:
        A confirmation message.
    """
    user_clean = user_id.strip()
    pref_type = preference_type.strip().lower()
    val_clean = value.strip()
    
    if user_clean not in USER_PREFERENCES:
        USER_PREFERENCES[user_clean] = {
            "brands": set(),
            "categories": set(),
            "budget": None
        }
        
    if pref_type == "brand":
        USER_PREFERENCES[user_clean]["brands"].add(val_clean)
        return f"I have saved '{val_clean}' as your preferred brand in memory."
    elif pref_type == "category":
        mapped_cat = val_clean.title()
        if val_clean.lower() == "phone" or val_clean.lower() == "mobile":
            mapped_cat = "Mobiles"
        USER_PREFERENCES[user_clean]["categories"].add(mapped_cat)
        return f"I have saved '{mapped_cat}' as your preferred shopping category in memory."
    elif pref_type == "budget":
        try:
            budget_val = float(val_clean.replace("₹", "").replace(",", "").strip())
            USER_PREFERENCES[user_clean]["budget"] = budget_val
            return f"I have saved ₹{budget_val:,} as your maximum budget preference in memory."
        except ValueError:
            return f"Could not parse budget value '{value}'."
            
    return f"Unsupported preference type '{preference_type}'."


def shopping_advisor(user_query: str, user_id: str = "demo_user_001") -> str:
    """Analyzes a shopping dilemma, compares choices, recommends coupons, and estimates final costs.
    
    Args:
        user_query: The customer query or comparison query (e.g. Should I buy HP Pavilion 14 or Dell Inspiron 15 for AI/ML?).
        user_id: The active user ID.
        
    Returns:
        A detailed advisory response showing comparisons, coupon optimization, and final payable costs.
    """
    import re
    
    q_lower = user_query.lower().strip()
    
    scored_prods = []
    for p in PRODUCTS_CATALOG:
        score = 0
        name_lower = p["name"].lower()
        id_lower = p["id"].lower()
        if id_lower in q_lower:
            score += 100
        if name_lower in q_lower:
            score += 50
        else:
            words = name_lower.replace("-", " ").split()
            for w in words:
                if len(w) > 2 and w in q_lower:
                    score += 10
        if score > 0:
            scored_prods.append((p, score))
            
    scored_prods.sort(key=lambda x: -x[1])
    unique_prods = []
    for p, s in scored_prods:
        if p["id"] not in [x["id"] for x in unique_prods]:
            unique_prods.append(p)
            
    if len(unique_prods) < 2:
        category = "Laptops"
        if "phone" in q_lower or "mobile" in q_lower:
            category = "Mobiles"
        elif "watch" in q_lower or "wearable" in q_lower:
            category = "Wearables"
        elif "audio" in q_lower or "headphone" in q_lower or "earbud" in q_lower:
            category = "Audio"
            
        recs = recommend_products(category=category, budget=None, requirements=user_query, user_id=user_id)
        return f"I couldn't identify two specific products to compare. Let me recommend some choices:\n\n{recs}"
        
    prod_a = unique_prods[0]
    prod_b = unique_prods[1]
    
    score_a = 0
    score_b = 0
    reasons = []
    
    ram_a = prod_a.get("specs", {}).get("RAM", "")
    ram_b = prod_b.get("specs", {}).get("RAM", "")
    
    price_a = prod_a["price"]
    price_b = prod_b["price"]
    
    def parse_ram(ram_str):
        match = re.search(r'(\d+)\s*gb', ram_str.lower())
        return int(match.group(1)) if match else 0
        
    gb_a = parse_ram(ram_a)
    gb_b = parse_ram(ram_b)
    
    if "ai/ml" in q_lower or "development" in q_lower or "programming" in q_lower:
        if gb_a > gb_b:
            score_a += 20
            reasons = [
                f"{gb_a}GB RAM",
                "Better multitasking",
                "Better future-proofing"
            ]
        elif gb_b > gb_a:
            score_b += 20
            reasons = [
                f"{gb_b}GB RAM",
                "Better multitasking",
                "Better future-proofing"
            ]
        else:
            if price_a < price_b:
                score_a += 5
                reasons = ["More budget friendly choice", "Great value for money"]
            else:
                score_b += 5
                reasons = ["More budget friendly choice", "Great value for money"]
                
    elif "gaming" in q_lower:
        has_gpu_a = "Graphics" in prod_a.get("specs", {}) or "rtx" in str(prod_a.get("specs", {}).values()).lower()
        has_gpu_b = "Graphics" in prod_b.get("specs", {}) or "rtx" in str(prod_b.get("specs", {}).values()).lower()
        if has_gpu_a and not has_gpu_b:
            score_a += 20
            reasons = ["Dedicated graphics card (RTX)", "Smoother gaming frame rates"]
        elif has_gpu_b and not has_gpu_a:
            score_b += 20
            reasons = ["Dedicated graphics card (RTX)", "Smoother gaming frame rates"]
        else:
            if price_a < price_b:
                score_a += 5
                reasons = ["More budget friendly choice", "Great value for money"]
            else:
                score_b += 5
                reasons = ["More budget friendly choice", "Great value for money"]
                
    elif "photography" in q_lower or "camera" in q_lower:
        desc_a = prod_a["description"].lower()
        desc_b = prod_b["description"].lower()
        cam_200_a = "200mp" in desc_a or "200mp" in str(prod_a.get("specs", {}).values()).lower()
        cam_200_b = "200mp" in desc_b or "200mp" in str(prod_b.get("specs", {}).values()).lower()
        cam_50_a = "50mp" in desc_a or "50mp" in str(prod_a.get("specs", {}).values()).lower()
        cam_50_b = "50mp" in desc_b or "50mp" in str(prod_b.get("specs", {}).values()).lower()
        
        if cam_200_a and not cam_200_b:
            score_a += 20
            reasons = ["Flagship 200MP camera system", "Superior details and zoom capabilities"]
        elif cam_200_b and not cam_200_a:
            score_b += 20
            reasons = ["Flagship 200MP camera system", "Superior details and zoom capabilities"]
        elif cam_50_a and not cam_50_b:
            score_a += 10
            reasons = ["50MP camera system", "Better details and photography capabilities"]
        elif cam_50_b and not cam_50_a:
            score_b += 10
            reasons = ["50MP camera system", "Better details and photography capabilities"]
        else:
            if price_a < price_b:
                score_a += 5
                reasons = ["More budget friendly choice", "Great value for money"]
            else:
                score_b += 5
                reasons = ["More budget friendly choice", "Great value for money"]
    else:
        if gb_a != gb_b:
            if gb_a > gb_b:
                score_a += gb_a - gb_b
                reasons = [f"Higher RAM ({gb_a}GB vs {gb_b}GB)", "Better multitasking capabilities"]
            else:
                score_b += gb_b - gb_a
                reasons = [f"Higher RAM ({gb_b}GB vs {gb_a}GB)", "Better multitasking capabilities"]
        else:
            if price_a < price_b:
                score_a += 10
                reasons = ["More budget friendly choice", "Great value for money"]
            else:
                score_b += 10
                reasons = ["More budget friendly choice", "Great value for money"]
                
    rec_prod = prod_a if score_a >= score_b else prod_b
    
    best_coupon_code = "WELCOME50"
    best_discount = 0
    
    used = set()
    try:
        import streamlit as st
        if st.session_state and "used_codes" in st.session_state:
            active_u = user_id or st.session_state.get("active_user", "demo_user_001")
            used = st.session_state["used_codes"].get(active_u, set())
    except Exception:
        pass
        
    for code, info in DISCOUNT_CODES.items():
        is_used = code in used or info["used"]
        if not is_used:
            discount_val = (rec_prod["price"] * info["discount"]) / 100
            if discount_val > best_discount:
                best_discount = discount_val
                best_coupon_code = code
                
    if best_discount == 0:
        best_coupon_code = "None"
        best_discount = 0
        
    final_payable = rec_prod["price"] - best_discount
    
    res_str = f"Recommendation: {rec_prod['name']}\n\n"
    res_str += "Reasons:\n"
    for r in reasons:
        res_str += f"* {r}\n"
    res_str += f"\nCoupon:\n{best_coupon_code}\n\n"
    res_str += f"Final Effective Cost:\n₹{final_payable:,.0f}"
    
    return res_str


class Gemini(ADKGemini):
    api_key: str = os.environ.get("GEMINI_API_KEY", "")

    @cached_property
    def api_client(self) -> Client:
        from google.genai import Client

        base_url, api_version = self._base_url_and_api_version
        kwargs_for_http_options = {
            "headers": self._tracking_headers(),
            "retry_options": self.retry_options,
            "base_url": base_url,
        }
        if api_version:
            kwargs_for_http_options["api_version"] = api_version
        return Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(**kwargs_for_http_options),
        )

    @cached_property
    def _live_api_client(self) -> Client:
        from google.genai import Client

        base_url, _ = self._base_url_and_api_version
        return Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                api_version=self._live_api_version,
                base_url=base_url,
            ),
        )


root_agent = Agent(
    name="shopping_assistant_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
        api_key=os.environ.get("GEMINI_API_KEY", ""),
    ),
    instruction=(
        "You are an AI shopping assistant for a retail store. Help customers search for products, "
        "compare products, and get recommendations based on category, budget, and requirements. "
        "You have access to a shopping cart; help customers add/remove/view/clear items. "
        "You can evaluate available coupon codes (WELCOME50 and SUMMER20) and recommend the best one for maximum savings. "
        "When helping users make decisions, use the shopping_advisor tool to compare options, suggest coupons, "
        "and calculate final payable costs. Track customer brand, category, and budget preferences in memory "
        "using set_user_preference, and prioritize these preferences in future recommendations. "
        "Always maintain a helpful, professional tone."
    ),
    tools=[
        register_user,
        redeem_discount_code,
        search_products,
        compare_products,
        recommend_products,
        add_to_cart,
        remove_from_cart,
        view_cart,
        clear_cart,
        get_best_coupon,
        shopping_advisor,
        set_user_preference
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
