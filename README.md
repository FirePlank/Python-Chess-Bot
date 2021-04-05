# Chess-Bot
This is a chess bot i made using python and cython! It supports the uci protocol meaning you can pretty much 
plug it into any gui chess application and it will be able to play there.

## Installation
Just download this repository and install all the requirements in the requirements.txt with `pip install -r requirements.txt`
and you are done! It's that easy

## Usage
You can use this with pretty much anything that supports the uci protocol. When they ask for the engine file please
give them the main.cmd that is in relation to main.py.

## Play Me
The bot is actually playable right now on lichess. The username is firefullbot. Just challenge the bot on standard mode on any time format and the game
will begin. If the bot does not accept or decline the challenge within 5 seconds it means the script is currently down so please come back later!

I'm quite curious of the rating of the bot. If enough ppl play it on rated maybe we can get the rating close enough to the truth.
The bot is quite underrated right now.

## Settings
Most applications allow you to specify the depth right from there, but if they dont you can just open up main.py and change the vars there for diversity.
Please keep the depth at a maximum of 4 because anything more will make the bot think for too long.
