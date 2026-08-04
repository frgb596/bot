import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
);

export async function saveUserCookies(discordId: string, rt: string, at: string) {
  const { error } = await supabase.from('user_cookies').upsert({
    discord_id: discordId,
    app_rt: rt,
    app_at: at,
    updated_at: new Date(),
  }, { onConflict: 'discord_id' });
  if (error) throw error;
}

export async function saveRoundHistory(discordId: string, games: any[]) {
  const rows = games.map(g => ({
    discord_id: discordId,
    game_type: g.type,
    round_id: g.id,
    mines_count: g.mines || null,
    grid_size: g.gridSize || null,
    difficulty: g.difficulty || null,
    created_at: new Date(g.timestamp).toISOString(),
  }));

  const { error } = await supabase.from('user_round_history').upsert(rows, {
    onConflict: 'discord_id,game_type,round_id'
  });
  if (error) throw error;
}
