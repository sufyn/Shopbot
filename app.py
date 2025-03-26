import streamlit as st
import requests
from datetime import datetime

# Google Custom Search credentials (replace with yours)
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
CSE_ID = "YOUR_CSE_ID"
AMAZON_ASSOCIATE_TAG = "yourid-20"  # Replace with your Amazon Associate Tag

# Function to search products with images
def search_products(query, max_price=None, sort_by="relevance", category="all"):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query} site:amazon.com -inurl:(login signup)&searchType=image"
    if category != "all":
        url += f" {category}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])[:10]  # Get more for filtering
        results = []
        for item in items:
            title = item["title"]
            link = f"{item['link']}&tag={AMAZON_ASSOCIATE_TAG}"
            image = item["image"]["thumbnailLink"] if "image" in item else None
            price_str = item.get("snippet", "").split("$")[1].split(" ")[0] if "$" in item.get("snippet", "") else "N/A"
            price = float(price_str) if price_str != "N/A" and price_str.replace(".", "").isdigit() else None
            if price and max_price and price > max_price:
                continue
            results.append({"title": title, "price": price if price else "N/A", "link": link, "image": image})
        
        # Sort results
        if sort_by == "price_asc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("inf"))
        elif sort_by == "price_desc" and any(r["price"] != "N/A" for r in results):
            results = sorted(results, key=lambda x: x["price"] if x["price"] != "N/A" else float("-inf"), reverse=True)
        
        return results[:5]  # Limit to 5 after filtering/sorting
    except Exception as e:
        st.error(f"Search failed: {e}. Try again or check your API quota!")
        return []

# Custom CSS for a modern, beautiful design
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stTextInput > div > div > input {border-radius: 15px; padding: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .stButton > button {background-color: #007bff; color: white; border-radius: 15px; padding: 10px 20px; font-weight: bold;}
    .stButton > button:hover {background-color: #0056b3;}
    .card {border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; background-color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 15px;}
    .sidebar .sidebar-content {background-color: #ffffff; border-right: 1px solid #ddd;}
    h1 {color: #343a40; font-family: 'Arial', sans-serif;}
    h3 {color: #495057;}
    </style>
""", unsafe_allow_html=True)

# App layout
st.title("🛒 ShopBot - Discover Deals with Style")
st.subheader("Search for products and see them come to life with images!")

# Sidebar for filters and history
with st.sidebar:
    st.header("🔧 Filters")
    max_price = st.slider("Max Price ($)", 0, 1000, 100, step=10)
    sort_by = st.selectbox("Sort By", ["relevance", "price_asc", "price_desc"], 
                          format_func=lambda x: {"relevance": "Relevance", "price_asc": "Price: Low to High", "price_desc": "Price: High to Low"}[x])
    category = st.selectbox("Category", ["all", "electronics", "books", "clothing", "home"])
    if st.button("Reset Filters"):
        max_price, sort_by, category = 100, "relevance", "all"
    st.write("---")
    st.header("📜 Chat History")
    if "history" not in st.session_state:
        st.session_state.history = []
    for entry in st.session_state.history[-5:]:  # Show last 5 entries
        st.write(f"**{entry['time']}**: {entry['query']}")

# Chat input
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("What are you shopping for?", placeholder="e.g., gaming mouse, blue jacket", key="query_input")
with col2:
    search_button = st.button("Search", use_container_width=True)

# Process search
if search_button and query:
    with st.spinner("🔍 Finding the best deals..."):
        results = search_products(query, max_price, sort_by, category)
        if results:
            # Add to history
            st.session_state.history.append({"time": datetime.now().strftime("%H:%M:%S"), "query": query})
            st.success(f"Found {len(results)} items for '{query}':")
            for result in results:
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if result["image"]:
                            st.image(result["image"], width=100)
                        else:
                            st.write("No image")
                    with col_info:
                        st.write(f"**{result['title']}**")
                        st.write(f"Price: ${result['price']}")
                        st.markdown(f"[Buy Now]({result['link']})", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No results found. Try a different query or category!")

# Footer
st.markdown("---")
st.write("Powered by Google Image Search & Amazon Associates. ShopBot earns a commission on purchases.")