import streamlit as st
import requests
import json
import re
import os
import sys

# Resolve paths to allow direct imports from backend
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    from app.chat_db import get_messages, save_message
except ImportError:
    # Fallback in case of running independently
    def get_messages(user_id: str):
        return []
    def save_message(user_id: str, role: str, content: str):
        pass

# Session state initialization at the top of the file
if "registered_users" not in st.session_state:
    st.session_state["registered_users"] = [
        "demo_user_001", "demo_user_002", "demo_user_003"
    ]
if "active_user" not in st.session_state:
    st.session_state["active_user"] = "demo_user_001"
if "previous_user" not in st.session_state:
    st.session_state["previous_user"] = ""
if "used_codes" not in st.session_state:
    st.session_state["used_codes"] = {}
if "pending_message" not in st.session_state:
    st.session_state["pending_message"] = ""
if "trigger_send" not in st.session_state:
    st.session_state["trigger_send"] = False

# Load messages for the active user if changed or uninitialized
if "messages" not in st.session_state or st.session_state["active_user"] != st.session_state["previous_user"]:
    st.session_state["messages"] = get_messages(st.session_state["active_user"])
    st.session_state["previous_user"] = st.session_state["active_user"]

try:
    from app.agent import register_user, redeem_discount_code, REGISTERED_USERS, DISCOUNT_CODES
except ImportError:
    # Fallback in case of import error or running independently
    REGISTERED_USERS = {"user123", "shopper_jane", "buyer_bob"}
    DISCOUNT_CODES = {
        "WELCOME50": {"discount": 50, "used": False},
        "SUMMER20": {"discount": 20, "used": False},
    }
    def register_user(user_id: str) -> str:
        user_clean = user_id.strip()
        if not user_clean:
            return "Registration failed: User ID cannot be empty."
        REGISTERED_USERS.add(user_clean)
        return f"User '{user_clean}' successfully registered."
    def redeem_discount_code(user_id: str, code: str) -> str:
        user_clean = user_id.strip()
        if user_clean not in REGISTERED_USERS:
            return f"Redemption failed: User ID '{user_clean}' is not registered. Please register first."
        code_upper = code.upper().strip()
        if code_upper not in DISCOUNT_CODES:
            return f"Redemption failed: Discount code '{code}' is invalid."
        code_data = DISCOUNT_CODES[code_upper]
        if code_data["used"]:
            return f"Redemption failed: Discount code '{code_upper}' has already been redeemed."
        code_data["used"] = True
        return f"Success! {code_data['discount']}% discount code '{code_upper}' has been successfully redeemed for user '{user_clean}'."

def generate_fallback_response(prompt: str, user_id: str) -> str:
    """Intelligent conversational fallback simulating the agent when credentials are not configured."""
    prompt_lower = prompt.lower().strip()

    # 1. Available coupons check
    if any(k in prompt_lower for k in ["discount", "coupon", "campaign", "code", "offer", "deal", "avail"]):
        codes_list = []
        user = st.session_state["active_user"]
        used = st.session_state["used_codes"].get(user, set())
        for code, info in DISCOUNT_CODES.items():
            is_used = code in used or info["used"]
            status = "🔴 Redeemed" if is_used else "🟢 Available"
            codes_list.append(f"- **{code}**: {info['discount']}% off ({status})")
        return (
            "Here are the active discount campaigns currently configured:\n\n"
            + "\n".join(codes_list) + "\n\n"
            f"To redeem, you can ask me: `redeem WELCOME50` (currently acting as session user `{user_id}`)."
        )

    # 2. Registration check
    if any(k in prompt_lower for k in ["register", "sign up", "signup", "create user", "create account"]):
        res = register_user(user_id)
        return f"{res}"

    # 3. Redemption check
    code_match = re.search(r'(WELCOME50|SUMMER20)', prompt.upper())
    if code_match:
        code = code_match.group(1)
        res = redeem_discount_code(user_id, code)
        if "success" in res.lower():
            user = st.session_state["active_user"]
            if user not in st.session_state["used_codes"]:
                st.session_state["used_codes"][user] = set()
            st.session_state["used_codes"][user].add(code)
        return f"{res}"

    # 4. Fallback conversational response
    return (
        f"Hello! I am your AI Shopping Assistant. Currently interacting as registered user `{user_id}`.\n\n"
        "I can help you:\n"
        "1. **Search Products**: e.g., 'Find laptops under ₹70000'\n"
        "2. **Compare Products**: e.g., 'Compare iPhone 17 and Samsung S25'\n"
        "3. **Get Recommendations**: e.g., 'Recommend a gaming laptop'\n"
        "4. **Redeem Coupon**: e.g., 'Apply coupon WELCOME50'\n\n"
        "How can I help you today?"
    )

# Page Setup
st.set_page_config(
    page_title="ShopAssist AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Linear/Vercel inspired Premium Dark Theme)
st.markdown("""
<style>
[data-testid="stHeader"]{display:none!important}
[data-testid="stToolbar"]{display:none!important}
footer{display:none!important}
#MainMenu{display:none!important}

[data-testid="stAppViewContainer"]{background:#090D16!important}
[data-testid="stMain"]{background:#090D16!important}
[data-testid="stMainBlockContainer"]{background:#090D16!important;padding:0!important}

[data-testid="stSidebar"]{
  background:#05080E!important;
  border-right:1px solid #1E293B!important
}
[data-testid="stSidebar"] * {color:#E2E8F0!important}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {color:#E2E8F0!important}

[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div{
  background:#111827!important;
  border:1px solid #1E293B!important;
  border-radius:8px!important;
  color:#E2E8F0!important
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg{fill:#9CA3AF!important}

[data-testid="stSidebar"] [data-testid="stTextInput"] input{
  background:#111827!important;
  border:1px solid #1E293B!important;
  border-radius:8px!important;
  color:#E2E8F0!important
}
[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder{
  color:#6B7280!important
}

[data-testid="stSidebar"] button{
  background:#3B82F6!important;
  color:#ffffff!important;
  border:none!important;
  border-radius:8px!important;
  font-size:12px!important;
  font-weight:500!important
}
[data-testid="stSidebar"] button:hover{
  background:#2563EB!important;
  color:#ffffff!important
}

[data-testid="stChatMessage"]{
  background:transparent!important;
  border:none!important;
  padding:8px 0!important;
  box-shadow:none!important
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"]{
  background:transparent!important
}

[data-testid="stChatInput"]{
  background:#111827!important;
  border:1px solid #1E293B!important;
  border-radius:12px!important
}
[data-testid="stChatInput"] textarea{
  background:#111827!important;
  color:#F3F4F6!important
}

.stChatMessage--user [data-testid="stMarkdownContainer"] p{
  background:#3B82F6!important;
  color:#ffffff!important;
  border-radius:16px 16px 2px 16px!important;
  padding:12px 16px!important;
  display:inline-block!important;
  max-width:75%!important;
  font-size:14px!important;
  line-height:1.5!important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)!important
}
.stChatMessage--assistant [data-testid="stMarkdownContainer"] p{
  background:#1E293B!important;
  color:#E2E8F0!important;
  border:1px solid #334155!important;
  border-radius:16px 16px 16px 2px!important;
  padding:12px 16px!important;
  display:inline-block!important;
  max-width:80%!important;
  font-size:14px!important;
  line-height:1.5!important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)!important
}

.stButton > button{
  background:#3B82F6!important;
  color:#ffffff!important;
  border:none!important;
  border-radius:8px!important;
  font-size:13px!important;
  font-weight:500!important;
  padding:8px 16px!important;
  transition: all 0.2s ease!important
}
.stButton > button:hover{
  background:#2563EB!important;
  transform: translateY(-1px)!important;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3)!important
}

div[data-testid="column"] .stButton > button{
  background:#111827!important;
  color:#E2E8F0!important;
  border:1px solid #1E293B!important;
  border-radius:12px!important;
  padding:16px 8px!important;
  text-align:center!important;
  font-size:12px!important;
  font-weight:600!important;
  height:70px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  box-shadow: none!important;
  transition: all 0.2s ease!important
}
div[data-testid="column"] .stButton > button:hover{
  background:#1E293B!important;
  border-color:#3B82F6!important;
  color:#FFFFFF!important;
  transform: translateY(-2px)!important
}

.coupon-card{
  background:#111827;
  border:1px solid #1E293B;
  border-radius:12px;
  padding:14px;
  margin-bottom:12px;
  transition: border-color 0.2s ease;
}
.coupon-card:hover{
  border-color:#3B82F6;
}
.cbadge{
  display:inline-flex;
  align-items:center;
  gap:4px;
  background:rgba(59, 130, 246, 0.15);
  color:#60A5FA;
  font-size:10px;
  font-weight:600;
  padding:3px 8px;
  border-radius:6px;
  margin-bottom:6px
}
.ccode{
  font-size:14px;
  font-weight:600;
  color:#F3F4F6;
  font-family:monospace;
  letter-spacing:.04em
}
.cdesc{font-size:11px;color:#9CA3AF;margin-top:4px;margin-bottom:8px}
.used-lbl{font-size:11px;color:#10B981;font-weight:500}

.hero-container {
  text-align: center;
  padding: 60px 20px 40px;
  max-width: 650px;
  margin: 0 auto;
}
.hero-title {
  font-size: 40px;
  font-weight: 800;
  color: #FFFFFF;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #FFFFFF 0%, #93C5FD 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-subtitle {
  font-size: 16px;
  color: #9CA3AF;
  margin-bottom: 24px;
}
.hero-desc {
  font-size: 14px;
  color: #6B7280;
  line-height: 1.6;
}

.user-profile {
  background: #111827;
  border: 1px solid #1E293B;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #3B82F6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 16px;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #F3F4F6;
}
.user-tier {
  font-size: 11px;
  color: #9CA3AF;
}

/* Product Card Grid */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin: 12px 0;
}
.product-card {
  background: #111827;
  border: 1px solid #1E293B;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.2s ease;
}
.product-card:hover {
  border-color: #3B82F6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}
.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.product-category {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}
.product-price {
  font-size: 14px;
  font-weight: 700;
  color: #10B981;
}
.product-title {
  font-size: 15px;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 6px;
}
.product-desc {
  font-size: 12px;
  color: #9CA3AF;
  line-height: 1.4;
  margin-bottom: 12px;
  flex-grow: 1;
}
.product-id {
  font-size: 10px;
  color: #4B5563;
  font-family: monospace;
}

/* Style Markdown Tables */
div[data-testid="stMarkdownContainer"] table {
  width: 100%!important;
  border-collapse: collapse!important;
  margin: 16px 0!important;
  font-size: 14px!important;
  color: #E2E8F0!important;
}
div[data-testid="stMarkdownContainer"] th {
  background: #111827!important;
  border: 1px solid #1E293B!important;
  padding: 10px 14px!important;
  font-weight: 600!important;
  text-align: left!important;
}
div[data-testid="stMarkdownContainer"] td {
  border: 1px solid #1E293B!important;
  padding: 10px 14px!important;
  background: #0D111C!important;
}
div[data-testid="stMarkdownContainer"] tr:hover td {
  background: #1E293B!important;
}
</style>
""", unsafe_allow_html=True)

def parse_and_render_search_results(text: str):
    # Split text into lines
    lines = text.split("\n")
    products = []
    
    # Extract values from table rows
    for line in lines:
        if line.strip().startswith("|") and not "Product ID" in line and not "---" in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                p_id = parts[0]
                name = parts[1].replace("**", "")
                category = parts[2]
                price = parts[3]
                desc = parts[4]
                products.append({
                    "id": p_id,
                    "name": name,
                    "category": category,
                    "price": price,
                    "description": desc
                })
                
    if products:
        # Build HTML grid
        html = '<div class="product-grid">'
        for p in products:
            html += f"""
<div class="product-card">
  <div class="product-header">
    <span class="product-category">{p['category']}</span>
    <span class="product-price">{p['price']}</span>
  </div>
  <div class="product-title">{p['name']}</div>
  <div class="product-desc">{p['description']}</div>
  <div class="product-id">ID: {p['id']}</div>
</div>
"""
        html += '</div>'
        # Display the leading text before the table, if any
        leading_lines = []
        for line in lines:
            if line.strip().startswith("|"):
                break
            if line.strip():
                leading_lines.append(line)
        if leading_lines:
            st.markdown("\n".join(leading_lines))
        st.markdown(html, unsafe_allow_html=True)
        return True
    return False

def parse_and_render_recommendations(text: str):
    # Check if this contains recommended products list
    if "### Recommended" not in text:
        return False
        
    lines = text.split("\n")
    recommendations = []
    current_rec = None
    
    for line in lines:
        stripped = line.strip()
        # Match "1. **Name** (Price)" or similar
        match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*\s+\((.+?)\)', stripped)
        if match:
            if current_rec:
                recommendations.append(current_rec)
            current_rec = {
                "name": match.group(1),
                "price": match.group(2),
                "specs": "",
                "description": ""
            }
        elif stripped.startswith("- *Specs*:") and current_rec:
            current_rec["specs"] = stripped.replace("- *Specs*:", "").strip()
        elif stripped.startswith("- *Why this is a good fit*:") and current_rec:
            current_rec["description"] = stripped.replace("- *Why this is a good fit*:", "").strip()
            
    if current_rec:
        recommendations.append(current_rec)
        
    if recommendations:
        # Build HTML grid for recommendations
        html = '<div class="product-grid">'
        for r in recommendations:
            # Guess category from title or specs
            category = "Recommendation"
            if "laptop" in r['name'].lower() or "macbook" in r['name'].lower():
                category = "Laptops"
            elif "iphone" in r['name'].lower() or "samsung" in r['name'].lower() or "oneplus" in r['name'].lower() or "redmi" in r['name'].lower():
                category = "Mobiles"
            elif "watch" in r['name'].lower() or "fitbit" in r['name'].lower():
                category = "Wearables"
            elif "buds" in r['name'].lower() or "sony" in r['name'].lower() or "airpods" in r['name'].lower():
                category = "Audio"
            elif "echo" in r['name'].lower() or "nest" in r['name'].lower():
                category = "Smart Home"
                
            html += f"""
<div class="product-card">
  <div class="product-header">
    <span class="product-category">{category}</span>
    <span class="product-price">{r['price']}</span>
  </div>
  <div class="product-title">{r['name']}</div>
  <div class="product-desc" style="margin-bottom: 6px;"><b>Specs</b>: {r['specs']}</div>
  <div class="product-desc"><i>{r['description']}</i></div>
</div>
"""
        html += '</div>'
        
        # Display title
        title_line = "### Recommended Products"
        for line in lines:
            if "### Recommended" in line:
                title_line = line
                break
        st.markdown(title_line)
        st.markdown(html, unsafe_allow_html=True)
        return True
    return False

# Consume pending_message trigger if trigger_send is True
if st.session_state.get("trigger_send") and st.session_state.get("pending_message"):
    user_input = st.session_state["pending_message"]
    # Append user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    save_message(st.session_state["active_user"], "user", user_input)
    # Reset trigger flags
    st.session_state["trigger_send"] = False
    st.session_state["pending_message"] = ""
    st.rerun()

# Two-column Layout: Left column (Sidebar content) & Right column (Main Chat Area)
col_left, col_right = st.columns([1, 2.5])

# Left column acting as sidebar
with col_left:
    # 1. BRANDING HEADER
    st.markdown("### 🛍️ ShopAssist AI")
    st.markdown("<p style='color:#9CA3AF; font-size: 12px; margin-top: -10px;'>Your AI shopping copilot</p>", unsafe_allow_html=True)

    # User Profile Block
    active_user = st.session_state["active_user"]
    initial = active_user[0].upper() if active_user else "U"
    st.markdown(f"""
<div class="user-profile">
  <div class="user-avatar">{initial}</div>
  <div class="user-info">
    <div class="user-name">{active_user}</div>
    <div class="user-tier">Loyalty Member</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # 2. AVAILABLE COUPONS
    st.markdown("#### Available Coupons")
    user = st.session_state["active_user"]
    used = st.session_state["used_codes"].get(user, set())

    coupon_descriptions = {
        "WELCOME50": "Get 50% off on your first order",
        "SUMMER20": "Save 20% on all summer catalog items"
    }

    for code, info in DISCOUNT_CODES.items():
        discount_pct = info["discount"]
        description = coupon_descriptions.get(code, "Discount coupon code.")
        is_used = code in used or info["used"]
        
        st.markdown(f"""
<div class="coupon-card">
  <div class="cbadge">🏷 {discount_pct}% OFF</div>
  <div class="ccode">{code}</div>
  <div class="cdesc">{description}</div>
</div>
""", unsafe_allow_html=True)
        
        if is_used:
            st.markdown('<div class="used-lbl">✓ Coupon Redeemed</div>', unsafe_allow_html=True)
        else:
            if st.button("Apply Code", key=f"redeem_{code.lower()}", use_container_width=True):
                st.toast(f"🎟️ Redeeming {code}...", icon="✅")
                st.session_state["pending_message"] = f"Redeem coupon code {code} for user {st.session_state['active_user']}"
                st.session_state["trigger_send"] = True
                
                user = st.session_state["active_user"]
                if user not in st.session_state["used_codes"]:
                    st.session_state["used_codes"][user] = set()
                st.session_state["used_codes"][user].add(code)
                st.rerun()
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    st.divider()

    # 3. ACTIVE SESSION Selector
    st.markdown("#### Switch Profile")
    selected = st.selectbox(
        "Switch User Profile",
        options=st.session_state["registered_users"],
        index=st.session_state["registered_users"].index(
            st.session_state["active_user"]
        ),
        label_visibility="collapsed"
    )
    st.session_state["active_user"] = selected

    # Create new account input
    new_name = st.text_input("New username", placeholder="Add profile ID...", label_visibility="collapsed")
    if st.button("Add Account", key="reg_btn", use_container_width=True):
        name = new_name.strip()
        if not name:
            st.error("Enter a username.")
        elif name in st.session_state["registered_users"]:
            st.warning(f"{name} already registered.")
        else:
            st.session_state["registered_users"].append(name)
            st.session_state["active_user"] = name
            st.session_state["pending_message"] = f"Register new user with ID: {name}"
            st.session_state["trigger_send"] = True
            st.success(f"✓ Registered {name}!")
            st.rerun()

# Right column acting as Main Chat Area
with col_right:
    # Header bar
    st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
  padding:12px 0 16px;border-bottom:1px solid #1E293B;margin-bottom:14px">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:16px;font-weight:600;color:#FFFFFF">
      💬 Chat Assistant
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    # 3. CHAT HISTORY OR HERO
    if not st.session_state["messages"]:
        st.markdown("""
<div class="hero-container">
  <div class="hero-title">ShopAssist AI</div>
  <div class="hero-subtitle">Your personal shopping assistant powered by Gemini</div>
  <div class="hero-desc">
    Ask me about products, discover ongoing deals, register your account, and redeem coupon codes instantly. Let's make shopping seamless.
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
        act_cols = st.columns(4)
        with act_cols[0]:
            if st.button("🛍️ Find Products", use_container_width=True, key="action_find"):
                st.session_state["pending_message"] = "Find laptops under ₹70000"
                st.session_state["trigger_send"] = True
                st.rerun()
        with act_cols[1]:
            if st.button("🔄 Compare Products", use_container_width=True, key="action_compare"):
                st.session_state["pending_message"] = "Compare iPhone 17 and Samsung S25"
                st.session_state["trigger_send"] = True
                st.rerun()
        with act_cols[2]:
            if st.button("⭐ Recommend Products", use_container_width=True, key="action_recommend"):
                st.session_state["pending_message"] = "Recommend a gaming laptop"
                st.session_state["trigger_send"] = True
                st.rerun()
        with act_cols[3]:
            if st.button("🏷️ View Discounts", use_container_width=True, key="action_discounts"):
                st.session_state["pending_message"] = "Show available discounts"
                st.session_state["trigger_send"] = True
                st.rerun()
    else:
        for msg in st.session_state["messages"]:
            content = msg["content"]
            lines = content.split("\n")
            reply_lines = []
            for line in lines:
                stripped = line.strip()
                # Skip tool call / tool result lines or indicator symbols
                if not (stripped.startswith("tool_call:") or stripped.startswith("tool_result:") or stripped.startswith("✓") or stripped.startswith("⚙")):
                    if stripped:
                        reply_lines.append(stripped)
            
            if reply_lines:
                msg_text = "\n".join(reply_lines)
                with st.chat_message(msg["role"]):
                    rendered = False
                    if msg["role"] == "assistant":
                        if "Product ID | Name | Category | Price | Description" in msg_text:
                            rendered = parse_and_render_search_results(msg_text)
                        elif "### Recommended" in msg_text:
                            rendered = parse_and_render_recommendations(msg_text)
                    
                    if not rendered:
                        st.markdown(msg_text)

    # If the last message is from user, fetch response from backend or fallback
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
        user_input = st.session_state["messages"][-1]["content"]

        with st.chat_message("assistant"):
            # Prepare mock/fallback prefix if needed
            is_redeem = "redeem" in user_input.lower() or "apply" in user_input.lower()
            is_register = "register" in user_input.lower() or "sign up" in user_input.lower() or "signup" in user_input.lower()

            tool_call_prefix = ""
            if is_redeem:
                code_match = re.search(r'(WELCOME50|SUMMER20)', user_input.upper())
                if code_match:
                    tool_call_prefix = f"tool_call: redeem_discount_code(user_id='{st.session_state['active_user']}', code='{code_match.group(1)}')\n"
            elif is_register:
                tool_call_prefix = f"tool_call: register_user(user_id='{st.session_state['active_user']}')\n"

            # Execute requests logic
            import json

            full_response = ""
            tool_lines = []

            try:
                with requests.post(
                    "http://localhost:8000/chat",
                    json={
                        "message": user_input,
                        "user_id": st.session_state["active_user"]
                    },
                    stream=True,
                    timeout=60
                ) as resp:
                    resp.raise_for_status()
                    for raw_line in resp.iter_lines(decode_unicode=True):
                        if not raw_line or not raw_line.startswith("data:"):
                            continue
                        data_str = raw_line[5:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(data_str)
                            # ADK sends different event types — only render "text" type
                            event_type = chunk.get("type", "")
                            if event_type == "tool_call" or event_type == "tool_use":
                                name = chunk.get("name", "unknown_tool")
                                args = chunk.get("args") or chunk.get("input") or {}
                                args_str = ", ".join(
                                    f'{k}="{v}"' for k, v in args.items()
                                )
                                tool_lines.append(f"tool_call: {name}({args_str})")
                            elif event_type in ("text", "message", "content", ""):
                                text = (
                                    chunk.get("text") or
                                    chunk.get("content") or
                                    chunk.get("message") or
                                    chunk.get("response") or ""
                                )
                                # Skip if this looks like raw args JSON, not a reply
                                if text and not any(
                                    k in text for k in ["user_id", "code=", "args"]
                                ):
                                    full_response += text
                        except json.JSONDecodeError:
                            # Plain text line — only keep if it looks like a sentence
                            stripped = data_str.strip()
                            if stripped.startswith("tool_call:"):
                                tool_lines.append(stripped)
                            elif len(stripped) > 10 and not stripped.startswith("{"):
                                full_response += stripped

            except requests.exceptions.ConnectionError:
                full_response = (
                    "⚠️ Agent offline. Run: cd backend && "
                    "uv run uvicorn app.main:app --reload"
                )
            except Exception as e:
                full_response = f"⚠️ Error: {str(e)}"

            # Build final stored message
            combined_parts = tool_lines + (
                [full_response.strip()] if full_response.strip() else []
            )
            combined = "\n".join(combined_parts)
            
            # Ensure we prepended tool call prefix for mock fallback path if it was used
            if ("Agent offline" in combined or "⚠️ Error:" in combined) and tool_call_prefix:
                mock_tool_list = [tool_call_prefix.strip()]
                fallback_text = generate_fallback_response(user_input, st.session_state["active_user"])
                combined = "\n".join(mock_tool_list)
                if fallback_text.strip():
                    combined += ("\n" if combined else "") + fallback_text.strip()

            st.session_state["messages"].append({
                "role": "assistant",
                "content": combined
            })
            save_message(st.session_state["active_user"], "assistant", combined)
            st.rerun()

# CHAT INPUT
if prompt := st.chat_input("Ask about products, redeem a code…"):
    st.session_state["pending_message"] = prompt
    st.session_state["trigger_send"] = True
    st.rerun()
