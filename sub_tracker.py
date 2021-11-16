import json, platform, sys, os, requests, threading
from time import sleep
from typing import Dict, Any, Union

class SubTracker:
    thread: threading.Thread
    is_running: bool = False
    account_id: int
    pfp: str
    update_frequency: float
    webhook: str
    __old_subs: int

    REQUEST_TIMEOUT = 3

    def __init__(self, account_id: int, webhook: str, update_frequency: float = 3) -> None:
        self.account_id = account_id
        self.update_frequency = update_frequency
        self.webhook = webhook
        r = requests.get(f"https://accounts.rec.net/account/{self.account_id}", timeout=self.REQUEST_TIMEOUT)
        r_json = r.json()
        self.thread = threading.Thread(target=self.__sub_tracker, name="@"+r_json['username'])
        self.pfp = "https://img.rec.net/" + r_json["profileImage"]
        self.__old_subs = fetch_subscribers(self.account_id, self.REQUEST_TIMEOUT)['subs']


    # Functions to start and stop tracker.
    # Currently does nothing meaningful.
    def start(self) -> None:
        """Start tracker."""
        self.is_running = True
        self.thread.start()

    def stop(self) -> None:
        """Stop tracker."""
        self.is_running = False


    def __sub_tracker(self) -> None:
        """Sub tracker loop."""
        while True:
            # Fetch sub count.
            sub_fetch = fetch_subscribers(self.account_id, self.REQUEST_TIMEOUT)
            # Login if the fetch attempt was unsuccessful.
            if not sub_fetch['success']:
                print(f"[{self.thread.name}] Username is invalid!")
                break

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
                r = requests.post(self.webhook, json=payload, timeout=self.REQUEST_TIMEOUT)
                if not r.ok:
                    print(f"[{self.thread.name}] POST request failed")
                self.__old_subs = subs
            elif subs < self.__old_subs:
                print(f"[{self.thread.name}] Lost subs!", self.__old_subs-subs)
                payload["embeds"][0]["title"] = "Lost subscribers!"
                payload["embeds"][0]["description"] = f"{self.__old_subs:,} (-{(self.__old_subs-subs):,})\n**Subscribers:** `{subs:,}`"
                r = requests.post(self.webhook, json=payload, timeout=self.REQUEST_TIMEOUT)
                if not r.ok:
                    print(f"[{self.thread.name}] POST request failed")
                self.__old_subs = subs
            else:
                print(f"[{self.thread.name}] No sub change.")
            
            # Wait the given time before checking again.
            sleep(self.update_frequency)

        # Print if loop is broken out of
        print(f"[{self.thread.name}] Loop broken out of")


def fetch_subscribers(token: str, account_id: int, timeout: float = 3) -> Union[Dict[str, bool], Dict[str, Any]]:
    """Fetch subscriber count from the rec.net servers."""
    # Send GET request to request sub count.
    r = requests.get(
        f"https://clubs.rec.net/subscription/subscriberCount/{account_id}", timeout=timeout
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
    if "RR_WEBHOOK" not in os.environ:
        sys.exit(
            "Environment variables missing!\n" \
            f"'RR_WEBHOOK' present: {'RR_WEBHOOK' in os.environ}"
        )

    # Check existence of environment variables.
    if "RR_WEBHOOK" not in os.environ:
        # If any of the above are missing, request user input to acquire them.
        webhook = input("Webhook URL to POST to: ")
    else:
        # Get webhook from environment variable.
        webhook = os.environ['RR_WEBHOOK']

    # Select account to track.
    account_id = None
    while not account_id:
        username_input = input("Username of account to track subs of: ")
        r = requests.get(f"https://accounts.rec.net/account?username={username_input}")
        if not r.ok:
            print("Account does not exist. Try again.")
            continue
        account_id = r.json()["accountId"]

    # Create SubTracker instance and start its thread.
    tracker = SubTracker(account_id, webhook, cfg["update_frequency"] if cfg else 3)
    tracker.thread.start()

if __name__ == "__main__":
    main()
