import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

export const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
);

export async function saveUserCookies(discordId: string, rt: string, at: string) {
  const { error } = await supabase.from('user_cookies').upsert({
    discord_id: discordId,
    cookie: `app.rt=${rt}; app.at=${at}`,
    updated_at: new Date(),
  }, { onConflict: 'discord_id' });
  if (error) throw error;
}

export async function saveRoundHistory(discordId: string, games: any[]) {
  const rows = games.map(g => ({
    discord_id: discordId,
    game_type: 'mines',
    round_id: g._id || g.id,
    mines_count: g.mines,
    grid_size: g.gridSize,
    difficulty: null,
    created_at: g.createdAt ? new Date(g.createdAt).toISOString() : new Date().toISOString(),
  }));

  const { error } = await supabase.from('user_round_history').upsert(rows, {
    onConflict: 'discord_id,game_type,round_id'
  });
  if (error) throw error;
}
