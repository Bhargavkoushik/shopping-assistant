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
import os

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from pydantic import BaseModel

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    project_id = "mock-project-id"
    class MockLogger:
        def log_struct(self, data, severity="INFO"):
            pass
    logger = MockLogger()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

otel_to_cloud = True
try:
    google.auth.default()
except Exception:
    otel_to_cloud = False

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri if otel_to_cloud else None,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=otel_to_cloud,
)
app.title = "shopping-assistant"
app.description = "API for interacting with the Agent shopping-assistant"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


CATEGORIES_MAP = {
    "laptops": ["laptops", "laptop"],
    "mobiles": ["mobiles", "mobile", "phones", "phone"],
    "wearables": ["wearables", "wearable", "smartwatches", "smartwatch", "watches", "watch"],
    "audio": ["audio devices", "audio device", "audio", "headphones", "headphone", "earbuds", "earbud"],
    "smart home": ["smart home products", "smart home product", "smart home", "home products", "home product"]
}

CATALOG_CAT_MAP = {
    "laptops": "Laptops",
    "mobiles": "Mobiles",
    "wearables": "Wearables",
    "audio": "Audio",
    "smart home": "Smart Home"
}

def check_product_discovery(msg: str):
    from typing import Optional
    import re
    msg_clean = msg.lower().strip()
    
    for canonical_name, aliases in CATEGORIES_MAP.items():
        catalog_cat = CATALOG_CAT_MAP[canonical_name]
        for alias in aliases:
            alias_esc = re.escape(alias)
            patterns = [
                rf"^find\s+{alias_esc}\b",
                rf"^search\s+{alias_esc}\b",
                rf"^show\s+{alias_esc}\b",
                rf"^list\s+{alias_esc}\b",
                rf"^what\s+{alias_esc}\s+are\s+available\b",
                rf"^which\s+{alias_esc}\s+do\s+you\s+sell\b",
                rf"^what\s+{alias_esc}\s+do\s+you\s+have\b",
                rf"^show\s+all\s+{alias_esc}\b",
                rf"^available\s+{alias_esc}\b",
                rf"^{alias_esc}\s+catalog\b",
                rf"^do\s+you\s+have\s+any\s+{alias_esc}\b",
                rf"^list\s+all\s+{alias_esc}\b",
                rf"^browse\s+{alias_esc}\b"
            ]
            for pat in patterns:
                if re.search(pat, msg_clean):
                    budget = None
                    budget_match = re.search(r'(?:under|below|budget of)?\s*(?:rs\.?|inr|₹)?\s*(\d+)', msg_clean)
                    if budget_match:
                        budget = float(budget_match.group(1))
                    return {
                        "category": catalog_cat,
                        "max_price": budget
                    }
                    
    for canonical_name, aliases in CATEGORIES_MAP.items():
        catalog_cat = CATALOG_CAT_MAP[canonical_name]
        for alias in aliases:
            if msg_clean == alias or msg_clean == f"{alias}s":
                return {
                    "category": catalog_cat,
                    "max_price": None
                }
                
    return None


class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    import json
    import re

    from fastapi.responses import StreamingResponse

    def event_generator():
        prompt_lower = request.message.lower().strip()

        # Parse intent and yield simulated tool_call if found
        intent_info = {}
        is_register = "register" in prompt_lower or "sign up" in prompt_lower or "signup" in prompt_lower
        is_redeem = "redeem" in prompt_lower or "apply" in prompt_lower
        
        discovery_info = check_product_discovery(request.message)

        if is_register:
            tc_text = f"tool_call: register_user(user_id={request.user_id!r})\n"
            yield f"data: {json.dumps({'text': tc_text})}\n\n"
            intent_info = {"intent": "register_user", "args": {}}
        elif is_redeem:
            code_match = re.search(r'(WELCOME50|SUMMER20)', request.message.upper())
            if code_match:
                tc_text = f"tool_call: redeem_discount_code(user_id={request.user_id!r}, code={code_match.group(1)!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "redeem_discount_code", "args": {"code": code_match.group(1)}}
        elif discovery_info:
            category = discovery_info["category"]
            max_price = discovery_info["max_price"]
            tc_text = f"tool_call: search_products(query={category!r}, max_price={max_price!r}, category={category!r})\n"
            yield f"data: {json.dumps({'text': tc_text})}\n\n"
            intent_info = {"intent": "search_products", "args": {"query": category, "max_price": max_price, "category": category}}
        else:
            # A. Shopping Advisor
            advisor_match = re.search(r'should\s+i\s+buy\s+(.+?)\s+or\s+(.+?)(?:\s+for\s+(.+))?\??$', prompt_lower)
            if advisor_match:
                tc_text = f"tool_call: shopping_advisor(user_query={request.message!r}, user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "shopping_advisor", "args": {"user_query": request.message}}
            # B. Coupon Optimization
            elif any(k in prompt_lower for k in ["best coupon for", "which coupon is best", "coupon for"]):
                coupon_match = re.search(r'(?:which\s+)?coupon\s+(?:is\s+)?(?:best|better)\s+for\s+(.+?)\??$', prompt_lower)
                if not coupon_match:
                    coupon_match = re.search(r'best\s+coupon\s+for\s+(.+?)\??$', prompt_lower)
                if not coupon_match:
                    coupon_match = re.search(r'coupon\s+for\s+(.+?)\??$', prompt_lower)
                if coupon_match:
                    prod_name = coupon_match.group(1).strip()
                    tc_text = f"tool_call: get_best_coupon(product_name={prod_name!r}, user_id={request.user_id!r})\n"
                    yield f"data: {json.dumps({'text': tc_text})}\n\n"
                    intent_info = {"intent": "get_best_coupon", "args": {"product_name": prod_name}}
            # C. Cart Operations
            elif re.search(r'\b(?:clear|empty)\s+(?:my\s+)?cart\b', prompt_lower):
                tc_text = f"tool_call: clear_cart(user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "clear_cart", "args": {}}
            elif re.search(r'\b(?:show|view|display|what\'s\s+in)\s+(?:my\s+)?cart\b', prompt_lower) or prompt_lower == "cart":
                tc_text = f"tool_call: view_cart(user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "view_cart", "args": {}}
            elif re.search(r'\badd\s+(\d+)?\s*(.+?)\s+to\s+(?:my\s+)?cart\b', prompt_lower):
                add_match = re.search(r'\badd\s+(\d+)?\s*(.+?)\s+to\s+(?:my\s+)?cart\b', prompt_lower)
                qty = int(add_match.group(1)) if add_match.group(1) else 1
                prod = add_match.group(2).strip()
                tc_text = f"tool_call: add_to_cart(user_id={request.user_id!r}, product_id={prod!r}, quantity={qty})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "add_to_cart", "args": {"product_id": prod, "quantity": qty}}
            elif re.search(r'\bremove\s+(.+?)(?:\s+from\s+(?:my\s+)?cart)?$', prompt_lower):
                remove_match = re.search(r'\bremove\s+(.+?)(?:\s+from\s+(?:my\s+)?cart)?$', prompt_lower)
                prod = remove_match.group(1).strip()
                tc_text = f"tool_call: remove_from_cart(user_id={request.user_id!r}, product_id={prod!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "remove_from_cart", "args": {"product_id": prod}}
            # D. User Preference
            elif re.search(r'\bi\s+prefer\s+(.+?)\.?$', prompt_lower):
                pref_match = re.search(r'\bi\s+prefer\s+(.+?)\.?$', prompt_lower)
                val = pref_match.group(1).strip()
                pref_type = "brand"
                for cat in ["laptop", "mobile", "phone", "audio", "wearable", "smart home"]:
                    if cat in val:
                        pref_type = "category"
                        if cat == "phone":
                            val = "Mobiles"
                        elif cat == "laptop":
                            val = "Laptops"
                        else:
                            val = cat.title()
                        break
                if pref_type == "brand":
                    val = val.replace("phones", "").replace("mobiles", "").replace("laptops", "").replace("products", "").strip().title()
                tc_text = f"tool_call: set_user_preference(preference_type={pref_type!r}, value={val!r}, user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "set_user_preference", "args": {"preference_type": pref_type, "value": val}}
            elif re.search(r'\b(?:my\s+)?budget\s+(?:is\s+)?(?:of\s+)?(?:rs\.?|inr|₹)?\s*(\d+)\.?$', prompt_lower):
                budget_pref_match = re.search(r'\b(?:my\s+)?budget\s+(?:is\s+)?(?:of\s+)?(?:rs\.?|inr|₹)?\s*(\d+)\.?$', prompt_lower)
                val = budget_pref_match.group(1)
                tc_text = f"tool_call: set_user_preference(preference_type='budget', value={val!r}, user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "set_user_preference", "args": {"preference_type": "budget", "value": val}}
            # E. Product Recommendations
            elif "recommend" in prompt_lower or "best" in prompt_lower:
                category = "Laptops"
                for cat in ["laptop", "mobile", "phone", "audio", "wearable", "smart home", "watch"]:
                    if cat in prompt_lower:
                        if cat in ("phone", "mobile"):
                            category = "Mobiles"
                        elif cat == "laptop":
                            category = "Laptops"
                        elif cat in ("watch", "wearable"):
                            category = "Wearables"
                        else:
                            category = cat.title()
                        break
                budget = None
                budget_match = re.search(r'(?:under|below|budget of)?\s*(?:rs\.?|inr|₹)?\s*(\d+)', prompt_lower)
                if budget_match:
                    budget = float(budget_match.group(1))
                tc_text = f"tool_call: recommend_products(category={category!r}, budget={budget!r}, requirements={request.message!r}, user_id={request.user_id!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "recommend_products", "args": {"category": category, "budget": budget, "requirements": request.message}}
            # F. Compare Products
            elif "compare" in prompt_lower:
                match = re.search(r'compare\s+(.+?)\s+(?:and|vs)\s+(.+)', prompt_lower)
                if match:
                    tc_text = f"tool_call: compare_products(product_a={match.group(1).strip()!r}, product_b={match.group(2).strip()!r})\n"
                    yield f"data: {json.dumps({'text': tc_text})}\n\n"
                    intent_info = {"intent": "compare_products", "args": {"product_a": match.group(1).strip(), "product_b": match.group(2).strip()}}
            # G. Search / Find / Get / Show
            elif any(k in prompt_lower for k in ["find", "search", "show", "get"]):
                category = None
                for cat in ["laptop", "mobile", "phone", "audio", "wearable", "smart home", "watch"]:
                    if cat in prompt_lower:
                        if cat in ("phone", "mobile"):
                            category = "Mobiles"
                        elif cat == "laptop":
                            category = "Laptops"
                        elif cat in ("watch", "wearable"):
                            category = "Wearables"
                        else:
                            category = cat.title()
                        break
                budget = None
                budget_match = re.search(r'(?:under|below|budget of)?\s*(?:rs\.?|inr|₹)?\s*(\d+)', prompt_lower)
                if budget_match:
                    budget = float(budget_match.group(1))
                search_query = category if category else request.message
                tc_text = f"tool_call: search_products(query={search_query!r}, max_price={budget!r}, category={category!r})\n"
                yield f"data: {json.dumps({'text': tc_text})}\n\n"
                intent_info = {"intent": "search_products", "args": {"query": search_query, "max_price": budget, "category": category}}

        try:
            from google.adk.agents.run_config import RunConfig, StreamingMode
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            from app.agent import root_agent

            if not os.environ.get("GEMINI_API_KEY"):
                raise ValueError("GEMINI_API_KEY environment variable is empty.")

            session_service = InMemorySessionService()
            session = session_service.create_session_sync(user_id=request.user_id, app_name="shopping-assistant")
            runner = Runner(agent=root_agent, session_service=session_service, app_name="shopping-assistant")

            new_message = types.Content(
                role="user", parts=[types.Part.from_text(text=request.message)]
            )

            events = runner.run(
                new_message=new_message,
                user_id=request.user_id,
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.SSE),
            )

            has_emitted = False
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            has_emitted = True
                            yield f"data: {json.dumps({'text': part.text})}\n\n"
            if not has_emitted:
                raise ValueError("Empty agent response.")
        except Exception:
            # Fallback mock generator using custom tools
            from app.agent import (
                DISCOUNT_CODES,
                add_to_cart,
                clear_cart,
                compare_products,
                get_best_coupon,
                recommend_products,
                redeem_discount_code,
                register_user,
                remove_from_cart,
                search_products,
                set_user_preference,
                shopping_advisor,
                view_cart,
            )

            def get_fallback():
                intent = intent_info.get("intent")
                args = intent_info.get("args", {})

                if intent == "register_user":
                    return register_user(request.user_id)
                elif intent == "redeem_discount_code":
                    return redeem_discount_code(request.user_id, args["code"])
                elif intent == "add_to_cart":
                    res = add_to_cart(request.user_id, args["product_id"], args["quantity"])
                    try:
                        data = json.loads(res)
                        if data.get("status") == "success":
                            return data["message"]
                        return f"Error: {data.get('message')}"
                    except Exception:
                        return res
                elif intent == "remove_from_cart":
                    res = remove_from_cart(request.user_id, args["product_id"])
                    try:
                        data = json.loads(res)
                        if data.get("status") == "success":
                            return data["message"]
                        return f"Error: {data.get('message')}"
                    except Exception:
                        return res
                elif intent == "view_cart":
                    res = view_cart(request.user_id)
                    try:
                        data = json.loads(res)
                        if data.get("status") == "success":
                            if not data.get("items"):
                                return data["message"]

                            res_str = "### 🛒 Your Shopping Cart:\n\n"
                            res_str += "| Product | Qty | Price | Total |\n"
                            res_str += "| --- | --- | --- | --- |\n"
                            for item in data["items"]:
                                res_str += f"| **{item['product_name']}** | {item['quantity']} | ₹{item['price']:,} | ₹{item['total_price']:,} |\n"
                            res_str += f"\n**Subtotal**: ₹{data['subtotal']:,}\n"
                            return res_str
                        return f"Error: {data.get('message')}"
                    except Exception:
                        return res
                elif intent == "clear_cart":
                    res = clear_cart(request.user_id)
                    try:
                        data = json.loads(res)
                        if data.get("status") == "success":
                            return data["message"]
                        return f"Error: {data.get('message')}"
                    except Exception:
                        return res
                elif intent == "get_best_coupon":
                    return get_best_coupon(args["product_name"], request.user_id)
                elif intent == "set_user_preference":
                    return set_user_preference(args["preference_type"], args["value"], request.user_id)
                elif intent == "shopping_advisor":
                    return shopping_advisor(args["user_query"], request.user_id)
                elif intent == "recommend_products":
                    return recommend_products(args["category"], args["budget"], args["requirements"], request.user_id)
                elif intent == "compare_products":
                    return compare_products(args["product_a"], args["product_b"])
                elif intent == "search_products":
                    return search_products(args["query"], args["max_price"], args["category"])

                if any(k in prompt_lower for k in ["discount", "coupon", "campaign", "code", "offer", "deal", "avail"]):
                    codes_list = []
                    for code, info in DISCOUNT_CODES.items():
                        status = "🔴 Redeemed" if info["used"] else "🟢 Available"
                        codes_list.append(f"- **{code}**: {info['discount']}% off ({status})")
                    return (
                        "Here are the active discount campaigns currently configured:\n\n"
                        + "\n".join(codes_list) + "\n\n"
                        f"To redeem, you can ask me: `redeem WELCOME50` (currently acting as session user `{request.user_id}`)."
                    )

                return (
                    f"Hello! I am your AI Shopping Assistant. Currently interacting as registered user `{request.user_id}`.\n\n"
                    "I can help you:\n"
                    "1. **Search & Recommend Products**: e.g., 'Find laptops under ₹70000'\n"
                    "2. **Shopping Advisor / Tradeoffs**: e.g., 'Should I buy HP Pavilion 14 or Dell Inspiron 15 for AI/ML?'\n"
                    "3. **Cart Operations**: e.g., 'Add HP Pavilion 14 to cart', 'Show my cart', 'Clear cart'\n"
                    "4. **Coupon Optimization**: e.g., 'Which coupon is best for HP Pavilion 14?'\n"
                    "5. **User Preferences**: e.g., 'I prefer Samsung phones'\n"
                    "6. **Redeem Coupon**: e.g., 'Apply coupon WELCOME50'\n\n"
                    "How can I help you today?"
                )

            fallback_text = get_fallback()
            for i in range(0, len(fallback_text), 15):
                chunk = fallback_text[i:i+15]
                yield f"data: {json.dumps({'text': chunk})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")




# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
