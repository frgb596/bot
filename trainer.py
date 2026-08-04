import requests
import numpy as np
import pandas as pd
import os
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, LSTM
from sklearn.model_selection import train_test_split
from config import MINES_MODEL_PATH, SLIDE_MODEL_PATH
from predictor import BloxflipAuth  # 复用 predictor 中的认证类

CSV_FILE = "games.csv"

def get_session():
    # 使用与 predictor 相同的认证方式
    auth = BloxflipAuth()
    return auth.get_session()

# ---------- Save game to CSV ----------
def save_game_to_csv(tx):
    df = pd.DataFrame([tx])
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

# ---------- Fetch from API ----------
def fetch_mines_history(limit=500):
    session = get_session()
    url = f"https://bloxflip.com/api/games/mines/history?size={limit}&page=0"
    resp = session.get(url)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"API error: {resp.status_code}")
        return []

def load_local_mines_data():
    if not os.path.exists(CSV_FILE):
        return []
    df = pd.read_csv(CSV_FILE)
    df = df[df['game'] == 'Mines']
    return df.to_dict('records')

# ---------- Prepare data for CNN ----------
def prepare_mines_data(history):
    X, y = [], []
    for game in history:
        grid = np.zeros((5, 5), dtype=int)
        moves = game.get('moves', [])
        for i, move in enumerate(moves):
            idx = move['index']
            row, col = divmod(idx, 5)
            if move['bomb']:
                grid[row][col] = -1
            else:
                grid[row][col] = 1
            if i < len(moves) - 1:
                next_move = moves[i+1]
                if not next_move['bomb']:
                    X.append(grid.copy())
                    y.append(next_move['index'])
    if len(X) > 0:
        return np.array(X).reshape(-1, 5, 5, 1), np.array(y)
    else:
        return None, None

def build_mines_cnn():
    model = Sequential([
        Conv2D(32, (2, 2), activation='relu', input_shape=(5, 5, 1)),
        MaxPooling2D((2, 2)),
        Conv2D(64, (2, 2), activation='relu'),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(25, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

# ---------- Main training functions ----------
def train_mines_model():
    api_data = fetch_mines_history(500)
    local_data = load_local_mines_data()
    all_data = api_data + local_data
    if not all_data:
        return "No Mines data available"
    X, y = prepare_mines_data(all_data)
    if X is None or len(X) < 10:
        return "Not enough labeled data (need at least 10 samples)"
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = build_mines_cnn()
    model.fit(X_train, y_train, epochs=30, batch_size=32, validation_data=(X_test, y_test))
    model.save(MINES_MODEL_PATH)
    acc = model.evaluate(X_test, y_test, verbose=0)[1]
    return f"Mines model trained on {len(X)} samples. Accuracy: {acc:.2%}"

def train_slide_model():
    # Placeholder – you can replace with real data later
    return "Slide model training skipped (no real data yet)."

def train_all():
    result_mines = train_mines_model()
    result_slide = train_slide_model()
    return f"{result_mines}\n{result_slide}"

if __name__ == "__main__":
    print(train_all())
