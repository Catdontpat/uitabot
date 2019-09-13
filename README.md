# uitabot
**uitabot** is a [Discord](https://discordapp.com/) music bot that can be controlled both via chat commands and a real time web client. For a list of available chat commands see [COMMANDS.md](COMMANDS.md).

## Requirements
* [Discord API key](https://discordapp.com/developers)
* [YouTube API key](https://developers.google.com/youtube/v3/)
* Python 3.6
* npm
* ffmpeg & ffprobe (version 4 or newer needed for some live streams)

## Linux Installation from Source
### Setup
```sh
# Tested on Ubuntu 18.04
sudo apt-get install git python3 python3-dev libffi-dev ffmpeg npm
git clone https://github.com/tedle/uitabot.git
cd uitabot/bot
python3 -m pip install -r requirements.txt
cd ../web-client
npm install
```

### Configuration
Make a copy of the `config.example.json` in the root folder.
```sh
cp config.example.json config.json
```
Edit the new `config.json` file and fill in all the variables as needed. Documentation for every option can be found in [CONFIG.md](CONFIG.md).

### Building
#### Backend
```sh
cd bot
python3 uitabot.py
```
#### Frontend (development)
```sh
cd web-client
npm run dev
```
This will run a local web server that supports hot-reloading for development.
#### Frontend (production)
```sh
cd web-client
npm run build
```
This will output static asset files to the `web-client/build` folder that can then be served from any generic web server.

## Binary Installation
Not supported.

## License
[ISC License](LICENSE)
