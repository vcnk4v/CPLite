#!/usr/bin/env python3
"""
Profile-based Token Collector for CPLite Load Testing

This script uses your existing Chrome profile (already logged in to Google)
to collect authentication tokens for load testing with Locust.

Requirements:
- Python 3.6+
- selenium
- webdriver_manager

Usage:
  python profile_token_collector.py --count 5 --base-url http://localhost:8000
"""

import argparse
import csv
import json
import time
import os
import platform
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Output file
OUTPUT_FILE = "auth_tokens.csv"

def get_default_chrome_profile_path():
    """Get the default Chrome profile path based on the OS"""
    system = platform.system()
    home = str(Path.home())
    
    if system == "Windows":
        return os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Library", "Application Support", "Google", "Chrome")
    elif system == "Linux":
        return os.path.join(home, ".config", "google-chrome")
    else:
        return None

def setup_driver(profile_path=None):
    """Setup Chrome driver with user profile"""
    chrome_options = Options()
    
    # Use the provided profile path or get the default one
    if not profile_path:
        profile_path = get_default_chrome_profile_path()
    
    if profile_path:
        print(f"[*] Using Chrome profile at: {profile_path}")
        chrome_options.add_argument(f"user-data-dir={profile_path}")
    else:
        print("[!] Warning: No Chrome profile specified. Login may be blocked.")
    
    # Add other necessary options
    chrome_options.add_argument("--window-size=1300,1000")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Enable logging
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    # Create a new driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def get_auth_url(base_url, role="learner"):
    """Get the authentication URL"""
    # Adjust this URL to match your application's OAuth entry point
    return f"{base_url}/login?preferred_role={role}"

def extract_tokens_from_network(driver, timeout=30):
    """Extract tokens from network traffic"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check network requests
            logs = driver.get_log('performance')
            for log in logs:
                try:
                    log_entry = json.loads(log["message"])["message"]
                    
                    if "Network.responseReceived" == log_entry["method"]:
                        req_url = log_entry["params"]["response"]["url"]
                        if "/api/auth/google" in req_url or "/api/auth/login" in req_url or "/api/auth/token" in req_url:
                            print(f"[+] Found potential auth response: {req_url}")
                            request_id = log_entry["params"]["requestId"]
                            try:
                                response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                resp_body = json.loads(response['body'])
                                if 'access_token' in resp_body and 'refresh_token' in resp_body:
                                    return {
                                        'access_token': resp_body['access_token'],
                                        'refresh_token': resp_body['refresh_token'],
                                        'user_id': str(resp_body.get('user_id', '')),
                                        'role': resp_body.get('role', '')
                                    }
                            except Exception as e:
                                print(f"[-] Error parsing response: {str(e)}")
                except:
                    continue
        except Exception as e:
            print(f"[-] Error checking logs: {str(e)}")
        
        # Try to extract token from localStorage as backup method
        try:
            token_data = driver.execute_script("""
                return {
                    access_token: localStorage.getItem('access_token'),
                    refresh_token: localStorage.getItem('refresh_token'),
                    user_id: localStorage.getItem('user_id'),
                    role: localStorage.getItem('user_role')
                };
            """)
            
            if token_data['access_token']:
                return token_data
        except:
            pass
            
        # Wait before checking again
        time.sleep(2)
    
    return None

def collect_token(driver, base_url, role):
    """Collect a token by navigating to the auth URL"""
    auth_url = get_auth_url(base_url, role)
    print(f"[*] Navigating to: {auth_url}")
    driver.get(auth_url)
    
    print(f"[*] Collecting token for role: {role}")
    print("[*] Because we're using your Chrome profile, you should already be logged into Google")
    print("[*] If prompted, please click to authorize the application")
    
    # Wait for OAuth flow to complete and redirect
    print("[*] Waiting for OAuth flow to complete...")
    wait_time = 30
    for i in range(wait_time):
        time.sleep(1)
        print(f"[*] Waiting... {i+1}/{wait_time} seconds", end="\r")
        
        # Check if we're redirected to the app
        current_url = driver.current_url
        if base_url in current_url and "/login" not in current_url:
            print("\n[+] Redirected to app, authentication flow complete!")
            break
    
    # Extract tokens from network traffic
    print("[*] Attempting to capture authentication tokens...")
    tokens = extract_tokens_from_network(driver)
    
    # Manual input as last resort
    if not tokens:
        print("\n[-] Automated token capture failed.")
        print("[*] If you can see the token in the browser (developer tools → Network or Application → Local Storage),")
        print("[*] you can manually input the tokens.")
        
        manual_input = input("[?] Would you like to manually input the tokens? (y/n): ").lower()
        if manual_input == 'y':
            # Print extraction guide
            print("\n===== HOW TO EXTRACT TOKENS =====")
            print("1. In the browser, press F12 to open DevTools")
            print("2. Go to the 'Network' tab")
            print("3. In the filter box, type '/api/auth' to find authentication requests")
            print("4. Look for responses with tokens in the 'Response' tab")
            print("   OR")
            print("5. Go to 'Application' tab → 'Local Storage' and look for 'access_token'")
            
            access_token = input("\n[?] Access token: ")
            refresh_token = input("[?] Refresh token: ")
            user_id = input("[?] User ID: ")
            user_role = input("[?] User role (learner/mentor): ") or role
            
            if access_token and refresh_token:
                tokens = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user_id': user_id,
                    'role': user_role
                }
    
    if tokens and tokens.get('access_token'):
        print("[+] Successfully captured authentication tokens!")
        return tokens
    else:
        print("[-] Failed to capture tokens. Please try again.")
        return None

def save_tokens(tokens, output_file=OUTPUT_FILE):
    """Save tokens to CSV file"""
    file_exists = os.path.exists(output_file)
    
    with open(output_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['access_token', 'refresh_token', 'user_id', 'role'])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(tokens)
    
    print(f"[+] Tokens saved to {output_file}")

def run_collection(count, base_url, profile_path):
    """Run the token collection process"""
    try:
        driver = setup_driver(profile_path)
    except Exception as e:
        print(f"[-] Error setting up Chrome driver: {str(e)}")
        print("\n[*] Troubleshooting steps:")
        print("1. Make sure you have Chrome installed")
        print("2. Update your Chrome to the latest version")
        print("3. Make sure the Chrome profile path is correct")
        print("4. Try logging into Google manually in Chrome first")
        return
    
    try:
        print("========================================")
        print("= CPLite Auth Token Collector for Load Testing =")
        print("========================================")
        print(f"Base URL: {base_url}")
        print(f"Tokens to collect: {count}")
        print(f"Using Chrome profile: {profile_path or get_default_chrome_profile_path()}")
        
        print("\nThis script will use your existing Chrome profile")
        print("(which should already be logged into Google)")
        print("to collect authentication tokens for load testing.")
        
        for i in range(count):
            # Alternate between learner and mentor roles
            role = "learner" if i % 2 == 0 else "mentor"
            
            print(f"\n--- Collection {i+1}/{count} (Role: {role}) ---")
            token = collect_token(driver, base_url, role)
            
            if token:
                save_tokens(token)
            else:
                print("[-] Token collection failed for this iteration, continuing...")
            
            # Small delay between collections
            time.sleep(2)
            
            # Clear cookies and storage except Google auth
            try:
                driver.execute_script("""
                    // Get all cookies
                    const cookies = document.cookie.split(';');
                    
                    // Delete app cookies but keep Google cookies
                    for (let cookie of cookies) {
                        const cookieName = cookie.split('=')[0].trim();
                        if (!cookieName.includes('google')) {
                            document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                        }
                    }
                    
                    // Clear localStorage except Google items
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (!key.includes('google')) {
                            localStorage.removeItem(key);
                        }
                    }
                    
                    // Clear sessionStorage except Google items
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        if (!key.includes('google')) {
                            sessionStorage.removeItem(key);
                        }
                    }
                """)
            except:
                # If the script fails, just clear everything and re-login
                driver.delete_all_cookies()
                driver.execute_script("localStorage.clear(); sessionStorage.clear();")
        
        print("\n[+] Token collection completed!")
        print(f"[+] Collected tokens saved to {OUTPUT_FILE}")
        print("[+] You can now run Locust with these tokens.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect authentication tokens for load testing using Chrome profile")
    parser.add_argument("--count", type=int, default=5, help="Number of tokens to collect")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL of the application")
    parser.add_argument("--profile-path", type=str, help="Path to Chrome user profile (uses default if not specified)")
    
    args = parser.parse_args()
    run_collection(args.count, args.base_url, args.profile_path)