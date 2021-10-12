import json, os, platform, sys, requests, threading
from recnetlogin import login_to_recnet
from keep_alive import keep_alive
from time import sleep
from typing import List

def main():
    """Main script function."""
    global token, account_id, old_subs, pfp, username
    old_subs = 0

    # Initial prints.
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")

    # Initialize configuration.
    if not os.path.isfile("config.json"):
        sys.exit("'config.json' not found! Please add it and try again.")
    else:
        with open("config.json") as file:
            cfg = json.load(file)

    # Check existence of environment variables.
    if ("RR_USERNAME" or "RR_PASSWORD" or "RR_WEBHOOKS") not in os.environ:
        sys.exit(
            "Environment variables missing!\n"
            +f"'RR_USERNAME' present: {'RR_USERNAME' in os.environ}\n"
            +f"'RR_PASSWORD' present: {'RR_PASSWORD' in os.environ}\n"
            +f"'RR_WEBHOOKS' present: {'RR_WEBHOOKS' in os.environ}"
        )
    
    # Login to rec.net.
    login = login_to_recnet(os.environ["RR_USERNAME"], os.environ["RR_PASSWORD"])
    if not login["success"]:
        sys.exit("Incorrect RR account credentials!")
    
    #account_id = login['account_data']['accountId']
    #pfp = "https://img.rec.net/" + login['account_data']['profileImage']
    token = login['bearer_token']

    #Select account to track
    account_id = None
    while not account_id:
        username_input = input("Username of account to track subs of (Empty for using current login details): ")
        if username_input == "":
            account_id = login['account_data']['accountId']
            pfp = "https://img.rec.net/" + login['account_data']['profileImage']
            break
        r = requests.get(f"https://accounts.rec.net/account?username={username_input}")
        if not r.ok:
            print("Account does not exist. Try again.")
            continue
        result = r.json()
        account_id = result["accountId"]
        username = username_input
        pfp = "https://img.rec.net/" + result["profileImage"]



    old_subs = fetch_subscribers()['subs']

    # Get webhooks from environment variable.
    webhooks = os.environ['RR_WEBHOOKS'].split(";")
    print("Webhooks:", len(webhooks))
    for i in range(len(webhooks)):
        print(f"[{i}]{webhooks[i]}")
    print("-------------------")

    # Start sub tracker loop.
    t = threading.Thread(target=sub_tracker, args=(cfg['update_frequency'], webhooks))
    t.start()

    keep_alive()


def fetch_subscribers():
    """Fetch subscriber count from the rec.net servers."""
    global token, account_id

    # Send GET request to request sub count.
    r = requests.get(
        f"https://clubs.rec.net/subscription/subscriberCount/{account_id}",
        headers={"Authorization": token}
    )
    # Return a failed fetch attempt.
    if not r.ok:
        return {"success": False}

    subs = int(r.text)
    print("Subscribers:", subs)

    # Return success with sub count.
    return {"success": True, "subs": subs}


def sub_tracker(time: float, urls: List[str]):
    """Sub tracker loop."""
    global token, old_subs, pfp
    while True:
        # Fetch sub count.
        sub_fetch = fetch_subscribers()
        # Login if the fetch attempt was unsuccessful.
        if not sub_fetch['success']:
            login = login_to_recnet(os.environ["RR_USERNAME"], os.environ["RR_PASSWORD"])
            # Exit process if login failed. Otherwise set new token and continue.
            if not login['success']:
                sys.exit("Incorrect RR account credentials!")
            token = login['bearer_token']
            continue

        subs = sub_fetch['subs']

        # Post embeds of sub increase or decrease if applicable.
        if subs > old_subs:
            print("Gained subs!", subs-old_subs)
            payload = {
                "embeds": [
                    {
                        "title": "Gained subscribers!",
                        "description": f"{old_subs:,} (+{subs-old_subs})\n**Subscribers:** `{subs:,}`",
                        "color": 0xE67E22,
                        "thumbnail": {"url": pfp}
                    }
                ]
            }
            for url in urls:
                r = requests.post(url, json=payload, timeout=3)
                if not r.ok:
                    print(f"POST request failed\n{url}")
            old_subs = subs
        elif subs < old_subs:
            print("Lost subs!", old_subs-subs)
            payload = {
                "embeds": [
                    {
                        "title": "Lost subscribers!",
                        "description": f"{old_subs:,} (-{old_subs-subs})\n**Subscribers:** `{subs:,}`",
                        "color": 0xE67E22,
                        "thumbnail": {"url": pfp}
                    }
                ]
            }
            for url in urls:
                r = requests.post(url, json=payload, timeout=3)
                if not r.ok:
                    print(f"POST request failed\n{url}")
            old_subs = subs
        else:
            print("No sub change.")
        
        # Wait the given time before checking again.
        sleep(time)

# Start script if the script is the main script.
if __name__ == "__main__":
    main()
