import os, platform, sys, requests, threading
from recnetlogin import login_to_recnet
from time import sleep
from typing import List

class SubTracker:

    def __init__(self, name, account_id):
        self.thread = threading.Thread(target=self.sub_tracker, daemon=True)

    def sub_tracker(self):
        pass