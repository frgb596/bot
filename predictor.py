import requests
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
