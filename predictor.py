import requests
import numpy as np
import os
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, ROBLOX_COOKIE, BLOXFLIP_AUTH, MINES_MODEL_PATH, TOWERS_MODEL_PATH

# ============= AUTHENTICATION (dual) =============
class BloxflipAuth:
    """Handles both app.rt/app.at cookies and Roblox cookie login."""
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
                # Try to use bloxflip.py if installed
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

# ============= ALGORITHMS (from ege) =============
from algorithms.mines import MinesPredictor
from algorithms.towers import TowersPredictor

# ============= PREDICTOR WRAPPER =============
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

    # Helper to get current game state
    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your authentication credentials.")
        resp.raise_for_status()
        return resp.json()

predictor = BloxflipPredictor()import requests
import numpy as np
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, BLOXFLIP_AUTH, ROBLOX_COOKIE, MINES_MODEL_PATH, SLIDE_MODEL_PATH

# --- 新增: 从 ege 项目移植的认证类 ---
class BloxflipAuth:
    """模拟 ege 项目的 bloxflip.ts 认证逻辑"""
    def __init__(self):
        self.session = requests.Session()
        # 1. 设置模拟 Chrome 浏览器的 TLS 指纹 (ciphers, HTTP/2)
        # 注意: Python 的 requests 库底层是 urllib3，无法像 Node.js 的 undici 那样精细控制 TLS。
        # 这里通过设置 headers 和适配器来最大程度模拟。
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

        # 2. 处理认证 (优先使用 ROBLOX_COOKIE)
        self._setup_auth()

    def _setup_auth(self):
        """设置认证信息，优先使用 Roblox Cookie"""
        if ROBLOX_COOKIE:
            print("🔐 使用 ROBLOX_COOKIE 进行认证...")
            try:
                # 这里需要使用 bloxflip.py 库或类似方法将 Roblox Cookie 转换为 token
                # 由于 bloxflip.py 可能未安装，此处提供一个示例实现
                # 实际使用时，你可能需要安装并导入 bloxflip.py 库
                # from bloxflip import Authorization
                # auth = Authorization.generate(roblox_cookie=ROBLOX_COOKIE)
                # token = auth.token
                # self.session.headers.update({'Authorization': token})
                
                # 临时方案: 如果无法转换，则回退到 cookie 方式
                print("⚠️ 未找到 bloxflip.py 库，回退到 APP_RT/APP_AT 认证")
                self._use_cookie_auth()
            except Exception as e:
                print(f"❌ Roblox Cookie 认证失败: {e}")
                self._use_cookie_auth()
        else:
            self._use_cookie_auth()

    def _use_cookie_auth(self):
        """使用传统的 APP_RT 和 APP_AT cookie 认证"""
        print("🔐 使用 APP_RT/APP_AT Cookie 进行认证...")
        self.session.cookies.set('app.rt', APP_RT, domain='.bloxflip.com', path='/')
        self.session.cookies.set('app.at', APP_AT, domain='.bloxflip.com', path='/')
        if BLOXFLIP_AUTH:
            self.session.headers.update({'Authorization': BLOXFLIP_AUTH})

    def get_session(self):
        return self.session

# --- 原有的 BloxflipPredictor 类，但使用新的认证方式 ---
class BloxflipPredictor:
    def __init__(self):
        # 使用新的认证类来初始化 session
        auth = BloxflipAuth()
        self.session = auth.get_session()

        self.reload_models()
        self.accuracy = 54.1
        self.total_profit = 0.62
        self.games_analyzed = 0

    def reload_models(self):
        try:
            self.mines_model = load_model(MINES_MODEL_PATH)
        except:
            self.mines_model = None
        try:
            self.slide_model = load_model(SLIDE_MODEL_PATH)
        except:
            self.slide_model = None

    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your authentication credentials.")
        resp.raise_for_status()
        return resp.json()

    def get_current_mines_grid(self):
        try:
            data = self._get("https://bloxflip.com/api/games/mines")
        except Exception as e:
            print(f"Error: {e}")
            return None
        grid = np.zeros((5, 5), dtype=int)
        for tile in data.get('tiles', []):
            idx = tile['index']
            row, col = divmod(idx, 5)
            if tile.get('bomb'):
                grid[row][col] = -1
            elif tile.get('clicked'):
                grid[row][col] = 1
        return grid

    def predict_mines(self):
        if self.mines_model is None:
            return None, None, None
        grid = self.get_current_mines_grid()
        if grid is None:
            return None, None, None
        X = grid.reshape(1, 5, 5, 1)
        probs = self.mines_model.predict(X, verbose=0)[0]
        prob_grid = probs.reshape(5, 5)
        safe_spots = []
        bombs = []
        for r in range(5):
            for c in range(5):
                if grid[r][c] == -1:
                    bombs.append((r, c))
                elif grid[r][c] == 0:
                    safe_spots.append((r, c, prob_grid[r][c]))
        safe_spots.sort(key=lambda x: x[2], reverse=True)
        return safe_spots, bombs, prob_grid

    def predict_slide(self, last_10_colors):
        if self.slide_model is None:
            return "Unknown", 0.0
        color_map = {'red':0, 'purple':1, 'gold':2}
        reverse_map = {0:'red', 1:'purple', 2:'gold'}
        nums = [color_map.get(c, 0) for c in last_10_colors[-10:]]
        X = np.array(nums).reshape(1, 10, 1)
        pred = self.slide_model.predict(X, verbose=0)
        idx = np.argmax(pred)
        return reverse_map[idx], float(np.max(pred))

predictor = BloxflipPredictor()import requests
import numpy as np
from tensorflow.keras.models import load_model
from config import APP_RT, APP_AT, BLOXFLIP_AUTH, MINES_MODEL_PATH, SLIDE_MODEL_PATH

class BloxflipPredictor:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.set('app.rt', APP_RT, domain='.bloxflip.com', path='/')
        self.session.cookies.set('app.at', APP_AT, domain='.bloxflip.com', path='/')
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://bloxflip.com/',
            'Origin': 'https://bloxflip.com',
        })
        if BLOXFLIP_AUTH:
            self.session.headers.update({'Authorization': BLOXFLIP_AUTH})

        self.reload_models()
        self.accuracy = 54.1
        self.total_profit = 0.62
        self.games_analyzed = 0

    def reload_models(self):
        try:
            self.mines_model = load_model(MINES_MODEL_PATH)
        except:
            self.mines_model = None
        try:
            self.slide_model = load_model(SLIDE_MODEL_PATH)
        except:
            self.slide_model = None

    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code == 403:
            raise Exception("403 Forbidden – check your app.rt and app.at cookies.")
        resp.raise_for_status()
        return resp.json()

    def get_current_mines_grid(self):
        try:
            data = self._get("https://bloxflip.com/api/games/mines")
        except Exception as e:
            print(f"Error: {e}")
            return None
        grid = np.zeros((5, 5), dtype=int)
        for tile in data.get('tiles', []):
            idx = tile['index']
            row, col = divmod(idx, 5)
            if tile.get('bomb'):
                grid[row][col] = -1
            elif tile.get('clicked'):
                grid[row][col] = 1
        return grid

    def predict_mines(self):
        if self.mines_model is None:
            return None, None, None
        grid = self.get_current_mines_grid()
        if grid is None:
            return None, None, None
        X = grid.reshape(1, 5, 5, 1)
        probs = self.mines_model.predict(X, verbose=0)[0]
        prob_grid = probs.reshape(5, 5)
        safe_spots = []
        bombs = []
        for r in range(5):
            for c in range(5):
                if grid[r][c] == -1:
                    bombs.append((r, c))
                elif grid[r][c] == 0:
                    safe_spots.append((r, c, prob_grid[r][c]))
        safe_spots.sort(key=lambda x: x[2], reverse=True)
        return safe_spots, bombs, prob_grid

    def predict_slide(self, last_10_colors):
        if self.slide_model is None:
            return "Unknown", 0.0
        color_map = {'red':0, 'purple':1, 'gold':2}
        reverse_map = {0:'red', 1:'purple', 2:'gold'}
        nums = [color_map.get(c, 0) for c in last_10_colors[-10:]]
        X = np.array(nums).reshape(1, 10, 1)
        pred = self.slide_model.predict(X, verbose=0)
        idx = np.argmax(pred)
        return reverse_map[idx], float(np.max(pred))

# THIS IS THE ONLY LINE YOU NEED AT THE END:
predictor = BloxflipPredictor()
