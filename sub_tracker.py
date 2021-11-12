import json, platform, sys, os, requests, threading
from recnetlogin import login_to_recnet
from time import sleep
from typing import List, Dict, Any, Union

class SubTracker:
    thread: threading.Thread
    token: str
    account_id: int
    pfp: str
    update_frequency: float
    webhook: str
    __old_subs: int

    def __init__(self, token: str, account_id: int, webhook: str, update_frequency: float = 3) -> None:
        self.account_id = account_id
        self.token = token
        self.update_frequency = update_frequency
        self.webhook = webhook
        r = requests.get(f"https://accounts.rec.net/account/{self.account_id}")
        r_json = r.json()
        self.thread = threading.Thread(target=self.__sub_tracker, name="@"+r_json['username'])
        self.pfp = "https://img.rec.net/" + r_json["profileImage"]
        self.__old_subs = fetch_subscribers(self.token, self.account_id)['subs']


    def __sub_tracker(self) -> None:
        """Sub tracker loop."""
        while True:
            # Fetch sub count.
            sub_fetch = fetch_subscribers(self.token, self.account_id)
            # Login if the fetch attempt was unsuccessful.
            if not sub_fetch['success']:
                login = login_to_recnet(os.environ["RR_USERNAME"], os.environ["RR_PASSWORD"])
                # Break loop if login failed. Otherwise set new token and continue.
                if not login.success:
                    print(f"[{self.thread.name}] Invalid RR login details!")
                    break
                self.token = login.access_token
                continue

            subs = sub_fetch['subs']

            # Post embed of sub increase or decrease if applicable.
            payload = {
                "embeds": [
                    {
                        "color": 0xE67E22,
                        "thumbnail": {"url": self.pfp},
                        "footer": {"text": f"Account: {self.thread.name}"}
                    }
                ]
            }
            if subs > self.__old_subs:
                print(f"[{self.thread.name}] Gained subs!", subs-self.__old_subs)
                payload["embeds"][0]["title"] = "Gained subscribers!"
                payload["embeds"][0]["description"] = f"{self.__old_subs:,} (+{(subs-self.__old_subs):,})\n**Subscribers:** `{subs:,}`"
                r = requests.post(self.webhook, json=payload, timeout=3)
                if not r.ok:
                    print(f"[{self.thread.name}] POST request failed")
                self.__old_subs = subs
            elif subs < self.__old_subs:
                print(f"[{self.thread.name}] Lost subs!", self.__old_subs-subs)
                payload["embeds"][0]["title"] = "Lost subscribers!"
                payload["embeds"][0]["description"] = f"{self.__old_subs:,} (-{(self.__old_subs-subs):,})\n**Subscribers:** `{subs:,}`"
                r = requests.post(self.webhook, json=payload, timeout=3)
                if not r.ok:
                    print(f"[{self.thread.name}] POST request failed")
                self.__old_subs = subs
            else:
                print(f"[{self.thread.name}] No sub change.")
            
            # Wait the given time before checking again.
            sleep(self.update_frequency)

        # Print if loop is broken out of
        print(f"[{self.thread.name}] Loop broken out of")


def fetch_subscribers(token: str, account_id: int) -> Union[Dict[str, bool], Dict[str, Any]]:
    """Fetch subscriber count from the rec.net servers."""
    # Send GET request to request sub count.
    r = requests.get(
        f"https://clubs.rec.net/subscription/subscriberCount/{account_id}",
        headers={"Authorization": token}
    )
    # Return a failed fetch attempt.
    if not r.ok:
        return {"success": False}

    # Return success with sub count.
    return {"success": True, "subs": int(r.text)}


def main():
    """Main script function."""
    # Initial prints.
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")

    # Initialize configuration if it exists.
    if os.path.isfile("config.json"):
        with open("config.json") as file:
            cfg = json.load(file)

    # Check existence of environment variables.
    if ("RR_USERNAME" or "RR_PASSWORD" or "RR_WEBHOOK") not in os.environ:
        sys.exit(
            "Environment variables missing!\n" \
            f"'RR_USERNAME' present: {'RR_USERNAME' in os.environ}\n" \
            f"'RR_PASSWORD' present: {'RR_PASSWORD' in os.environ}\n" \
            f"'RR_WEBHOOK' present: {'RR_WEBHOOK' in os.environ}"
        )
    
    # Login to rec.net.
    login = login_to_recnet(os.environ["RR_USERNAME"], os.environ["RR_PASSWORD"])
    if not login.success:
        sys.exit("Incorrect RR account credentials!")

    # Get webhook from environment variable.
    webhook = os.environ['RR_WEBHOOK']

    # Select account to track.
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
        account_id = r.json()["accountId"]

    # Create SubTracker instance and start its thread.
    tracker = SubTracker(login.access_token, account_id, webhook, cfg["update_frequency"] if cfg else 3)
    tracker.thread.start()

if __name__ == "__main__":
    main()
