#!/usr/bin/env python3
"""
Simple Token Collector for CPLite Load Testing

This script helps you manually collect tokens for load testing by
guiding you through the process and saving the tokens to a CSV file.

Usage:
  python simple_token_collector.py
"""

import csv
import os
import webbrowser
import time
from datetime import datetime

# Output file
OUTPUT_FILE = "auth_tokens.csv"

def get_auth_url(base_url, role="learner"):
    """Get the authentication URL"""
    return f"{base_url}/login?preferred_role={role}"

def save_tokens(tokens, output_file=OUTPUT_FILE):
    """Save tokens to CSV file"""
    file_exists = os.path.exists(output_file)
    
    with open(output_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['access_token', 'refresh_token', 'user_id', 'role'])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(tokens)
    
    print(f"[+] Tokens saved to {output_file}")
    
    # Print a preview of the CSV file
    tokens_count = 1
    if file_exists:
        with open(output_file, 'r') as f:
            tokens_count = sum(1 for line in f) - 1  # Subtract header row
    
    print(f"[+] You now have {tokens_count} token(s) collected.")

def print_extraction_guide():
    """Print a guide on how to extract tokens"""
    print("\n===== HOW TO EXTRACT TOKENS =====")
    print("1. After logging in, open browser DevTools (F12 or right-click → Inspect)")
    print("2. Go to the 'Network' tab")
    print("3. In the filter box, type '/api/auth' to find authentication requests")
    print("4. Look for the response from a POST request to '/api/auth/google'")
    print("5. Click on that request, then click the 'Response' tab")
    print("6. You should see a JSON response with access_token, refresh_token, etc.")
    print("   Example: {\"access_token\":\"eyJ0...\", \"refresh_token\":\"eyJ1...\", \"user_id\":123, \"role\":\"learner\"}\n")

def collect_tokens_manually(count, base_url):
    """Guide the user through manually collecting tokens"""
    print("========================================")
    print("= Manual Token Collection for Load Testing =")
    print("========================================")
    print(f"Base URL: {base_url}")
    print(f"Tokens to collect: {count}")
    
    print("\nThis script will help you manually collect authentication tokens")
    print("for load testing with Locust. You will need to manually log in")
    print("with Google and extract the tokens from your browser.")
    
    # Print the extraction guide
    print_extraction_guide()
    
    for i in range(count):
        # Alternate between learner and mentor roles
        role = "mentor" if i % 2 == 0 else "learner"
        
        print(f"\n--- Collection {i+1}/{count} (Role: {role}) ---")
        
        # Open browser with the auth URL
        auth_url = get_auth_url(base_url, role)
        print(f"[*] Opening browser to: {auth_url}")
        webbrowser.open(auth_url)
        
        # Wait for user to complete login
        input("\n[*] Press Enter once you've logged in and can see the tokens...")
        
        # Get token info from user
        print("\n[*] Enter the token information you extracted:")
        access_token = input("Access Token: ")
        refresh_token = input("Refresh Token: ")
        user_id = input("User ID: ")
        user_role = input("User Role (learner/mentor): ") or role
        
        # Save tokens
        if access_token and refresh_token:
            tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_id': user_id,
                'role': user_role
            }
            save_tokens(tokens)
            print("[+] Token saved successfully!")
        else:
            print("[-] Missing token information, skipping...")
            print("[*] Let's try again with the guide.")
            print_extraction_guide()
            retry = input("[?] Would you like to try again for this token? (y/n): ").lower()
            if retry == 'y':
                i -= 1  # Retry this iteration
    
    print("\n[+] Token collection completed!")
    print(f"[+] Collected tokens saved to {OUTPUT_FILE}")
    print("[+] You can now run Locust with these tokens using:")
    print(f"    locust -f locustfile.py --host {base_url}")

if __name__ == "__main__":
    print("Simple Token Collector for CPLite Load Testing\n")
    
    base_url = input("Enter your application base URL [http://localhost:8000]: ") or "http://localhost:8000"
    count = int(input("How many tokens would you like to collect? [4]: ") or "4")
    
    collect_tokens_manually(count, base_url)