const BASE_URL = 'https://bloxflip.com/api';

const COMMON_HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Referer': 'https://bloxflip.com/mines',
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
  'x-currency': 'FLIPCOINS',
};

export interface BloxflipUser {
  id: string;
  username: string;
}

export interface MinesGame {
  _id: string;
  mines: number;
  gridSize: number;
  createdAt: string;
}

function buildCookieHeader(rt: string, at: string): string {
  return `app.rt=${rt}; app.at=${at}`;
}

export async function fetchProfile(rt: string, at: string): Promise<BloxflipUser> {
  const res = await fetch(`${BASE_URL}/user/lookup/me`, {
    headers: { ...COMMON_HEADERS, 'Cookie': buildCookieHeader(rt, at) },
  });
  if (!res.ok) throw new Error(`Profile fetch failed (${res.status})`);
  const data = await res.json();
  return { id: data.user?.id || data.id, username: data.user?.username || data.username };
}

export async function fetchMinesHistory(rt: string, at: string, limit: number = 100): Promise<MinesGame[]> {
  const allGames: MinesGame[] = [];
  let page = 0;
  while (allGames.length < limit) {
    const res = await fetch(`${BASE_URL}/games/mines/history?size=50&page=${page}`, {
      headers: { ...COMMON_HEADERS, 'Cookie': buildCookieHeader(rt, at) },
    });
    if (!res.ok) break;
    const data = await res.json();
    const games = Array.isArray(data) ? data : (data.games || data.data || []);
    if (games.length === 0) break;
    allGames.push(...games);
    page++;
    if (page > 10) break;
  }
  return allGames.slice(0, limit);
}
