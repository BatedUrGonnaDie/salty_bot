Somewhat basic twitch chat bot with Twitch API and soon LoL/Osu API integration.

Coded with Python 2.7.6.  Required module install Requests due to "core" integration with the script and how it automates stuff.  More features in the future will be using the Requests module.

Aim of this bot is to be able to retrieve game playing for speedrunners to have rotating commands for different games.  Out of box commands are specific for myself but can be easily modified for any game by simply changing a few lines.

Code is no longer duct taped together.

Commands Explanation
====================
`!wr` will simply output the world record for the game and category.  Game is retrieved from Twitch API, and category is from either Status or entered manually if certain ones are not found in the Status.

`!leaderboards` will simply output the leaderboard for the game and category you are playing if it has one that you entered.

`!quote`/`!pun` will display a randomly selected quote/pun from a file.

`!addqoute`/`!addpun` will add the givin quote/pun to a review file so that you can manually move it over later.  In the future you will be able to move them over through twitch chat so you don't have to do it manually.

`!song` will display the current song you are playing on osu if you have osu!np going and your game is set to Osu!, or it will output the current song you are listening to from a media player if you have something that can read the info from them (I use [SMG](http://obsproject.com/forum/threads/smg-now-playing.12744/) for this).

`!bet` is meant for when you might throw the run away, but can easily be repurposed for a voting system (ie: what champion to play in LoL next).  
`!bets` will simply output what is currently wining.  
`!resetbets` will clear all bets and start over from scratch.

`!recheck` will re-retrieve your game and status from twitch incase you started it when you were offline/something isn't right/changed game/status.

`!exit` will shut the bot down nicely.