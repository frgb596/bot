import { REST, Routes, ApplicationCommandOptionType } from 'discord.js';
import dotenv from 'dotenv';
dotenv.config();

const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN!);

(async () => {
  await rest.put(
    Routes.applicationCommands(process.env.DISCORD_CLIENT_ID!),
    {
      body: [
        {
          name: 'connect',
          description: 'Link your BloxFlip account for ML analysis',
          options: [
            { name: 'rt', description: 'APP_RT cookie', type: ApplicationCommandOptionType.String, required: true },
            { name: 'at', description: 'APP_AT cookie', type: ApplicationCommandOptionType.String, required: true },
          ],
        },
      ],
    }
  );
  console.log('✅ Slash commands registered');
})();
