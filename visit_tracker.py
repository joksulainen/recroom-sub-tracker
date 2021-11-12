import json, platform, os, requests, threading
from time import sleep
from typing import Dict, Any, Union

class VisitTracker:
    thread: threading.Thread
    room_id: int
    image: str
    update_frequency: float
    webhook: str
    __old_visits: int
    __old_visitors: int
    __old_cheers: int
    __old_favs: int

    def __init__(self, room_id: int, webhook: str, update_frequency: float = 10) -> None:
        self.room_id = room_id
        self.update_frequency = update_frequency
        self.webhook = webhook
        r = requests.get(f"https://rooms.rec.net/rooms/{self.room_id}")
        r_json = r.json()
        self.thread = threading.Thread(target=self.__room_tracker, name="^"+r_json['Name'])
        self.image = "https://img.rec.net/" + r_json["ImageName"]
        room_stats = fetch_room(self.room_id)
        self.__old_visits = room_stats['stats']['VisitCount']
        self.__old_visitors = room_stats['stats']['VisitorCount']
        self.__old_cheers = room_stats['stats']['CheerCount']
        self.__old_favs = room_stats['stats']['FavoriteCount']


    def __room_tracker(self) -> None:
        """Room tracker loop."""
        while True:
            # Fetch visit count.
            room_fetch = fetch_room(self.room_id)
            # Login if the fetch attempt was unsuccessful.
            if not room_fetch['success']:
                print(f"[{self.thread.name}] Room ID is invalid!")
                break

            visits = room_fetch['stats']['VisitCount']
            visitors = room_fetch['stats']['VisitorCount']
            cheers = room_fetch['stats']['CheerCount']
            favs = room_fetch['stats']['FavoriteCount']

            # Post embed of new stats if applicable.
            if (visits>self.__old_visits)or(visitors>self.__old_visitors)or(cheers>self.__old_cheers)or(favs>self.__old_favs):
                print(f"[{self.thread.name}] Room stats updated!")
                payload = {
                    "embeds": [
                        {
                            "title": "Room stats updated!",
                            "fields": [
                                {
                                    "name": "Visits",
                                    "value": f"{self.__old_visits:,} (+{(visits-self.__old_visits):,})\n**Total:** `{visits:,}`"
                                },
                                {
                                    "name": "Visitors",
                                    "value": f"{self.__old_visitors:,} (+{(visitors-self.__old_visitors):,})\n**Total:** `{visitors:,}`"
                                },
                                {
                                    "name": "Cheers",
                                    "value": f"{self.__old_cheers:,} (+{(cheers-self.__old_cheers):,})\n**Total:** `{cheers:,}`"
                                },
                                {
                                    "name": "Favorites",
                                    "value": f"{self.__old_favs:,} (+{(favs-self.__old_favs):,})\n**Total:** `{favs:,}`"
                                }
                            ],
                            "color": 0xE67E22,
                            "thumbnail": {"url": self.image},
                            "footer": {"text": f"Room: {self.thread.name}"}
                        }
                    ]
                }
                r = requests.post(self.webhook, json=payload, timeout=3)
                if not r.ok:
                    print(f"[{self.thread.name}] POST request failed")
                self.__old_visits = visits
                self.__old_visitors = visitors
                self.__old_cheers = cheers
                self.__old_favs = favs
            else:
                print(f"[{self.thread.name}] No new room stats.")
            
            # Wait the given time before checking again.
            sleep(self.update_frequency)

        # Print if loop is broken out of
        print(f"[{self.thread.name}] Loop broken out of")


def fetch_room(room_id: int) -> Union[Dict[str, bool], Dict[str, Any]]:
    """Fetch subscriber count from the rec.net servers."""
    # Send GET request to request room.
    r = requests.get(f"https://rooms.rec.net/rooms/{room_id}")
    # Return a failed fetch attempt.
    if not r.ok:
        return {"success": False}

    # Return success with room stats and owner id.
    return {"success": True, "stats": r.json()['Stats']}


def main():
    """Main script function."""
    # Initial prints.
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")

    # Initialize configuration.
    if os.path.isfile("config.json"):
        with open("config.json") as file:
            cfg = json.load(file)

    # Check existence of environment variables.
    if "RR_WEBHOOK" not in os.environ:
        # If any of the above are missing, request user input to acquire them.
        webhook = input("Webhook URL to POST to: ")
    else:
        # Get webhook from environment variable.
        webhook = os.environ['RR_WEBHOOK']

    # Select room to track.
    room_id = None
    while not room_id:
        room_name_input = input("Room name to track visits of: ")
        r = requests.get(f"https://rooms.rec.net/rooms?name={room_name_input}")
        if not r.ok:
            print("Room does not exist. Try again.")
            continue
        room_id = r.json()["RoomId"]

    # Create VisitTracker instance and start its thread.
    tracker = VisitTracker(room_id, webhook, cfg['update_frequency'] if cfg else 10)
    tracker.thread.start()

if __name__ == "__main__":
    main()
