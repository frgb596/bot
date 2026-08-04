import { Client, GatewayIntentBits, Interaction, ChatInputCommandInteraction, REST, Routes, ApplicationCommandOptionType } from 'discord.js';
import dotenv from 'dotenv';
import { fetchProfile, fetchMinesHistory } from './bloxflip.js';
import { supabase, saveUserCookies, saveRoundHistory } from './db.js';

dotenv.config();

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('clientReady', async () => {
  console.log(`🚀 Bot online as ${client.user?.tag}`);
  
  const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN!);
  await rest.put(Routes.applicationCommands(process.env.DISCORD_CLIENT_ID!), {
    body: [{
      name: 'connect',
      description: 'Link your BloxFlip account',
      options: [
        { name: 'rt', description: 'Your app.rt cookie', type: ApplicationCommandOptionType.String, required: true },
        { name: 'at', description: 'Your app.at cookie', type: ApplicationCommandOptionType.String, required: true },
      ],
    }],
  });
  console.log('✅ Slash commands registered');
});

client.on('interactionCreate', async (interaction: Interaction) => {
  if (!interaction.isChatInputCommand()) return;
  const cmd = interaction as ChatInputCommandInteraction;

  if (cmd.commandName === 'connect') {
    const rt = cmd.options.getString('rt', true);
    const at = cmd.options.getString('at', true);
    await cmd.deferReply({ ephemeral: true });

    try {
      const profile = await fetchProfile(rt, at);
      if (!profile.username) throw new Error("Invalid cookies");

      await saveUserCookies(cmd.user.id, rt, at);
      const history = await fetchMinesHistory(rt, at, 100);
      
      if (history.length > 0) await saveRoundHistory(cmd.user.id, history);

      await cmd.editReply(`✅ **Connected as ${profile.username}**\n⛏️ Synced ${history.length} Mines rounds.`);
    } catch (err: any) {
      await cmd.editReply(`❌ Failed: ${err.message}`);
    }
  }
});

client.login(process.env.DISCORD_TOKEN!);
