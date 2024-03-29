import os, requests, threading
from recnetlogin import login_to_recnet
from time import sleep
from typing import List, Dict, Any, Union

class SubTracker:
    thread: threading.Thread
    token: str
    account_id: int
    pfp: str
    update_frequency: float
    webhooks: List[str]
    __old_subs: int

    def __init__(self, token: str, account_id: int, webhooks: List[str], update_frequency: float = 3) -> None:
        self.account_id = account_id
        self.token = token
        self.update_frequency = update_frequency
        self.webhooks = webhooks
        r = requests.get(f"https://accounts.rec.net/account/{self.account_id}")
        self.thread = threading.Thread(target=self.__sub_tracker, name=r.json()['username'])
        self.pfp = "https://img.rec.net/" + r.json()["profileImage"]
        self.__old_subs = fetch_subscribers(self.token, self.account_id)['subs']


    def __sub_tracker(self) -> None:
        """Sub tracker loop."""
        while True:
            # Fetch sub count.
            sub_fetch = fetch_subscribers(self.token, self.account_id)
            # Login if the fetch attempt was unsuccessful.
            if not sub_fetch['success']:
                login = login_to_recnet(os.environ["RR_USERNAME"], os.environ["RR_PASSWORD"])
                # Exit process if login failed. Otherwise set new token and continue.
                if not login.success:
                    print(f"[{self.thread.name}] Invalid RR login details")
                    break
                self.token = login.access_token
                continue

            subs = sub_fetch['subs']

            # Post embeds of sub increase or decrease if applicable.
            payload = {
                "embeds": [
                    {
                        "color": 0xE67E22,
                        "footer": {"text": f"**Account:** {self.thread.name}", "icon_url": self.pfp}
                    }
                ]
            }
            if subs > self.__old_subs:
                print(f"[{self.thread.name}] Gained subs!", subs-self.__old_subs)
                payload["embeds"][0]["title"] = "Gained subscribers!"
                payload["embeds"][0]["description"] = f"{self.__old_subs:,} (+{(subs-self.__old_subs):,})\n**Subscribers:** `{subs:,}`"
                for url in self.webhooks:
                    r = requests.post(url, json=payload, timeout=3)
                    if not r.ok:
                        print(f"[{self.thread.name}] POST request failed\n{url}")
                self.__old_subs = subs
            elif subs < self.__old_subs:
                print(f"[{self.thread.name}] Lost subs!", self.__old_subs-subs)
                payload["embeds"][0]["title"] = "Lost subscribers!"
                payload["embeds"][0]["description"] = f"{self.__old_subs:,} (-{(self.__old_subs-subs):,})\n**Subscribers:** `{subs:,}`"
                for url in self.webhooks:
                    r = requests.post(url, json=payload, timeout=3)
                    if not r.ok:
                        print(f"[{self.thread.name}] POST request failed\n{url}")
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
