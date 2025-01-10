import requests
import random
import time
import os
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime
from fake_useragent import UserAgent
from colorama import init, Fore, Style, Back

init(autoreset=True)

def get_headers():
    ua = UserAgent()
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://earn.taker.xyz',
        'Referer': 'https://earn.taker.xyz/',
        'User-Agent': ua.random
    }

def format_console_output(timestamp, current, total, status, address, referral, status_color=Fore.BLUE):
    return (
        f"[ "
        f"{Style.DIM}{timestamp}{Style.RESET_ALL}"
        f" ] [ "
        f"{Fore.YELLOW}{current}/{total}"
        f"{Fore.WHITE} ] [ "
        f"{status_color}{status}"
        f"{Fore.WHITE} ] "
        f"{Fore.BLUE}Address: {Fore.YELLOW}{address} "
        f"{Fore.MAGENTA}[ "
        f"{Fore.GREEN}{referral}"
        f"{Fore.MAGENTA} ]"
    )

def load_proxies():
    if not os.path.exists('proxies.txt'):
        return []
    with open('proxies.txt', 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def get_random_proxy(proxies):
    if not proxies:
        return None
    return random.choice(proxies)

def generate_wallet():
    w3 = Web3()
    acct = w3.eth.account.create()
    return acct.key.hex(), acct.address

def sign_message(private_key, message):
    w3 = Web3()
    message_hash = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(message_hash, private_key)
    return signed_message.signature.hex()

def save_account(private_key, address, referral_code):
    with open('accounts.txt', 'a') as f:
        f.write(f"Wallet Privatekey: {private_key}\n")
        f.write(f"Wallet Address: {address}\n")
        f.write(f"Referred to: {referral_code}\n")
        f.write("-" * 85 + "\n")

def perform_tasks(token, proxies_dict):
    print(f"{Fore.CYAN}Starting tasks for account...")
    target_tasks = [4, 5, 6, 13, 15]
    successful_tasks = []
    
    try:
        request_headers = get_headers()
        request_headers['Authorization'] = f'Bearer {token}'
        assignment_response = requests.post(
            'https://lightmining-api.taker.xyz/assignment/list',
            headers=request_headers,
            proxies=proxies_dict,
            timeout=None
        )
        
        if assignment_response.status_code != 200:
            print(f"{Fore.RED}Failed to get tasks. Status code: {assignment_response.status_code}")
            return False

        response_data = assignment_response.json()
        if not response_data or 'data' not in response_data:
            print(f"{Fore.RED}Invalid response format: {response_data}")
            return False

        assignments = response_data['data']
        if not assignments:
            print(f"{Fore.YELLOW}No assignments found")
            return False
        
        for assignment in assignments:
            if assignment['assignmentId'] in target_tasks:
                try:
                    do_response = requests.post(
                        'https://lightmining-api.taker.xyz/assignment/do',
                        headers=request_headers,
                        json={"assignmentId": assignment['assignmentId']},
                        proxies=proxies_dict,
                        timeout=None
                    )
                    
                    response_data = do_response.json()
                    if response_data.get('code') == 200:
                        successful_tasks.append(assignment['title'])
                        print(f"{Fore.GREEN}✓ {assignment['title']}")
                    else:
                        print(f"{Fore.RED}Task failed: {assignment['title']} - {response_data.get('message', 'Unknown error')}")
                
                except Exception as e:
                    print(f"{Fore.RED}Error executing task {assignment['assignmentId']}: {str(e)}")
                
                time.sleep(random.uniform(1, 2))
        
        try:
            mining_response = requests.post(
                'https://lightmining-api.taker.xyz/assignment/startMining',
                headers=request_headers,
                proxies=proxies_dict,
                timeout=None
            )
            
            response_data = mining_response.json()
            if response_data.get('code') == 200:
                print(f"{Fore.GREEN}✓ Mining started successfully")
            else:
                print(f"{Fore.RED}Mining start failed: {response_data.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"{Fore.RED}Error starting mining: {str(e)}")
            
        return len(successful_tasks) > 0

    except Exception as e:
        print(f"{Fore.RED}Error during task execution: {str(e)}")
        return False

def create_account(referral_code, account_number, total_accounts, proxies):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    private_key, address = generate_wallet()
    
    request_headers = get_headers()
    proxy = get_random_proxy(proxies)
    proxies_dict = {'http': proxy, 'https': proxy} if proxy else None

    try:
        nonce_response = requests.post(
            'https://lightmining-api.taker.xyz/wallet/generateNonce',
            headers=request_headers,
            json={"walletAddress": address},
            proxies=proxies_dict,
            timeout=None
        )
        
        if nonce_response.status_code != 200:
            print(f"{Fore.RED}Failed to get nonce. Status code: {nonce_response.status_code}")
            return False

        response_data = nonce_response.json()
        if not response_data or 'data' not in response_data or 'nonce' not in response_data['data']:
            print(f"{Fore.RED}Invalid nonce response format: {response_data}")
            return False

        message = response_data['data']['nonce']
        signature = sign_message(private_key, message)

        login_response = requests.post(
            'https://lightmining-api.taker.xyz/wallet/login',
            headers=request_headers,
            json={
                "address": address,
                "signature": signature,
                "message": message,
                "invitationCode": referral_code
            },
            proxies=proxies_dict,
            timeout=None
        )
        
        if login_response.status_code == 200:
            response_data = login_response.json()
            if not response_data or 'data' not in response_data or 'token' not in response_data['data']:
                print(f"{Fore.RED}Invalid login response format: {response_data}")
                return False

            token = response_data['data']['token']
            print(format_console_output(timestamp, account_number, total_accounts, "SUCCESS", address, referral_code, Fore.GREEN))
            
            #perform_tasks(token, proxies_dict)
            save_account(private_key, address, referral_code)
            print(f"{Fore.CYAN}Processing next account...{Style.RESET_ALL}")
            return True
        else:
            print(format_console_output(timestamp, account_number, total_accounts, "LOGIN FAILED", address, referral_code, Fore.RED))
            print(f"{Fore.RED}Login failed with status code: {login_response.status_code}")
            return False

    except Exception as e:
        print(format_console_output(timestamp, account_number, total_accounts, "ERROR", address, referral_code, Fore.RED))
        print(f"{Fore.RED}Error details: {str(e)}")
        return False

def print_header():
    header = """
╔══════════════════════════════════════════╗
║   Taker.xyz Referral Bot + Auto Tasks    ║
║   Github: https://github.com/im-hanzou   ║
╚══════════════════════════════════════════╝"""
    print(f"{Fore.CYAN}{header}{Style.RESET_ALL}")

def main():
    print_header()
    referral_code = input(f"{Fore.YELLOW}Enter referral code: {Style.RESET_ALL}")
    num_accounts = int(input(f"{Fore.YELLOW}Enter how many referral: {Style.RESET_ALL}"))
    print()
    
    proxies = load_proxies()
    if not proxies:
        print(f"{Fore.YELLOW}No proxies found in proxies.txt, running without proxies")
    
    successful = 0
    for i in range(1, num_accounts + 1):
        if create_account(referral_code, i, num_accounts, proxies):
            successful += 1
    
    print(f"\n{Fore.CYAN}[✓] All Process Completed!{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Total: {Fore.YELLOW}{num_accounts} {Fore.WHITE}| "
          f"Success: {Fore.GREEN}{successful} {Fore.WHITE}| "
          f"Failed: {Fore.RED}{num_accounts - successful}")

if __name__ == "__main__":
    main()
