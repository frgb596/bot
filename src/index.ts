// Inside src/index.ts -> interactionCreate handler

if (cmd.commandName === 'connect') {
  const rt = cmd.options.getString('rt', true);
  const at = cmd.options.getString('at', true);
  
  await cmd.deferReply({ ephemeral: true });

  try {
    // 1. Verify Account
    const profile = await fetchProfile(rt, at);
    if (!profile.username) throw new Error("Invalid cookies: Could not get username.");

    // 2. Save Cookies
    await saveUserCookies(cmd.user.id, rt, at);

    // 3. Fetch MINES History Specifically
    const minesHistory = await fetchMinesHistory(rt, at, 100);

    // 4. Save to Supabase (Mapping Mines fields to your SQL schema)
    if (minesHistory.length > 0) {
      const rows = minesHistory.map(g => ({
        discord_id: cmd.user.id,
        game_type: 'mines',
        round_id: g._id,
        mines_count: g.mines,
        grid_size: g.gridSize,
        difficulty: null, // Mines doesn't usually have "difficulty" like Slide does
        created_at: new Date(g.createdAt).toISOString(),
      }));

      const { error } = await supabase
        .from('user_round_history')
        .upsert(rows, { onConflict: 'discord_id,game_type,round_id' });
      
      if (error) throw error;
    }

    await cmd.editReply(
      `✅ **Connected as ${profile.username}**\n` +
      `⛏️ **Mines History:** Synced ${minesHistory.length} rounds.\n` +
      `🤖 **ML Status:** Ready to predict.`
    );

  } catch (err: any) {
    console.error(err);
    await cmd.editReply(`❌ Failed: ${err.message}`);
  }
}
