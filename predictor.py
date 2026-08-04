import requests
import numpy as np
import os
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

class BloxflipAuth:
    def __init__(self, roblox_cookie=None, app_rt=None, app_at=None, auth_token=None):
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
        self._setup_auth(roblox_cookie, app_rt, app_at, auth_token)

    def _setup_auth(self, roblox_cookie, app_rt, app_at, auth_token):
        # Priority 1: explicit auth_token (from Roblox cookie or provided)
        if auth_token:
            self.session.headers.update({'Authorization': auth_token})
            return
        # Priority 2: Roblox cookie if provided
        if roblox_cookie:
            try:
                from bloxflip import Authorization
                auth = Authorization.generate(roblox_cookie=roblox_cookie)
                self.session.headers.update({'Authorization': auth.token})
                return
            except ImportError:
                print("⚠️ bloxflip.py not installed, falling back to cookies")
            except Exception as e:
                print(f"⚠️ Roblox auth failed: {e}, falling back to cookies")
        # Priority 3: app.rt/app.at cookies
        if app_rt and app_at:
            self.session.cookies.set('app.rt', app_rt, domain='.bloxflip.com', path='/')
            self.session.cookies.set('app.at', app_at, domain='.bloxflip.com', path='/')
            if BLOXFLIP_AUTH:
                self.session.headers.update({'Authorization': BLOXFLIP_AUTH})
        else:
            # Try environment variables as fallback
            if ROBLOX_COOKIE:
                try:
                    from bloxflip import Authorization
                    auth = Authorization.generate(roblox_cookie=ROBLOX_COOKIE)
                    self.session.headers.update({'Authorization': auth.token})
                    return
                except: pass
            if APP_RT and APP_AT:
                self.session.cookies.set('app.rt', APP_RT, domain='.bloxflip.com', path='/')
                self.session.cookies.set('app.at', APP_AT, domain='.bloxflip.com', path='/')
            else:
                raise ValueError("No valid authentication method provided.")

    def get_session(self):
        return self.session

from algorithms.mines import MinesPredictor
from algorithms.towers import TowersPredictor

class BloxflipPredictor:
    def __init__(self, session=None):
        self.session = session
        if self.session is None:
            self.auth = BloxflipAuth()
            self.session = self.auth.get_session()
        self.mines = MinesPredictor(self.session)
        self.towers = TowersPredictor(self.session)
        self.accuracy = 54.1
        self.total_profit = 0.62
        self.games_analyzed = 0
        # Per‑user sessions
        self.user_sessions = {}

    def get_user_session(self, user_id):
        """Return a session for a user, or None if not set."""
        return self.user_sessions.get(user_id)

    def set_user_session(self, user_id, auth_data):
        """
        auth_data: dict with 'type' ('roblox' or 'tokens') and credentials.
        For roblox: {'type':'roblox', 'cookie':'...'}
        For tokens: {'type':'tokens', 'app_rt':'...', 'app_at':'...'}
        We create a new BloxflipAuth and store the session.
        """
        if auth_data['type'] == 'roblox':
            auth = BloxflipAuth(roblox_cookie=auth_data['cookie'])
        elif auth_data['type'] == 'tokens':
            auth = BloxflipAuth(app_rt=auth_data['app_rt'], app_at=auth_data['app_at'])
        else:
            raise ValueError("Invalid auth type")
        self.user_sessions[user_id] = auth.get_session()
        return True

    def reload_models(self):
        self.mines.load_models()
        self.towers.load_models()

    def _get(self, url, params=None, session_override=None):
        sess = session_override or self.session
        resp = sess.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your authentication credentials.")
        resp.raise_for_status()
        return resp.json()

predictor = BloxflipPredictor()
