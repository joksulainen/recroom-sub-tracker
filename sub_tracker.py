import os, platform, sys, requests, threading
from recnetlogin import login_to_recnet
from time import sleep
from typing import List

class SubTracker:
    thread: threading.Thread = None
    name: str = ""
    account_id: int = None
    update_frequency: float = 3

    def __init__(self, name: str = "", account_id: int, update_frequency: float = 3):
        self.thread = threading.Thread(target=self.sub_tracker)

    def sub_tracker(self):
        pass
