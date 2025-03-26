import streamlit as st
import requests
from datetime import datetime

# Google Custom Search credentials (replace with yours)
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
CSE_ID = "YOUR_CSE_ID"
AMAZON_ASSOCIATE_TAG = "yourid-20"  # Replace with your Amazon Associate Tag

# Function to search products
def search_products(query, max_price=None, sort_by="relevance"):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query} site:amazon.com -inurl:(login signup)"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])[:10]  # Get more results for filtering
        results = []
        for item in items:
            title = item["title"]
            link = f"{item['link']}&tag={AMAZON_ASSOCIATE_TAG}"
            price_str = item.get("snippet", "").split("$")[1].split(" ")[0] if "$" in item.get("snippet", "") else "N/A"
            price = float(price_str) if price_str != "N/A" and price_str.replace(".", "").isdigit() else None
            if price and max_price and price > max_price:
                continue
            results.append({"title": title, "price": price if price else "N/A", "link": link})
        
        # Sort results
        if sort_by == "price_asc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("inf"))
        elif sort_by == "price_desc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("-inf"), reverse=True)
        
        return results[:5]  # Limit to 5 after filtering/sorting
    except Exception as e:
        st.error(f"Search failed: {e}. Try again later!")
        return []

# Custom CSS for styling
st.markdown("""
    <style>
    .main {background-color: #f0f2f6;}
    .stTextInput > div > div > input {border-radius: 10px; padding: 10px;}
    .stButton > button {background-color: #4CAF50; color: white; border-radius: 10px;}
    .result-box {border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px; background-color: white;}
    .sidebar .sidebar-content {background-color: #ffffff;}
    </style>
""", unsafe_allow_html=True)

# App layout
st.title("🛒 ShopBot - Your Smart Shopping Buddy")
st.subheader("Find the best deals across the web instantly!")

# Sidebar for filters and history
with st.sidebar:
    st.header("Options")
    max_price = st.slider("Max Price ($)", 0, 500, 100, step=10)
    sort_by = st.selectbox("Sort By", ["relevance", "price_asc", "price_desc"], 
                          format_func=lambda x: {"relevance": "Relevance", "price_asc": "Price: Low to High", "price_desc": "Price: High to Low"}[x])
    st.write("---")
    st.header("Chat History")
    if "history" not in st.session_state:
        st.session_state.history = []
    for entry in st.session_state.history:
        st.write(f"**{entry['time']}**: {entry['query']}")

# Chat input
query = st.text_input("What do you want to buy?", placeholder="e.g., cheap gaming mouse", key="query_input")
search_button = st.button("Search")

# Process search
if search_button and query:
    with st.spinner("Fetching deals..."):
        results = search_products(query, max_price, sort_by)
        if results:
            # Add to history
            st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "query": query})
            st.success(f"Found {len(results)} items for '{query}':")
            for result in results:
                with st.container():
                    st.markdown(f"<div class='result-box'>", unsafe_allow_html=True)
                    st.write(f"**{result['title']}**")
                    st.write(f"Price: ${result['price']}")
                    st.markdown(f"[Buy Now]({result['link']})", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No results found. Try a broader query!")

# Footer
st.markdown("---")
st.write("Powered by Google Search & Amazon Associates. ShopBot earns a commission on purchases.")