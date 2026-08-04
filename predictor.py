import httpx
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
