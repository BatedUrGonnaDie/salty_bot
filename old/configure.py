import os
import ConfigParser

def configure():
    config = ConfigParser.RawConfigParser()

    if os.path.exists('config.ini'):
        config.read('config.ini')
        nick = config.get('Login', 'twitch_nick')
        password = config.get('Login', 'oauth')
        message_after_number = config.getint('Twitch Messaging', 'Message After Amount')
        message_number_timer = config.getfloat('Twitch Messaging', 'Message Amount Timer')
        automated_message = config.get('Twitch Messaging', 'Automated Message')
##        twitch_api = config.getboolean("API's", 'twitch')
##        league_api = config.getboolean("API's", 'league')
##        osu_api = config.getboolean("API's", 'osu')
    else:
        nick = raw_input('Twitch Username: ')
        password = raw_input('Twitch Oauth: ')
        if 'oauth:' not in password:
            password = 'oauth:' + password
        message_after_number = raw_input('How many messages passed until automated message: ')
        message_number_timer = raw_input('Minimum time before # of lines will trigger (in seconds): ')
        automated_message = raw_input('Automated message: ')
        print "You will need API keys for each API you wish to use."
        print "Note the basic Twitch info grab does not require an API key."
        twitch_api = raw_input('Use twitch api? y/n: ')
        twitch_api.lower()
        while twitch_api != 'y' and twitch_api != 'n':
            print "Please enter 'y' or 'n'."
            twitch_api = raw_input('Use twitch api? y/n: ')
            twitch_api.lower()
        league_api = raw_input('Use league api? y/n :')
        league_api.lower()
        while league_api != 'y' and league_api != 'n':
            print "Please enter 'y' or 'n'."
            league_api = raw_input('Use league api? y/n: ')
            league_api.lower()
        osu_api = raw_input('Use osu api? y/n: ')
        osu_api.lower()
        while osu_api != 'y' and osu_api != 'n':
            print "Please enter 'y' or 'n'."
            osu_api = raw_input('Use osu api? y/n: ')
            osu_api.lower()
        twitch_api = boolify(twitch_api)
        league_api = boolify(league_api)
        osu_api = boolify(osu_api)
        config.add_section('Login')
        config.set('Login', 'Username', nick)
        config.set('Login', 'Oauth', password)
        config.add_section('Twitch Messaging')
        config.set('Twitch Messaging', 'Message After Amount', message_after_number)
        config.set('Twitch Messaging', 'Message Amount Timer', message_number_timer)
        config.set('Twitch Messaging', 'Automated Message', automated_message)
        config.add_section("API's")
        config.set("API's", 'Twitch', twitch_api)
        config.set("API's", 'League', league_api)
        config.set("API's", 'Osu', osu_api)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    return nick, password, message_after_number, message_number_timer, automated_message
