predictor = BloxflipPredictor()
import asyncio
import os
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

# ---------- MinesPredictor ----------
class MinesPredictor:
    def __init__(self, session):
        self.session = session
        self.models = []
        self.load_models()

    def load_models(self):
        try:
            from tensorflow.keras.models import load_model
            # Try ensemble
            for i in range(3):
                path = f"models/mines_ensemble_{i}.h5"
                self.models.append(load_model(path))
        except:
            try:
                from tensorflow.keras.models import load_model
                self.models = [load_model(MINES_MODEL_PATH)]
            except:
                self.models = []

    def get_current_grid(self):
        resp = self.session.get("https://bloxflip.com/api/games/mines")
        if resp.status_code != 200:
            return None
        data = resp.json()
        import numpy as np
        grid = np.zeros((5,5), dtype=int)
        for tile in data.get('tiles', []):
            idx = tile['index']
            r, c = divmod(idx, 5)
            if tile.get('bomb'):
                grid[r][c] = -1
            elif tile.get('clicked'):
                grid[r][c] = 1
        return grid

    def predict(self):
        grid = self.get_current_grid()
        if grid is None:
            return None, None
        if not self.models:
            return [], []
        import numpy as np
        X = grid.reshape(1,5,5,1)
        # Ensemble prediction (average probabilities)
        probs = np.mean([m.predict(X, verbose=0) for m in self.models], axis=0)[0]
        prob_grid = probs.reshape(5,5)

        safe_spots = []
        bombs = []
        for r in range(5):
            for c in range(5):
                if grid[r][c] == -1:
                    bombs.append((r,c))
                elif grid[r][c] == 0:
                    safe_spots.append((r,c,prob_grid[r][c]))
        safe_spots.sort(key=lambda x: x[2], reverse=True)
        return safe_spots, bombs

# ---------- TowersPredictor ----------
class TowersPredictor:
    def __init__(self, session):
        self.session = session
        self.model = None
        self.load_models()

    def load_models(self):
        try:
            from tensorflow.keras.models import load_model
            self.model = load_model(TOWERS_MODEL_PATH)
        except:
            self.model = None

    def get_current_grid(self):
        resp = self.session.get("https://bloxflip.com/api/games/towers")
        if resp.status_code != 200:
            return None
        return resp.json()

    def predict(self):
        data = self.get_current_grid()
        if data is None or self.model is None:
            return None, None
        # Simplified: return dummy safe spots (you can implement properly)
        return [], []

# ---------- BloxflipAuth ----------
class BloxflipAuth:
    def __init__(self, roblox_cookie=None, app_rt=None, app_at=None, auth_token=None):
        self.client = httpx.Client(
            http2=True,
            headers=self._get_headers(),
            cookies=self._get_cookies(roblox_cookie, app_rt, app_at),
            timeout=30.0,
            follow_redirects=True,
        )
        if auth_token:
            self.client.headers.update({'Authorization': auth_token})

    def _get_headers(self):
        return {
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
            'Referer': 'https://bloxflip.com/mines',
            'Origin': 'https://bloxflip.com',
        }

    def _get_cookies(self, roblox_cookie, app_rt, app_at):
        cookies = {}
        if roblox_cookie:
            try:
                from bloxflip import Authorization
                auth = Authorization.generate(roblox_cookie=roblox_cookie)
                self.client.headers.update({'Authorization': auth.token})
                return cookies
            except Exception as e:
                print(f"⚠️ Roblox auth failed: {e}, falling back to cookies")
        if app_rt and app_at:
            cookies['app.rt'] = app_rt
            cookies['app.at'] = app_at
        else:
            if APP_RT and APP_AT:
                cookies['app.rt'] = APP_RT
                cookies['app.at'] = APP_AT
        return cookies

    def get_session(self):
        return self.client

# ---------- Main Predictor Class ----------
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
        self.user_sessions = {}

    def get_user_session(self, user_id):
        return self.user_sessions.get(user_id)

    def set_user_session(self, user_id, auth_data):
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

# ===== THIS IS THE ONLY LINE AT THE BOTTOM =====
predictor = BloxflipPredictor()import httpx
import asyncio
import os
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

# ... (MinesPredictor, TowersPredictor 等类保持不变) ...

class BloxflipAuth:
    def __init__(self, roblox_cookie=None, app_rt=None, app_at=None, auth_token=None):
        # 1. 创建自定义的 HTTP/2 客户端，模拟 Chrome 指纹
        self.client = httpx.Client(
            http2=True,
            headers=self._get_headers(),
            cookies=self._get_cookies(roblox_cookie, app_rt, app_at),
            timeout=30.0,
            follow_redirects=True,
        )
        # 2. 设置认证 (如果有 auth_token)
        if auth_token:
            self.client.headers.update({'Authorization': auth_token})

    def _get_headers(self):
        """返回模拟 Chrome 浏览器的完整请求头"""
        return {
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
            'Referer': 'https://bloxflip.com/mines',
            'Origin': 'https://bloxflip.com',
        }

    def _get_cookies(self, roblox_cookie, app_rt, app_at):
        """构建 Cookie 字典，与 ege 的 buildCookieHeader 逻辑类似"""
        cookies = {}
        if roblox_cookie:
            # 如果提供了 Roblox cookie，尝试生成 token (需要 bloxflip.py)
            try:
                from bloxflip import Authorization
                auth = Authorization.generate(roblox_cookie=roblox_cookie)
                self.client.headers.update({'Authorization': auth.token})
                return cookies
            except Exception as e:
                print(f"⚠️ Roblox auth failed: {e}, falling back to cookies")
        if app_rt and app_at:
            cookies['app.rt'] = app_rt
            cookies['app.at'] = app_at
        else:
            # Fallback to environment variables
            if APP_RT and APP_AT:
                cookies['app.rt'] = APP_RT
                cookies['app.at'] = APP_AT
        return cookies

    def get_session(self):
        """返回 httpx 客户端，用于后续请求"""
        return self.client
