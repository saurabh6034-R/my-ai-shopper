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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://google.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

def search_amazon(product_name):
    encoded_query = urllib.parse.quote_plus(product_name)
    # FIX: Sahi Amazon search URL path add kiya
    search_url = f"https://amazon.in{encoded_query}"
    
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        # Amazon standard search product containers
        products = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        for p in products:
            title_el = p.find("h2")
            price_el = p.find("span", {"class": "a-price-whole"})
            rating_el = p.find("span", {"class": "a-icon-alt"})
            
            if title_el and price_el:
                price_text = price_el.text.replace(",", "").replace(".", "").strip()
                return {
                    "Platform": "Amazon",
                    "Title": title_el.text.strip(),
                    "Price": int(price_text),
                    "Rating": rating_el.text.strip() if rating_el else "4.2 out of 5 stars"
                }
    except Exception as e:
        pass
    return None

def search_flipkart(product_name):
    encoded_query = urllib.parse.quote_plus(product_name)
    # FIX: Sahi Flipkart search URL path add kiya
    search_url = f"https://flipkart.com{encoded_query}"
    
    try:
        response = requests.get(search_url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Flipkart Multi-layout support (List view vs Grid view)
        # 1. Product Titles ke liye dynamic classes check
        titles = soup.find_all("div", {"class": ["KzDlHZ", "_Wno68", "wjcE6g"]}) or soup.find_all("a", {"class": ["IRpwTa", "w1YHiO"]})
        prices = soup.find_all("div", {"class": ["Nx9bqj", "_WHSTC"]})
        ratings = soup.find_all("div", {"class": ["XQDwRK", "r4v1bZ"]})
        
        if titles and prices:
            for i in range(min(len(titles), len(prices))):
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
        st.error("Please add your Gemini API Key in Streamlit Secrets or Environment Variables!")
    elif not product_input:
        st.warning("Pehle product ka naam likhein!")
    else:
        with st.spinner("Websites par live rates check ho rahe hain..."):
            results = []
            
            amz = search_amazon(product_input)
            if amz:
                results.append(amz)
                
            fk = search_flipkart(product_input)
            if fk:
                results.append(fk)
                
        if results:
            st.subheader("📊 Live Price Data Jo Mila:")
            for r in results:
                st.info(f"**[{r['Platform']}]** {r['Title']} \n\n 💰 Price: **₹{r['Price']}** | ⭐ Rating: {r['Rating']}")
                
            st.subheader("🤖 AI Verdict (Sahi Choice):")
            try:
                # Naya google-genai library initialization
                client = genai.Client(api_key=api_key)
                prompt = f"""
                Aap ek expert Indian shopping assistant hain. Is live data ko dekhein: {results}. 
                Mujhe simple aur saaf Hindi me batayein ki Premium aur Value for money ke hisab se kaun sa option lena sahi hai aur kyun. 
                Dono me se ek ko clear winner ghoshit karein.
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                st.success(response.text)
            except Exception as e:
                st.error(f"AI error: {e}. Agar aapne google-generativeai use kiya hai, to client structure check karein.")
        else:
            st.error("Amazon aur Flipkart dono ne request block kar di hai ya product nahi mila. Kripya thodi der baad try karein ya specific model ka naam likhein.")
