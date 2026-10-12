import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.genai as genai
import os

st.set_page_config(page_title="AI Price Checker", layout="centered")
st.title("🛒 AI Best Deal Finder")
st.write("Amazon aur Flipkart ke live rates check karein aur AI se best option jaanein!")

# API Key config
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

def search_amazon(product_name):
    search_url = f"https://amazon.in{product_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, "html.parser")
        products = soup.find_all("div", {"data-component-type": "s-search-result"})
        for p in products[:2]:
            title_el = p.find("h2")
            price_el = p.find("span", "a-price-whole")
            rating_el = p.find("span", "a-icon-alt")
            if title_el and price_el:
                return {
                    "Platform": "Amazon",
                    "Title": title_el.text.strip(),
                    "Price": int(price_el.text.replace(",", "").replace(".", "").strip()),
                    "Rating": rating_el.text.split()[0] if rating_el else "N/A"
                }
    except: return None

def search_flipkart(product_name):
    search_url = f"https://flipkart.com{product_name.replace(' ', '%20')}"
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, "html.parser")
        titles = soup.find_all("div", {"class": ["_Wno68", "KzDlHZ", "wjcE6g"]}) 
        prices = soup.find_all("div", {"class": "Nx9bqj"})
        ratings = soup.find_all("div", {"class": "XQDwRK"})
        if titles and prices:
            price_clean = prices[0].text.replace("₹", "").replace(",", "").strip()
            return {
                "Platform": "Flipkart",
                "Title": titles[0].text.strip(),
                "Price": int(price_clean),
                "Rating": ratings[0].text.strip() if ratings else "N/A"
            }
    except: return None

product_input = st.text_input("Product ka naam likhein:", placeholder="e.g., iPhone 15 128gb")

if st.button("Best Deal Dhundo ✨"):
    if not api_key:
        st.error("Please add your Gemini API Key in Streamlit Secrets!")
    elif not product_input:
        st.warning("Pehle product ka naam likhein!")
    else:
        with st.spinner("Websites par rates check ho rahe hain... Please wait..."):
            results = []
            amz = search_amazon(product_input)
            if amz: results.append(amz)
            fk = search_flipkart(product_input)
            if fk: results.append(fk)
            
            if results:
                st.subheader("📊 Live Price Data Jo Mila:")
                for r in results:
                    st.info(f"**[{r['Platform']}]** {r['Title']} \n\n 💰 Price: **₹{r['Price']}** | ⭐ Rating: {r['Rating']}")
                
                st.subheader("🤖 AI Verdict (Sahi Choice):")
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"Aap ek expert shopping assistant hain. Is data ko dekhein: {results}. Mujhe simple Hindi me batayein ki Premium aur Value for money ke hisab se kaun sa option lena sahi hai aur kyun."
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"AI error: {e}")
            else:
                st.error("Amazon ya Flipkart se koi data nahi mila. Ek baar phir sahi naam daal kar try karein.")
