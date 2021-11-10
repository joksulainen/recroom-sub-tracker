import json, os, platform, sys, requests
from recnetlogin import login_to_recnet
from sub_tracker import SubTracker
from keep_alive import keep_alive

def main():
    """Main script function."""
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
    if not login.success:
        sys.exit("Incorrect RR account credentials!")

    #Select account to track
    account_id = None
    while not account_id:
        username_input = input("Username of account to track subs of (Empty for using current login details): ")
        if username_input == "":
            account_id = login.data["accountId"]
            break
        r = requests.get(f"https://accounts.rec.net/account?username={username_input}")
        if not r.ok:
            print("Account does not exist. Try again.")
            continue
        result = r.json()
        account_id = result["accountId"]

    # Get webhooks from environment variable.
    webhooks = os.environ['RR_WEBHOOKS'].split(";")
    print("Webhooks:", len(webhooks))
    for i in range(len(webhooks)):
        print(f"[{i}]{webhooks[i]}")
    print("-------------------")

    # Create SubTracker instance and start its thread.
    sub_tracker = SubTracker(login.access_token, account_id, webhooks, cfg["update_frequency"])
    sub_tracker.thread.start()

    keep_alive()

# Start script if the script is the main script.
if __name__ == "__main__":
    main()
