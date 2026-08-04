import numpy as np
from tensorflow.keras.models import load_model
from config import MINES_MODEL_PATH

class MinesPredictor:
    def __init__(self, session):
        self.session = session
        self.models = []
        self.load_models()

    def load_models(self):
        try:
            # Load ensemble of 3 models (if they exist)
            for i in range(3):
                path = f"models/mines_ensemble_{i}.h5"
                self.models.append(load_model(path))
        except:
            # Fallback to single model
            try:
                self.models = [load_model(MINES_MODEL_PATH)]
            except:
                self.models = []

    def get_current_grid(self):
        # Fetch current Mines game state
        resp = self.session.get("https://bloxflip.com/api/games/mines")
        if resp.status_code != 200:
            return None
        data = resp.json()
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
            return [], []  # no models loaded

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
