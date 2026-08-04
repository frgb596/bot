import requests
import numpy as np
import os
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

class BloxflipAuth:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'Referer': 'https://bloxflip.com/',
            'Origin': 'https://bloxflip.com',
        })
        self._setup_auth()

    def _setup_auth(self):
        # Priority 1: Roblox cookie if provided
        if ROBLOX_COOKIE:
            print("🔐 Using ROBLOX_COOKIE authentication")
            try:
                from bloxflip import Authorization
                auth = Authorization.generate(roblox_cookie=ROBLOX_COOKIE)
                token = auth.token
                self.session.headers.update({'Authorization': token})
                return
            except ImportError:
                print("⚠️ bloxflip.py not installed, falling back to cookies")
            except Exception as e:
                print(f"⚠️ Roblox auth failed: {e}, falling back to cookies")

        # Priority 2: app.rt/app.at cookies
        if APP_RT and APP_AT:
            print("🔐 Using APP_RT/APP_AT cookies")
            self.session.cookies.set('app.rt', APP_RT, domain='.bloxflip.com', path='/')
            self.session.cookies.set('app.at', APP_AT, domain='.bloxflip.com', path='/')
            if BLOXFLIP_AUTH:
                self.session.headers.update({'Authorization': BLOXFLIP_AUTH})
        else:
            raise ValueError("Neither ROBLOX_COOKIE nor APP_RT/APP_AT provided.")

    def get_session(self):
        return self.session

from algorithms.mines import MinesPredictor
from algorithms.towers import TowersPredictor

class BloxflipPredictor:
    def __init__(self):
        self.auth = BloxflipAuth()
        self.session = self.auth.get_session()
        self.mines = MinesPredictor(self.session)
        self.towers = TowersPredictor(self.session)
        self.accuracy = 54.1
        self.total_profit = 0.62
        self.games_analyzed = 0

    def set_auth(self, roblox_cookie=None, app_rt=None, app_at=None):
        """Update authentication credentials and reinitialize session."""
        if roblox_cookie:
            os.environ['ROBLOX_COOKIE'] = roblox_cookie
        if app_rt:
            os.environ['APP_RT'] = app_rt
        if app_at:
            os.environ['APP_AT'] = app_at
        
        # Reinitialize auth and session
        self.auth = BloxflipAuth()
        self.session = self.auth.get_session()
        # Update mines and towers sessions
        self.mines.session = self.session
        self.towers.session = self.session
        return True

    def reload_models(self):
        self.mines.load_models()
        self.towers.load_models()

    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your authentication credentials.")
        resp.raise_for_status()
        return resp.json()

predictor = BloxflipPredictor()
import numpy as np
import os
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

class BloxflipAuth:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'Referer': 'https://bloxflip.com/',
            'Origin': 'https://bloxflip.com',
        })
        self._setup_auth()

    def _setup_auth(self):
        if ROBLOX_COOKIE:
            print("🔐 Using ROBLOX_COOKIE authentication")
            try:
                from bloxflip import Authorization
                auth = Authorization.generate(roblox_cookie=ROBLOX_COOKIE)
                token = auth.token
                self.session.headers.update({'Authorization': token})
                return
            except ImportError:
                print("⚠️ bloxflip.py not installed, falling back to cookies")
            except Exception as e:
                print(f"⚠️ Roblox auth failed: {e}, falling back to cookies")
        if APP_RT and APP_AT:
            print("🔐 Using APP_RT/APP_AT cookies")
            self.session.cookies.set('app.rt', APP_RT, domain='.bloxflip.com', path='/')
            self.session.cookies.set('app.at', APP_AT, domain='.bloxflip.com', path='/')
            if BLOXFLIP_AUTH:
                self.session.headers.update({'Authorization': BLOXFLIP_AUTH})
        else:
            raise ValueError("Neither ROBLOX_COOKIE nor APP_RT/APP_AT provided.")

    def get_session(self):
        return self.session

from algorithms.mines import MinesPredictor
from algorithms.towers import TowersPredictor

class BloxflipPredictor:
    def __init__(self):
        self.auth = BloxflipAuth()
        self.session = self.auth.get_session()
        self.mines = MinesPredictor(self.session)
        self.towers = TowersPredictor(self.session)
        self.accuracy = 54.1
        self.total_profit = 0.62
        self.games_analyzed = 0

    def reload_models(self):
        self.mines.load_models()
        self.towers.load_models()

    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your authentication credentials.")
        resp.raise_for_status()
        return resp.json()

predictor = BloxflipPredictor()
