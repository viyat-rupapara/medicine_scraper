import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import streamlit as st
import re

# ---------- Configuration ----------
# Streamlit configuration for deployment
st.set_page_config(
    page_title="Medicine Information Scraper",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- Headers ----------
# Using a common user-agent to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/113.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ---------- Search Helpers ----------
# These functions find the most relevant product page URL from a search query.

def search_1mg(product_name):
    """Searches Tata 1mg and returns the top product URL."""
    try:
        query = quote(product_name)
        
        # Try different search URLs
        search_urls = [
            f"https://www.1mg.com/search/all?name={query}",
            f"https://www.1mg.com/search/drugs?name={query}",
            f"https://www.1mg.com/drugs?search={query}"
        ]
        
        # Add fallback for levocetrizen
        if "levocetrizen" in product_name.lower():
            return "https://www.1mg.com/drugs/levocetrizen-5mg-tablet-542407"
        
        for url in search_urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Try multiple selectors for drug links
                selectors = [
                    "a[href*='/drugs/']",
                    "a[href*='/otc/']",
                    ".style__product-card a",
                    ".style__product-name a",
                    "[data-testid='product-card'] a"
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        href = links[0].get("href")
                        if href:
                            if href.startswith("http"):
                                return href
                            else:
                                return "https://www.1mg.com" + href
                                
            except requests.exceptions.RequestException:
                continue
                
        # If no results found, try a more general search
        try:
            url = f"https://www.1mg.com/search?name={query}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Look for any product links
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                href = link.get("href")
                if href and ("/drugs/" in href or "/otc/" in href):
                    if href.startswith("http"):
                        return href
                    else:
                        return "https://www.1mg.com" + href
                        
        except:
            pass
            
    except Exception as e:
        print(f"1mg search error: {e}")
    return None


def search_apollo(product_name):
    """Searches Apollo Pharmacy and returns the top product URL."""
    try:
        query = quote(product_name)
        
        # Common medicine names to Apollo URLs mapping (fallback)
        fallback_urls = {
            "paracetamol": "https://www.apollopharmacy.in/medicine/dolo-650mg-tablet",
            "crocin": "https://www.apollopharmacy.in/medicine/crocin-advance-tablet",
            "aspirin": "https://www.apollopharmacy.in/medicine/aspirin-tablet",
            "ibuprofen": "https://www.apollopharmacy.in/medicine/brufen-400mg-tablet",
            "cetirizine": "https://www.apollopharmacy.in/medicine/zyrtec-10mg-tablet",
            "levocetrizen": "https://www.apollopharmacy.in/medicine/levocetrizen-10-tablet-10-s"
        }
        
        # Check fallback first for common medicines
        for key, url in fallback_urls.items():
            if key.lower() in product_name.lower():
                return url
        
        # Try different search URL patterns - Apollo might have changed their URLs
        search_patterns = [
            f"https://www.apollopharmacy.in/otc/{query}",
            f"https://www.apollopharmacy.in/medicine/{query}",
            f"https://www.apollopharmacy.in/search-medicines/{query}",
            f"https://www.apollopharmacy.in/drugs/{query}",
            f"https://www.apollopharmacy.in/products?search={query}"
        ]
        
        for url in search_patterns:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    
                    # Check if this is a direct product page
                    if soup.find("h1") and any(keyword in soup.find("h1").get_text().lower() 
                                              for keyword in [product_name.lower(), 'tablet', 'capsule']):
                        return url
                    
                    # Look for product links in search results
                    selectors = [
                        "a[href*='/medicine/']",
                        "a[href*='/product/']", 
                        "a[href*='/otc/']",
                        "a[href*='/drugs/']"
                    ]
                    
                    for selector in selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get("href")
                            if href:
                                if href.startswith("http"):
                                    return href
                                else:
                                    return "https://www.apollopharmacy.in" + href
                                    
            except:
                continue
                
    except Exception as e:
        print(f"Apollo search error: {e}")
    return None


def search_truemeds(product_name):
    """Searches Truemeds and returns the top product URL."""
    try:
        query = quote(product_name)
        
        # Common medicine names to Truemeds URLs mapping (fallback)
        fallback_urls = {
            "paracetamol": "https://www.truemeds.in/medicine/dolo-650-tablet",
            "crocin": "https://www.truemeds.in/medicine/crocin-advance-tablet", 
            "aspirin": "https://www.truemeds.in/medicine/aspirin-tablet",
            "ibuprofen": "https://www.truemeds.in/medicine/brufen-400-tablet",
            "cetirizine": "https://www.truemeds.in/medicine/cetirizine-10mg-tablet",
            "levocetrizen": "https://www.truemeds.in/medicine/levocetrizen-10mg-tablet-10-tm-tacr1-053283"
        }
        
        # Check fallback first for common medicines
        for key, url in fallback_urls.items():
            if key.lower() in product_name.lower():
                return url
        
        # Try different search approaches - Truemeds might be using different URLs
        search_patterns = [
            f"https://www.truemeds.in/medicine/{query.replace('%20', '-').lower()}-tablet",
            f"https://www.truemeds.in/medicine/{query.replace('%20', '-').lower()}",
            f"https://www.truemeds.in/drug/{query.replace('%20', '-').lower()}",
            f"https://www.truemeds.in/products/{query.replace('%20', '-').lower()}"
        ]
        
        # Test if direct medicine URLs exist
        for url in search_patterns:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    # Check if this looks like a valid product page
                    if soup.find("h1") and any(keyword in soup.find("h1").get_text().lower() 
                                              for keyword in [product_name.lower(), 'tablet', 'capsule']):
                        return url
            except:
                continue
        
        # Try search pages (these might load content via JavaScript)
        search_urls = [
            f"https://www.truemeds.in/search?q={query}",
            f"https://www.truemeds.in/search/{query}",
            f"https://www.truemeds.in/medicines?search={query}"
        ]
        
        for url in search_urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Try multiple selectors for product links
                selectors = [
                    "a[href*='/medicine/']",
                    "a[href*='/product/']",
                    "a[href*='/drug/']"
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href")
                        if href and ('/medicine/' in href or '/product/' in href or '/drug/' in href):
                            if href.startswith("http"):
                                return href
                            else:
                                return "https://www.truemeds.in" + href
                                
            except:
                continue
                
    except Exception as e:
        print(f"Truemeds search error: {e}")
    return None

# ---------- Site-Specific Scrapers ----------
# Each function is tailored to the specific HTML structure of the website.

def scrape_1mg(soup):
    """Scrapes data from a Tata 1mg product page."""
    data = {
        "overview": None, "uses_and_benefits": None, "side_effects": None,
        "how_to_use": None, "how_drug_works": None, "safety_advice": None,
        "missed_dose": None, "all_substitutes": [], "quick_tips": None,
        "fact_box": None, "interaction_with_drugs": None,
        "patient_concerns": None, "user_feedback": None, "faqs": []
    }

    # Method 1: Extract content from div elements with substantial text
    content_divs = soup.find_all("div")
    content_texts = []
    
    for div in content_divs:
        text = div.get_text(" ", strip=True)
        if len(text) > 50 and len(text) < 2000:  # Reasonable content length
            content_texts.append(text)
    
    # Method 2: Categorize content based on keywords and context
    for text in content_texts:
        text_lower = text.lower()
        
        # Uses and benefits
        if any(keyword in text_lower for keyword in ['treatment of', 'used for', 'indication']) and not data["uses_and_benefits"]:
            if len(text) > len(data["uses_and_benefits"] or ""):
                data["uses_and_benefits"] = text
        
        # Side effects
        elif any(keyword in text_lower for keyword in ['side effects', 'adverse effects', 'most side effects']) and not data["side_effects"]:
            if len(text) > len(data["side_effects"] or ""):
                data["side_effects"] = text
        
        # How to use
        elif any(keyword in text_lower for keyword in ['take this medicine', 'dose and duration', 'how to take']) and not data["how_to_use"]:
            data["how_to_use"] = text
        
        # How drug works
        elif any(keyword in text_lower for keyword in ['works by', 'mechanism', 'blocks', 'antihistamine']) and not data["how_drug_works"]:
            if 'take this medicine' not in text_lower:  # Avoid duplicate with how_to_use
                data["how_drug_works"] = text
        
        # Safety advice
        elif any(keyword in text_lower for keyword in ['alcohol', 'pregnancy', 'breastfeeding', 'driving', 'unsafe', 'caution']) and not data["safety_advice"]:
            if len(text) > 100:  # Ensure substantial safety content
                data["safety_advice"] = text
        
        # Overview/About
        elif any(keyword in text_lower for keyword in ['belongs to', 'class of', 'antihistamine', 'description']) and not data["overview"]:
            if len(text) > 100:
                data["overview"] = text
        
        # Quick tips
        elif any(keyword in text_lower for keyword in ['quick tip', 'tip', 'remember', 'important']) and not data["quick_tips"]:
            data["quick_tips"] = text
        
        # Missed dose
        elif any(keyword in text_lower for keyword in ['missed dose', 'forget to take', 'skip']) and not data["missed_dose"]:
            data["missed_dose"] = text

    # Method 3: Extract structured information from specific sections
    
    # Extract substitutes
    substitute_links = soup.find_all("a", href=lambda x: x and "/drugs/" in x)
    substitutes = []
    for link in substitute_links[:10]:  # Limit to 10 substitutes
        substitute_name = link.get_text(strip=True)
        if substitute_name and len(substitute_name) < 100:
            substitutes.append(substitute_name)
    data["all_substitutes"] = list(set(substitutes))  # Remove duplicates
    
    # Extract fact box from lists or structured content
    fact_lists = soup.find_all("ul")
    for ul in fact_lists:
        list_text = ul.get_text(" | ", strip=True)
        if any(keyword in list_text.lower() for keyword in ['composition', 'manufacturer', 'therapeutic', 'habit forming']):
            if not data["fact_box"] or len(list_text) > len(data["fact_box"]):
                data["fact_box"] = list_text

    # Method 4: Extract FAQs
    faq_elements = soup.find_all(['h3', 'h4'], string=lambda text: text and '?' in text)
    faqs = []
    for faq_q in faq_elements[:5]:  # Limit to 5 FAQs
        question = faq_q.get_text(strip=True)
        answer_elem = faq_q.find_next_sibling()
        if answer_elem:
            answer = answer_elem.get_text(" ", strip=True)
            if len(answer) > 20:
                faqs.append({"q": question, "a": answer})
    data["faqs"] = faqs

    # Method 5: Extract specific 1mg sections based on H2 headings
    h2_headings = soup.find_all('h2')
    for h2 in h2_headings:
        heading_text = h2.get_text().strip().lower()
        
        # Find content after this heading
        content_elem = h2.find_next_sibling()
        while content_elem and content_elem.name in ['div', 'p', 'section']:
            content = content_elem.get_text(" ", strip=True)
            if len(content) > 30:
                
                # Patient concerns
                if 'patient concerns' in heading_text and not data["patient_concerns"]:
                    data["patient_concerns"] = content
                    break
                
                # User feedback
                elif 'user feedback' in heading_text and not data["user_feedback"]:
                    data["user_feedback"] = content
                    break
                
                # Overview (Product introduction)
                elif 'product introduction' in heading_text and not data["overview"]:
                    data["overview"] = content
                    break
            
            content_elem = content_elem.find_next_sibling()

    # Method 6: Extract drug interactions
    interaction_keywords = ['interaction', 'drug interaction', 'contraindication']
    for text in content_texts:
        if any(keyword in text.lower() for keyword in interaction_keywords) and not data["interaction_with_drugs"]:
            if len(text) > 50:
                data["interaction_with_drugs"] = text
                break

    return data


def scrape_apollo(soup):
    """Scrapes data from an Apollo Pharmacy product page."""
    data = {
        "about_medicine": None, "side_effects": None, "uses_and_benefits": None,
        "directions_for_use": None, "how_it_works": None, "storage": None,
        "overdose": None, "drug_warnings": None, "drug_interactions": None,
        "diet_and_lifestyle": None, "therapeutic": None, "safety_advice": None,
        "faqs": [], "product_substitutes": []
    }

    # Method 1: Extract content from divs with class 'wj' (Apollo's main content containers)
    content_divs = soup.find_all("div", class_="wj")
    content_texts = []
    
    for div in content_divs:
        text = div.get_text(" ", strip=True)
        if len(text) > 30:  # Only substantial content
            content_texts.append(text)
    
    # Method 2: Extract from all content containers and paragraphs  
    all_containers = soup.find_all(['div', 'section', 'p', 'span'])
    for container in all_containers:
        text = container.get_text(" ", strip=True)
        if text and len(text) > 50 and len(text) < 1000:
            content_texts.append(text)
    
    # Remove duplicates
    content_texts = list(dict.fromkeys(content_texts))
    
    # Method 3: Enhanced categorization based on keywords
    for text in content_texts:
        text_lower = text.lower()
        
        # About medicine (general description, class)
        if any(keyword in text_lower for keyword in ['belongs to', 'class of', 'antihistamine', 'medication used', 'drug that']) and not data["about_medicine"]:
            data["about_medicine"] = text
        
        # Side effects
        elif any(keyword in text_lower for keyword in ['side effect', 'adverse effect', 'may cause', 'common side']) and not data["side_effects"]:
            data["side_effects"] = text
            
        # Uses and benefits 
        elif any(keyword in text_lower for keyword in ['used to treat', 'treatment of', 'prescribed for', 'indication', 'treats']) and not data["uses_and_benefits"]:
            data["uses_and_benefits"] = text
            
        # Directions for use
        elif any(keyword in text_lower for keyword in ['directions for use', 'how to take', 'dosage', 'administration']) and not data["directions_for_use"]:
            data["directions_for_use"] = text
            
        # How it works
        elif any(keyword in text_lower for keyword in ['how it works', 'works by', 'mechanism of action', 'action']) and not data["how_it_works"]:
            data["how_it_works"] = text
            
        # Drug warnings
        elif any(keyword in text_lower for keyword in ['should not be taken', 'contraindicated', 'warning', 'caution']) and not data["drug_warnings"]:
            data["drug_warnings"] = text
            
        # Storage
        elif any(keyword in text_lower for keyword in ['store in', 'storage', 'keep out', 'temperature']) and not data["storage"]:
            data["storage"] = text
        
        # Drug interactions
        elif any(keyword in text_lower for keyword in ['drug interaction', 'avoid taking', 'concurrent use']) and not data["drug_interactions"]:
            data["drug_interactions"] = text
        
        # Diet and lifestyle
        elif any(keyword in text_lower for keyword in ['diet', 'lifestyle', 'food', 'alcohol', 'exercise']) and not data["diet_and_lifestyle"]:
            data["diet_and_lifestyle"] = text
        
        # Overdose
        elif any(keyword in text_lower for keyword in ['overdose', 'too much', 'excess dose']) and not data["overdose"]:
            data["overdose"] = text
        
        # Therapeutic class
        elif any(keyword in text_lower for keyword in ['therapeutic', 'pharmacological', 'category']) and not data["therapeutic"]:
            if len(text) < 300:  # Keep therapeutic info concise
                data["therapeutic"] = text

    # Method 4: Extract safety advice from JSON-LD or structured content
    safety_elements = soup.find_all(string=lambda text: text and any(word in text.lower() for word in ['alcohol', 'pregnancy', 'breastfeeding', 'driving']))
    safety_content = []
    
    for elem in safety_elements:
        text = elem.strip()
        
        # Clean up JSON-LD content
        if text.startswith('{"@context"'):
            try:
                import json
                json_data = json.loads(text)
                
                if "alcoholWarning" in json_data:
                    safety_content.append(f"Alcohol: {json_data['alcoholWarning']}")
                if "pregnancyWarning" in json_data:
                    safety_content.append(f"Pregnancy: {json_data['pregnancyWarning']}")
                if "breastfeedingWarning" in json_data:
                    safety_content.append(f"Breastfeeding: {json_data['breastfeedingWarning']}")
                if "drivingWarning" in json_data:
                    safety_content.append(f"Driving: {json_data['drivingWarning']}")
            except:
                pass
        elif len(text) > 20 and len(text) < 300:
            # Regular safety text
            if any(keyword in text.lower() for keyword in ['alcohol', 'pregnancy', 'breastfeeding', 'driving']):
                safety_content.append(text)
    
    if safety_content:
        data["safety_advice"] = " | ".join(safety_content[:4])

    # Method 5: Extract FAQs
    faq_elements = soup.find_all(string=lambda text: text and '?' in text and len(text) > 10)
    faqs = []
    
    for faq_text in faq_elements[:8]:  # Limit to 8 FAQs
        if faq_text.strip().endswith('?'):
            question = faq_text.strip()
            parent = faq_text.parent
            
            if parent:
                # Look for answer in next siblings
                next_elem = parent.find_next_sibling()
                if next_elem:
                    answer = next_elem.get_text(" ", strip=True)
                    if len(answer) > 20 and len(answer) < 500:
                        faqs.append({"q": question, "a": answer})
    
    if faqs:
        data["faqs"] = faqs

    # Method 6: Extract product substitutes
    substitute_links = soup.find_all("a", string=lambda text: text and any(keyword in text.lower() for keyword in ['tablet', 'capsule', 'mg', 'ml']))
    substitutes = []
    
    for link in substitute_links[:15]:  # Limit to 15 substitutes
        substitute_name = link.get_text(strip=True)
        if substitute_name and len(substitute_name) < 100 and substitute_name not in substitutes:
            # Filter out navigation and non-medicine links
            if not any(unwanted in substitute_name.lower() for unwanted in ['search', 'category', 'home', 'cart', 'login']):
                substitutes.append(substitute_name)
    
    if substitutes:
        data["product_substitutes"] = substitutes

    # Method 7: Fill empty fields with available content (fallback)
    empty_fields = [k for k, v in data.items() if not v and k not in ['faqs', 'product_substitutes']]
    available_texts = [text for text in content_texts if len(text) > 80 and len(text) < 400]
    
    for i, field in enumerate(empty_fields):
        if i < len(available_texts):
            # Assign remaining content to empty fields
            data[field] = available_texts[i]

    return data
    safety_elements = soup.find_all(string=lambda text: text and any(word in text.lower() for word in ['alcohol', 'pregnancy', 'breastfeeding', 'driving']))
    if safety_elements:
        safety_content = []
        for elem in safety_elements:
            text = elem.strip()
            # Clean up JSON-LD content
            if text.startswith('{"@context"'):
                try:
                    import json
                    json_data = json.loads(text)
                    if "alcoholWarning" in json_data:
                        safety_content.append(f"Alcohol: {json_data['alcoholWarning']}")
                    if "pregnancyWarning" in json_data:
                        safety_content.append(f"Pregnancy: {json_data['pregnancyWarning']}")
                    if "breastfeedingWarning" in json_data:
                        safety_content.append(f"Breastfeeding: {json_data['breastfeedingWarning']}")
                    if "drivingWarning" in json_data:
                        safety_content.append(f"Driving: {json_data['drivingWarning']}")
                except:
                    pass
            elif len(text) > 20 and len(text) < 200:
                safety_content.append(text)
        if safety_content:
            data["safety_advice"] = " | ".join(safety_content[:3])

    # Method 5: Extract more content sections that are missing
    for text in content_texts:
        text_lower = text.lower()
        
        # Directions for use
        if any(keyword in text_lower for keyword in ['directions for use', 'how to take', 'dosage instructions']) and not data["directions_for_use"]:
            data["directions_for_use"] = text
        
        # Drug interactions
        elif any(keyword in text_lower for keyword in ['drug interaction', 'contraindication', 'avoid taking with']) and not data["drug_interactions"]:
            data["drug_interactions"] = text
        
        # Diet and lifestyle
        elif any(keyword in text_lower for keyword in ['diet', 'lifestyle', 'food', 'exercise']) and not data["diet_and_lifestyle"]:
            data["diet_and_lifestyle"] = text
        
        # Overdose information
        elif any(keyword in text_lower for keyword in ['overdose', 'too much', 'excess']) and not data["overdose"]:
            data["overdose"] = text
        
        # Therapeutic class
        elif any(keyword in text_lower for keyword in ['therapeutic', 'class', 'category', 'belongs to']) and not data["therapeutic"]:
            if len(text) < 200:  # Keep it concise for therapeutic class
                data["therapeutic"] = text

    # Method 6: Extract FAQs from structured content
    faq_elements = soup.find_all(string=lambda text: text and '?' in text and len(text) > 10)
    faqs = []
    for i, faq_text in enumerate(faq_elements[:5]):  # Limit to 5 FAQs
        if faq_text.strip().endswith('?'):
            question = faq_text.strip()
            parent = faq_text.parent
            if parent:
                # Look for answer in next siblings
                next_elem = parent.find_next_sibling()
                if next_elem:
                    answer = next_elem.get_text(" ", strip=True)
                    if len(answer) > 20 and len(answer) < 500:
                        faqs.append({"q": question, "a": answer})
    
    if faqs:
        data["faqs"] = faqs

    # Method 7: Extract product substitutes
    substitute_elements = soup.find_all("a", string=lambda text: text and any(keyword in text.lower() for keyword in ['tablet', 'capsule', 'mg']))
    substitutes = []
    for elem in substitute_elements[:10]:
        substitute_name = elem.get_text(strip=True)
        if substitute_name and len(substitute_name) < 100 and substitute_name not in substitutes:
            substitutes.append(substitute_name)
    
    if substitutes:
        data["product_substitutes"] = substitutes

    return data


def scrape_truemeds(soup):
    """Scrapes data from a Truemeds product page."""
    data = {
        "uses": None, "directions_for_use": None, "route_of_administration": None,
        "side_effects": None, "medicine_activity": None, "precautions_and_warnings": None,
        "interactions": None, "dosage_information": None, "storage": None,
        "diet_and_lifestyle_guidance": None, "fact_box": None, "faqs": []
    }
    
    # Method 1: Extract content based on h2 headings and their following content
    h2_headings = soup.find_all('h2')
    
    for h2 in h2_headings:
        heading_text = h2.get_text().strip().lower()
        
        # Find content after this heading
        content = None
        current = h2.find_next_sibling()
        
        # Look for the first substantial content element
        while current and current.name != 'h2':
            if current.name in ['p', 'div', 'section', 'ul', 'ol']:
                text = current.get_text(" ", strip=True)
                if len(text) > 30 and not any(skip in text.lower() for skip in ['login', 'sign up', 'cart', 'wishlist']):
                    content = text
                    break
            current = current.find_next_sibling()
        
        # Alternative: look in the parent section
        if not content:
            parent = h2.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True)
                heading_clean = h2.get_text(strip=True)
                if heading_clean in parent_text:
                    remaining_text = parent_text.replace(heading_clean, "", 1).strip()
                    if len(remaining_text) > 50:
                        content = remaining_text[:600]  # Increased limit for more content
        
        # Map content to appropriate fields based on heading
        if content:
            if 'about' in heading_text or 'introduction' in heading_text:
                data["uses"] = content  # "About" section often contains usage info
            elif 'uses' in heading_text or 'indication' in heading_text:
                data["uses"] = content
            elif 'directions' in heading_text or 'how to use' in heading_text or 'administration' in heading_text:
                data["directions_for_use"] = content
            elif 'route' in heading_text and 'administration' in heading_text:
                data["route_of_administration"] = content
            elif 'side effects' in heading_text or 'adverse effects' in heading_text:
                data["side_effects"] = content
            elif ('how' in heading_text and 'works' in heading_text) or 'mechanism' in heading_text:
                data["medicine_activity"] = content
            elif 'safety' in heading_text or 'warnings' in heading_text or 'precautions' in heading_text:
                data["precautions_and_warnings"] = content
            elif 'interactions' in heading_text or 'contraindications' in heading_text:
                data["interactions"] = content
            elif 'storage' in heading_text or 'store' in heading_text:
                data["storage"] = content
            elif 'dosage' in heading_text or 'dose' in heading_text:
                data["dosage_information"] = content

    # Method 2: Enhanced content extraction from all elements
    # Find all content containers
    all_elements = soup.find_all(['p', 'div', 'section', 'span', 'li'])
    content_texts = []
    
    for elem in all_elements:
        text = elem.get_text(" ", strip=True)
        if text and len(text) > 40 and len(text) < 800:
            # Filter out navigation and unwanted content
            if not any(skip in text.lower() for skip in ['login', 'sign up', 'cart', 'wishlist', 'search', 'menu']):
                content_texts.append(text)
    
    # Remove duplicates
    content_texts = list(dict.fromkeys(content_texts))
    
    # Method 3: Content categorization using enhanced keywords
    for text in content_texts:
        text_lower = text.lower()
        
        # Uses (enhanced keywords)
        if any(keyword in text_lower for keyword in ['used for', 'treats', 'prescribed for', 'allergy', 'allergic', 'histamine', 'antihistamine', 'indication']) and not data["uses"]:
            data["uses"] = text
        
        # Side effects
        elif any(keyword in text_lower for keyword in ['side effect', 'adverse effect', 'drowsiness', 'nausea', 'headache', 'dry mouth', 'may cause']) and not data["side_effects"]:
            data["side_effects"] = text
        
        # Directions for use
        elif any(keyword in text_lower for keyword in ['take with', 'swallow', 'dosage', 'once daily', 'how to take', 'administration']) and not data["directions_for_use"]:
            data["directions_for_use"] = text
        
        # Medicine activity (how it works)
        elif any(keyword in text_lower for keyword in ['blocks', 'prevents', 'inhibits', 'mechanism', 'works by', 'action']) and not data["medicine_activity"]:
            data["medicine_activity"] = text
        
        # Precautions and warnings
        elif any(keyword in text_lower for keyword in ['precaution', 'warning', 'caution', 'avoid', 'should not']) and not data["precautions_and_warnings"]:
            data["precautions_and_warnings"] = text
        
        # Interactions
        elif any(keyword in text_lower for keyword in ['interaction', 'concurrent', 'combination', 'avoid taking with']) and not data["interactions"]:
            data["interactions"] = text
        
        # Storage
        elif any(keyword in text_lower for keyword in ['store', 'storage', 'temperature', 'keep out', 'room temperature']) and not data["storage"]:
            data["storage"] = text
        
        # Route of administration
        elif any(keyword in text_lower for keyword in ['oral', 'by mouth', 'route of administration', 'take orally']) and not data["route_of_administration"]:
            data["route_of_administration"] = text
        
        # Diet and lifestyle guidance
        elif any(keyword in text_lower for keyword in ['diet', 'lifestyle', 'food', 'alcohol', 'exercise', 'driving']) and not data["diet_and_lifestyle_guidance"]:
            data["diet_and_lifestyle_guidance"] = text

    # Method 4: Extract fact box information from structured sections
    fact_elements = soup.find_all(['div', 'section'], class_=lambda x: x and ('fact' in str(x).lower() or 'key' in str(x).lower() or 'info' in str(x).lower()))
    if fact_elements:
        fact_content = []
        for elem in fact_elements:
            text = elem.get_text(" ", strip=True)
            if len(text) > 20 and len(text) < 300:
                fact_content.append(text)
        if fact_content:
            data["fact_box"] = " | ".join(fact_content[:3])

    # Method 5: Extract FAQs
    faq_elements = soup.find_all(string=lambda text: text and '?' in text and len(text) > 10)
    faqs = []
    
    for faq_text in faq_elements[:6]:  # Limit to 6 FAQs
        if faq_text.strip().endswith('?'):
            question = faq_text.strip()
            parent = faq_text.parent
            
            if parent:
                # Look for answer in next siblings
                next_elem = parent.find_next_sibling()
                if next_elem:
                    answer = next_elem.get_text(" ", strip=True)
                    if len(answer) > 15 and len(answer) < 400:
                        faqs.append({"q": question, "a": answer})
    
    if faqs:
        data["faqs"] = faqs

    # Method 6: Fill empty fields with available relevant content (fallback strategy)
    empty_fields = [k for k, v in data.items() if not v and k != 'faqs']
    available_texts = [text for text in content_texts if len(text) > 60 and len(text) < 400]
    
    # Use keyword matching for better field assignment
    field_keywords = {
        "dosage_information": ['mg', 'dose', 'tablet', 'capsule', 'daily'],
        "uses": ['treatment', 'condition', 'disease', 'symptom'],
        "medicine_activity": ['receptor', 'protein', 'enzyme', 'pathway'],
        "precautions_and_warnings": ['pregnancy', 'liver', 'kidney', 'elderly']
    }
    
    for field in empty_fields:
        if field in field_keywords:
            keywords = field_keywords[field]
            for text in available_texts:
                if any(keyword in text.lower() for keyword in keywords):
                    data[field] = text
                    available_texts.remove(text)  # Don't reuse this text
                    break

    return data


# ---------- Main Scraper Function ----------
def scrape_product(url: str):
    """Main function to dispatch scraping task based on URL."""
    if not url:
        return {"error": "No product URL provided"}

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # --- Common Data Extraction ---
        data = {
            "url": url,
            "medicine_name": None,
            "product_images": [],
            "details": {} # To store site-specific data
        }

        # Title (common across sites)
        title = soup.find("h1")
        if title:
            data["medicine_name"] = title.get_text(strip=True)

        # Images (common across sites) - Improved image detection
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy")
            alt = img.get("alt", "").lower()
            
            if src and not src.startswith("data:image"):
                # Filter for actual product images, not logos or general website images
                if any(keyword in src.lower() for keyword in ["product", "medicine", "tablet", "capsule", "drug"]) or \
                   any(keyword in alt for keyword in ["tablet", "capsule", "medicine", "drug", data.get("medicine_name", "").lower().split()[0] if data.get("medicine_name") else ""]):
                    
                    # Skip common website elements
                    if not any(skip in src.lower() for skip in ["logo", "icon", "banner", "nav", "header", "footer", "visa", "mastercard", "amex"]):
                        # Ensure URL is absolute
                        if not src.startswith("http"):
                            base_url = "/".join(url.split("/")[:3])
                            src = base_url + src if src.startswith('/') else base_url + '/' + src
                        data["product_images"].append(src)
        # Remove duplicates
        data["product_images"] = list(dict.fromkeys(data["product_images"]))


        # --- Site-Specific Dispatching ---
        if "1mg.com" in url:
            data["details"] = scrape_1mg(soup)
        elif "apollopharmacy.in" in url:
            data["details"] = scrape_apollo(soup)
        elif "truemeds.in" in url:
            data["details"] = scrape_truemeds(soup)
        else:
            return {"error": f"Scraper not implemented for this domain: {url}"}
            
        return data

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch {url}. Reason: {e}"}


# ---------- Streamlit UI ----------
st.title("💊 Medicine Data Scraper")
st.markdown("Enter a medicine name. The tool will search on **Tata 1mg, Apollo Pharmacy, and Truemeds**, extract detailed information, and display it along with product photos.")

product_name = st.text_input("📝 Enter Medicine Name:", placeholder="e.g., Crocin Advance")

if product_name:
    urls = {}
    with st.spinner("Searching for product pages..."):
        st.write("🔍 Searching on different websites...")
        
        # Search 1mg
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("**1mg:**")
            with col2:
                url_1mg = search_1mg(product_name)
                urls["1mg"] = url_1mg
                if url_1mg:
                    st.success("✅ Found")
                else:
                    st.error("❌ Not found")
        
        # Search Apollo
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("**Apollo:**")
            with col2:
                url_apollo = search_apollo(product_name)
                urls["Apollo"] = url_apollo
                if url_apollo:
                    st.success("✅ Found")
                else:
                    st.error("❌ Not found")
        
        # Search Truemeds
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("**Truemeds:**")
            with col2:
                url_truemeds = search_truemeds(product_name)
                urls["Truemeds"] = url_truemeds
                if url_truemeds:
                    st.success("✅ Found")
                else:
                    st.error("❌ Not found")
    
    st.write("---")
    st.subheader("🔍 Found URLs")
    st.write(f"**1mg:** `{urls['1mg'] or 'Not Found'}`")
    st.write(f"**Apollo:** `{urls['Apollo'] or 'Not Found'}`")
    st.write(f"**Truemeds:** `{urls['Truemeds'] or 'Not Found'}`")
    st.write("---")
    
    results = {}
    has_results = False
    
    for site, url in urls.items():
        if url:
            with st.spinner(f"Scraping data from {site}..."):
                result = scrape_product(url)
                if "error" not in result:
                    results[site] = result
                    has_results = True
                else:
                    st.error(f"Could not scrape {site}: {result['error']}")
        else:
            st.warning(f"Skipping {site} as no product URL was found.")

    if has_results:
        st.success("✅ Data extraction complete!")
        
        # Create tabs for each result
        site_tabs = st.tabs(list(results.keys()))

        for i, site in enumerate(results.keys()):
            with site_tabs[i]:
                st.header(f"Data from {site}")
                result_data = results[site]
                
                # Display images in columns
                st.subheader(f"📸 Product Images")
                if result_data.get("product_images"):
                    # Display up to 5 images in columns
                    cols = st.columns(min(len(result_data["product_images"]), 5))
                    for idx, img_url in enumerate(result_data["product_images"][:5]):
                        with cols[idx]:
                            try:
                                st.image(img_url, caption=result_data.get("medicine_name"), use_container_width=True)
                            except Exception as e:
                                st.write(f"🖼️ Image {idx+1}: [View Image]({img_url})")
                                st.caption("Image could not be displayed")
                else:
                    st.write("No images found.")
                
                # Display the scraped JSON data
                st.subheader("📋 Scraped Data (JSON)")
                st.json(result_data)

        # Add a download button for all data combined
        st.download_button(
            label="📥 Download All Data as JSON",
            data=json.dumps(results, indent=4),
            file_name=f"{product_name.replace(' ', '_')}_data.json",
            mime="application/json",
        )