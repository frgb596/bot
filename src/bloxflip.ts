// src/bloxflip.ts

const BASE_URL = 'https://bloxflip.com/api';

// Headers required to bypass basic bot detection and match your browser session
const COMMON_HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Referer': 'https://bloxflip.com/mines', // Updated referer to match the game context
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
  'x-currency': 'FLIPCOINS',
};

export interface BloxflipUser {
  id: string;
  username: string;
  avatar?: string;
}

// Structure based on typical Mines API responses
export interface MinesGame {
  _id: string;
  betAmount: number;
  payoutMultiplier: number;
  mines: number;       // Number of mines chosen
  gridSize: number;    // e.g., 25 for 5x5
  tiles: number[];     // Array of revealed tile indices
  createdAt: string;
  status: string;      // "won", "lost", etc.
}

function buildCookieHeader(rt: string, at: string): string {
  // CRITICAL: Must use lowercase 'app.rt' and 'app.at' as seen in your cURL
  return `app.rt=${rt}; app.at=${at}`;
}

/**
 * Fetches the user profile to confirm identity (Username)
 */
export async function fetchProfile(rt: string, at: string): Promise<BloxflipUser> {
  const url = `${BASE_URL}/user/lookup/me`;
  
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      ...COMMON_HEADERS,
      'Cookie': buildCookieHeader(rt, at),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Profile fetch failed (${res.status}): ${text}`);
  }

  const data = await res.json();
  
  // Mapping based on common BloxFlip response structures
  return {
    id: data.user?.id || data.id || data._id,
    username: data.user?.username || data.username || data.name,
    avatar: data.user?.avatar || data.avatar,
  };
}

/**
 * Fetches Mines game history specifically
 * Uses pagination to get enough data for ML
 */
export async function fetchMinesHistory(rt: string, at: string, limit: number = 100): Promise<MinesGame[]> {
  const allGames: MinesGame[] = [];
  let page = 0;
  const pageSize = 50; // Fetch 50 at a time

  while (allGames.length < limit) {
    // Using the specific endpoint you found
    const url = `${BASE_URL}/games/mines/history?size=${pageSize}&page=${page}`;
    
    const res = await fetch(url, {
      method: 'GET',
      headers: {
        ...COMMON_HEADERS,
        'Cookie': buildCookieHeader(rt, at),
      },
    });

    if (!res.ok) {
      console.error(`[BloxFlip] History fetch failed on page ${page}: ${res.status}`);
      break; 
    }

    const data = await res.json();
    
    // The API usually returns an array directly or inside a 'data' or 'games' property
    // Adjust this line if the console logs show a different structure
    const games: MinesGame[] = Array.isArray(data) ? data : (data.games || data.data || []);
    
    if (games.length === 0) break;

    allGames.push(...games);
    page++;

    // Safety break to prevent infinite loops if API behaves unexpectedly
    if (page > 10) break; 
  }

  return allGames.slice(0, limit);
}
