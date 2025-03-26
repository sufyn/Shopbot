import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime
import plotly.express as px

# Credentials (replace with yours)
GOOGLE_API_KEY = "AIzaSyCfjAmnam4j9zK0faKujemRlQcX9V7_VAw"  # For Custom Search
CSE_ID = "402346d0d45834b80"
GEMINI_API_KEY = "AIzaSyBKt7IFiTNUtZUD9I0cDmmRKjoAF1ufXpo"  # For Generative AI

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")  # Adjust model name when available

# Function to search products (no affiliates)
def search_products(query, min_price=None, max_price=None, sort_by="relevance", category="all", exclude=""):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query} site:*.com -inurl:(login signup)&searchType=image"
    if category != "all":
        url += f" {category}"
    if exclude:
        url += f" -{exclude}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])[:10]
        results = []
        for item in items:
            title = item["title"]
            link = item["link"]  # No affiliate tag
            image = item["image"]["thumbnailLink"] if "image" in item else "https://via.placeholder.com/100?text=No+Image"
            price_str = item.get("snippet", "").split("$")[1].split(" ")[0] if "$" in item.get("snippet", "") else "N/A"
            price = float(price_str) if price_str != "N/A" and price_str.replace(".", "").isdigit() else None
            snippet = item.get("snippet", "No description available.")
            if price and ((min_price and price < min_price) or (max_price and price > max_price)):
                continue
            results.append({"title": title, "price": price if price else "N/A", "link": link, "image": image, "snippet": snippet})
        
        if sort_by == "price_asc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("inf"))
        elif sort_by == "price_desc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("-inf"), reverse=True)
        
        return results[:5]
    except Exception as e:
        return []

# Custom CSS
def load_css(dark_mode=False):
    if dark_mode:
        st.markdown("""
            <style>
            .main {background-color: #2c2f33; color: #ffffff;}
            .stTextInput > div > div > input {border-radius: 15px; padding: 12px; background-color: #3a3f44; color: #ffffff; border: 1px solid #555;}
            .stButton > button {background: linear-gradient(90deg, #7289da, #4e5d94); color: white; border-radius: 15px; padding: 10px 20px; font-weight: bold;}
            .stButton > button:hover {background: linear-gradient(90deg, #5a6eb8, #3b4a7a);}
            .card {border: 1px solid #444; border-radius: 10px; padding: 15px; background-color: #36393f; box-shadow: 0 4px 8px rgba(0,0,0,0.2); margin-bottom: 15px;}
            .sidebar .sidebar-content {background-color: #2f3136; border-right: 1px solid #444; color: #ffffff;}
            h1, h3 {color: #ffffff;}
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .main {background-color: #f8f9fa;}
            .stTextInput > div > div > input {border-radius: 15px; padding: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
            .stButton > button {background: linear-gradient(90deg, #007bff, #00c4cc); color: white; border-radius: 15px; padding: 10px 20px; font-weight: bold;}
            .stButton > button:hover {background: linear-gradient(90deg, #0056b3, #009ba1);}
            .card {border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; background-color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 15px;}
            .sidebar .sidebar-content {background-color: #ffffff; border-right: 1px solid #ddd;}
            h1 {color: #343a40;}
            h3 {color: #495057;}
            </style>
        """, unsafe_allow_html=True)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "query_counts" not in st.session_state:
    st.session_state.query_counts = {}

# Load CSS
load_css(st.session_state.dark_mode)

# Sidebar for page selection and settings
with st.sidebar:
    st.header("Navigation")
    page = st.selectbox("Choose Page", ["Chatbot", "E-commerce Search"])
    st.write("---")
    st.header("Settings")
    if st.button("Toggle Dark Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    st.write("---")
    st.header("Favorites")
    with st.expander("View Favorites"):
        for i, fav in enumerate(st.session_state.favorites):
            st.write(f"- {fav['title']} (${fav['price']})")
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.favorites.pop(i)
                st.rerun()

# Main page logic
if page == "Chatbot":
    st.title("💬 ShopBot Chat - Ask Me Anything!")
    st.subheader("Chat with me for help, ideas, or shopping advice!")

    # Chat input
    user_input = st.text_input("Type your message...", key="chat_input")
    if st.button("Send"):
        if user_input:
            with st.spinner("Thinking..."):
                response = model.generate_content(user_input)  # Gemini API call
                st.session_state.chat_history.append({"user": user_input, "bot": response.text})
    
    # Display chat history
    for chat in st.session_state.chat_history:
        st.markdown(f"**You**: {chat['user']}")
        st.markdown(f"**ShopBot**: {chat['bot']}")
        st.write("---")

elif page == "E-commerce Search":
    st.title("🛒 ShopBot Search - Find Products Online")
    st.subheader("Search for products with images across the web!")

    # Filters
    with st.expander("Advanced Filters"):
        min_price = st.slider("Min Price ($)", 0, 500, 0, step=5)
        max_price = st.slider("Max Price ($)", min_price, 1000, 100, step=10)
        sort_by = st.selectbox("Sort By", ["relevance", "price_asc", "price_desc"], 
                              format_func=lambda x: {"relevance": "Relevance", "price_asc": "Price: Low to High", "price_desc": "Price: High to Low"}[x])
        category = st.selectbox("Category", ["all", "electronics", "books", "clothing", "home", "toys"])
        exclude = st.text_input("Exclude Keywords", placeholder="e.g., used refurbished")
        if st.button("Reset Filters"):
            min_price, max_price, sort_by, category, exclude = 0, 100, "relevance", "all", ""

    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("What are you shopping for?", placeholder="e.g., gaming mouse", key="search_input")
    with col2:
        search_button = st.button("Search", use_container_width=True)

    # Process search
    if search_button and query:
        with st.spinner("🔍 Finding products..."):
            results = search_products(query, min_price, max_price, sort_by, category, exclude)
            if results:
                st.session_state.query_counts[query] = st.session_state.query_counts.get(query, 0) + 1
                st.success(f"Found {len(results)} items for '{query}':")
                for result in results:
                    with st.container():
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        col_img, col_info = st.columns([1, 2])
                        with col_img:
                            st.image(result["image"], width=100)
                        with col_info:
                            st.write(f"**{result['title']}**")
                            st.write(f"Price: ${result['price']}")
                            st.write(f"Details: {result['snippet'][:100]}..." if len(result['snippet']) > 100 else result['snippet'])
                            st.markdown(f"[View Product]({result['link']})", unsafe_allow_html=True)
                            if st.button("Add to Favorites", key=result["link"]):
                                if result not in st.session_state.favorites:
                                    st.session_state.favorites.append(result)
                                    st.success(f"Added '{result['title']}' to favorites!")
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No results found. Try a different query!")

# Footer
st.markdown("---")
st.write("Powered by Google Image Search & Gemini AI.")