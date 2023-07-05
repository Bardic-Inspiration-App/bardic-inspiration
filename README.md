# bardic-inspiration
Discord Application to help a DM/GM enhance their sessions.

## Built with:
* Python 3.10+
* Java
* discord.py
* Wavelink.py

## Development Setup
- Python 3.10 is required to run this bot, install it locally
- Create `credentials.json` file in root. Copy/Paste provided creds
- Add `.env` based on `env.example`

## Updating Dependencies
If you update dependencies then you will need to run the below for the heroku deploy
`poetry export --without-hashes --format=requirements.txt > requirements.txt`
