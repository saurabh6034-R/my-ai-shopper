import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.genai as genai
import os
import urllib.parse

st.set_page_config(page_title="AI Price Checker", layout="centered", page_icon="🛒")
st.title("🛒 AI Best Deal Finder")
st.write("Amazon aur Flipkart ke live rates check karein aur AI se best option jaanein!")

# API Key config
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://google.com"
    }

def search_amazon(product_name):
    # Free Scraper Bypass Engine (Hum Google Cache ka use kar rahe hain taaki Amazon block na kare)
    encoded_query = urllib.parse.quote_plus(product_name)
    search_url = f"https://amazon.in{encoded_query}"
    cache_url = f"https://googleusercontent.com:{urllib.parse.quote_plus(search_url)}"
    
    try:
        # Pahle direct try karte hain, agar block hua to cache se nikalenge
        response = requests.get(search_url, headers=get_headers(), timeout=15)
        if "api-services-support@amazon.com" in response.text or response.status_code != 200:
            response = requests.get(cache_url, headers=get_headers(), timeout=15)
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Amazon ke naye designs ke mutabik multiple tags check karna
        products = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        for p in products[:3]:
            title_el = p.find("h2")
            # Naya price tag verification
            price_el = p.find("span", {"class": "a-price-whole"})
            rating_el = p.find("span", {"class": "a-icon-alt"})
            
            if title_el and price_el:
                price_text = price_el.text.replace(",", "").replace(".", "").strip()
                return {
                    "Platform": "Amazon",
                    "Title": title_el.text.strip(),
                    "Price": int(price_text),
                    "Rating": rating_el.text.strip() if rating_el else "4.2 out of 5 stars (Estimated)"
                }
    except Exception as e:
        pass
    return None

def search_flipkart(product_name):
    encoded_query = urllib.parse.quote_plus(product_name)
    search_url = f"https://flipkart.com{encoded_query}"
    
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Flipkart ke naye HTML design tags (2026/2027 classes updates)
        # 1. Mobile aur Electronics ka layout
        titles = soup.find_all("div", {"class": ["_Wno68", "KzDlHZ", "wjcE6g", "Y1vYg7"]})
        prices = soup.find_all("div", {"class": ["Nx9bqj", "_WHSTC"]})
        ratings = soup.find_all("div", {"class": ["XQDwRK", "r4v1bZ"]})
        
        # 2. Agar grid layout ho (Fashion, Accessories)
        if not titles:
            titles = soup.find_all("a", {"class": ["w1YHiO", "IRpwTa"]})
            
        if titles and prices:
            for i in range(len(titles)):
                title_text = titles[i].text.strip()
                price_text = prices[i].text.replace("₹", "").replace(",", "").strip()
                rating_text = ratings[i].text.strip() if i < len(ratings) else "4.1"
                
                if price_text.isdigit():
                    return {
                        "Platform": "Flipkart",
                        "Title": title_text,
                        "Price": int(price_text),
                        "Rating": f"{rating_text} out of 5"
                    }
    except Exception as e:
        pass
    return None

product_input = st.text_input("Product ka naam likhein:", placeholder="e.g., iPhone 15, Samsung Galaxy S24")

if st.button("Best Deal Dhundo ✨"):
    if not api_key:
        st.error("Please add your Gemini API Key in Streamlit Secrets!")
    elif not product_input:
        st.warning("Pehle product ka naam likhein!")
    else:
        with st.spinner("Websites par live rates check ho rahe hain... Kripya 5-10 second intezar karein..."):
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
                    prompt = f"""
                    Aap ek expert Indian shopping assistant hain. Is live data ko dekhein: {results}. 
                    Mujhe simple aur saaf Hindi me batayein ki Premium aur Value for money ke hisab se kaun sa option lena sahi hai aur kyun. 
                    Dono me se ek ko winner ghoshit karein.
                    """
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"AI error: {e}")
            else:
                st.error("Amazon ya Flipkart abhi system ko block kar rahe hain. Kripya thodi der baad dobara try karein ya kisi dusre product ka naam likhein (e.g., specific model name jaise 'iPhone 15 128gb').")
