# TypeRace Discord Bot

A Discord bot that allows users to test their typing speed and race against each other, similar to popular typing test websites.

## Features

- **Typing Tests:** Test your typing speed with the `typespeed` command.
- **Typing Races:** Race against other users in the server with the `typerace` command.
- **Easy Mode:** Option to run tests without punctuation and capitalization.
- **Leaderboards & Profiles:** Track your progress over time and see how you stack up against others.
- **Database Integration:** Uses MongoDB Atlas to persist user statistics and bot data.
- **24/7 Hosting Ready:** Includes a `keep_alive.py` Flask server to easily host the bot on platforms like Render.

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/typeracediscordbot.git
   cd typeracediscordbot
   ```

2. **Install dependencies:**
   Make sure you have Python installed, then run:

   ```bash
   pip install -r requirements.txt
   ```

   _(Note: You may need to create a requirements.txt using `pip freeze > requirements.txt` if one isn't present)_

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add the following:

   ```env
   DISCORD_TOKEN=your_discord_bot_token
   MONGODB_URI=your_mongodb_connection_string
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Development

The bot's code is modularized into several components:

- `bot.py`: The entry point for the bot.
- `cogs/`: Contains the command modules (e.g., `typing.py` and `profile.py`).
- `utils.py`: Utility functions and database logic.
- `keep_alive.py`: A lightweight Flask server to keep the bot alive on ephemeral hosting services.
