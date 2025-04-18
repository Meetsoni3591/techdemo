from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os
from dotenv import load_dotenv
import random
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

def extract_emails_from_website(url):
    """Extract all emails from a company website"""
    print(f"\n🌐 Processing website: {url}")
    emails_found = set()
    try:
        # Add headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # First try the main page
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract emails from main page
        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        emails_found.update(emails)
        print(f"📧 Found {len(emails)} emails on main page")
        
        # Try to find and process all contact-related pages
        contact_links = soup.find_all('a', href=lambda href: href and any(term in href.lower() for term in ['contact', 'about', 'team', 'connect']))
        
        for link in contact_links:
            try:
                contact_url = urljoin(url, link['href'])
                print(f"🔗 Processing page: {contact_url}")
                
                contact_resp = requests.get(contact_url, timeout=10, headers=headers)
                contact_resp.raise_for_status()
                contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                
                # Extract emails from contact page
                contact_text = contact_soup.get_text()
                contact_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", contact_text)
                emails_found.update(contact_emails)
                print(f"📧 Found {len(contact_emails)} additional emails on this page")
                
                # Also check for email links
                email_links = contact_soup.find_all('a', href=lambda href: href and 'mailto:' in href.lower())
                for email_link in email_links:
                    email = email_link['href'].replace('mailto:', '').strip()
                    if email:
                        emails_found.add(email)
                
            except Exception as e:
                print(f"⚠️ Error processing page {contact_url}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
    
    # Filter out common non-email patterns
    filtered_emails = set()
    for email in emails_found:
        # Skip common false positives
        if not any(term in email.lower() for term in ['example.com', 'domain.com', 'your-email']):
            filtered_emails.add(email)
    
    print(f"✅ Total unique emails found: {len(filtered_emails)}")
    return list(filtered_emails)

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    
    # Basic options
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Anti-detection options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # GPU and WebGL options
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-webgl2')
    
    # User agent and other headers
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional JavaScript to prevent detection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def login_to_linkedin(driver):
    """Login to LinkedIn using credentials from .env file"""
    try:
        # Get credentials from .env file
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not email or not password:
            raise ValueError("LinkedIn credentials not found in .env file")
        
        # Navigate to LinkedIn login page
        driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(2, 4))
        
        # Enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_field.send_keys(email)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Enter password
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for login to complete
        time.sleep(random.uniform(10, 15))
        return True
        
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return False

def search_companies(driver, search_query):
    """Search for companies on LinkedIn and extract companies until finding at least 10 with emails"""
    try:
        companies = []
        page = 1
        max_pages = 5  # Maximum number of pages to search
        
        while len([c for c in companies if c['Emails'] != 'No emails found']) < 10 and page <= max_pages:
            print(f"\n📄 Processing page {page} of search results...")
            
            # Navigate to search page
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={search_query}&page={page}"
            driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            # Wait for search results to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results-container"))
            )
            
            # Scroll to load more results
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
            
            # Extract company information
            company_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-chameleon-result-urn]")
            
            for element in company_elements:
                try:
                    # Extract company name
                    name_element = element.find_element(By.CSS_SELECTOR, "span.t-16 a")
                    company_name = name_element.text.strip()
                    
                    # Extract website URL
                    try:
                        website_element = element.find_element(By.CSS_SELECTOR, "a[data-test-app-aware-link]")
                        website_url = website_element.get_attribute('href')
                    except:
                        website_url = None
                    
                    # Extract industry and location
                    try:
                        industry_element = element.find_element(By.CSS_SELECTOR, "div.t-14.t-black.t-normal")
                        industry_text = industry_element.text.strip()
                        parts = industry_text.split("•")
                        industry = parts[0].strip() if parts else "Not specified"
                        location = parts[1].strip() if len(parts) > 1 else "Not specified"
                    except:
                        industry = "Not specified"
                        location = "Not specified"
                    
                    # Extract followers count
                    try:
                        followers_element = element.find_element(By.CSS_SELECTOR, "div.t-14.t-normal")
                        followers = followers_element.text.strip()
                    except:
                        followers = "Not specified"
                    
                    # Extract description
                    try:
                        desc_element = element.find_element(By.CSS_SELECTOR, "p.entity-result__summary--2-lines")
                        description = desc_element.text.strip()
                    except:
                        description = "Not specified"
                    
                    # Extract emails if website URL is available
                    emails = []
                    if website_url:
                        print(f"\n🔍 Extracting emails for: {company_name}")
                        emails = extract_emails_from_website(website_url)
                        if emails:
                            print(f"📧 Found {len(emails)} emails for {company_name}:")
                            for email in emails:
                                print(f"   - {email}")
                    
                    companies.append({
                        'Company Name': company_name,
                        'Website': website_url,
                        'Industry': industry,
                        'Location': location,
                        'Followers': followers,
                        'Description': description,
                        'Emails': '; '.join(emails) if emails else 'No emails found'
                    })
                    
                    # Check if we have enough companies with emails
                    companies_with_emails = [c for c in companies if c['Emails'] != 'No emails found']
                    if len(companies_with_emails) >= 10:
                        print(f"\n✅ Found {len(companies_with_emails)} companies with email addresses")
                        return companies
                    
                except Exception as e:
                    print(f"Error extracting company data: {str(e)}")
                    continue
            
            page += 1
            time.sleep(random.uniform(2, 3))  # Wait before loading next page
        
        return companies
        
    except Exception as e:
        print(f"Error during company search: {str(e)}")
        return []

def main():
    # Setup Chrome driver
    driver = setup_driver()
    
    try:
        # Login to LinkedIn
        if not login_to_linkedin(driver):
            print("Failed to login to LinkedIn")
            return
        
        # Search for companies
        search_query = "mobile app development companies in India"
        print(f"Searching for: {search_query}")
        
        companies = search_companies(driver, search_query)
        
        if companies:
            # Filter companies to only include those with emails
            companies_with_emails = [company for company in companies if company['Emails'] != 'No emails found']
            
            if companies_with_emails:
                # Create DataFrame and save to CSV
                df = pd.DataFrame(companies_with_emails)
                df.to_csv('linkedin_companies_with_emails.csv', index=False)
                
                # Print results in a nice format
                print("\nCompanies with Email Addresses:")
                print("-" * 100)
                for idx, company in enumerate(companies_with_emails, 1):
                    print(f"{idx}. {company['Company Name']}")
                    print(f"   Industry: {company['Industry']}")
                    print(f"   Location: {company['Location']}")
                    print(f"   Website: {company['Website']}")
                    print(f"   Emails: {company['Emails']}")
                    print("-" * 100)
                
                print(f"\n✅ Found {len(companies_with_emails)} companies with email addresses")
                print(f"📊 Results saved to linkedin_companies_with_emails.csv")
            else:
                print("\n❌ No companies with email addresses found")
        else:
            print("No companies found")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main() 