from config import APP_RT, APP_AT, BLOXFLIP_AUTH
import requests

def get_session():
    s = requests.Session()
    s.cookies.set('app.rt', APP_RT, domain='.bloxflip.com')
    s.cookies.set('app.at', APP_AT, domain='.bloxflip.com')
    if BLOXFLIP_AUTH:
        s.headers.update({'Authorization': BLOXFLIP_AUTH})
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    return s

def fetch_mines_history(limit=500):
    session = get_session()
    url = f"https://bloxflip.com/api/games/mines/history?size={limit}&page=0"
    resp = session.get(url)
    return resp.json() if resp.status_code == 200 else []
