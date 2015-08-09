#!/usr/bin/python

import urllib
import urllib2
import sys
import os 
import json        
import subprocess

#------- GLOBALS -----------
player = "'/usr/bin/omxplayer -o hdmi'"
twitchApiUrl = 'https://api.twitch.tv/kraken/'
gameLimit = 50
streamLimit = 50
pipe = open('/dev/input/js0', 'r')

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class Input:
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_X = 2
    BUTTON_Y = 3
    BUTTON_L = 4
    BUTTON_R = 5
    BUTTON_SELECT = 6
    BUTTON_START = 7
    AXIS_LEFT = 8
    AXIS_RIGHT = 9
    AXIS_UP = 10
    AXIS_DOWN = 11
    NONE = 12

class Action:
    BUTTON_UP = 0
    BUTTON_DOWN = 1
    NONE = 2


    
# Converts the byte array from joystick to a action paired with button input
def ReadInput():
    msg = []
    while 1:
        for char in pipe.read(1):
            msg += [ord(char)]
            if len(msg) == 8:
                button = Input.NONE
                action = Action.BUTTON_DOWN

                # Action Type
                if msg[4] == 0:
                    action = Action.BUTTON_UP

                # Button event
                typ = ''
                if msg[6] == 2:
                    typ = 'axis'
                    if msg[5] == 128:
                        if msg[7] == 1:
                            button = Input.AXIS_UP
                        if msg[7] == 0:
                            button = Input.AXIS_LEFT
                    if msg[5] == 127:
                        if msg[7] == 1:
                            button = Input.AXIS_DOWN
                        if msg[7] == 0:
                            button = Input.AXIS_RIGHT
                elif msg[6] == 1: 
                    typ = 'button'
                    button = msg[7]

                return (action, button)

def TwitchCall(method, params):
    try:
        data = urllib.urlencode(params)
        response = urllib2.urlopen(('%s%s?%s' % (twitchApiUrl, method, data)).encode('utf-8'))
        result = response.read()
        return json.loads(result)
    except Exception as e:
        print 'An error has occurred when calling the Twitch Api: %s' % method
        print sys.exc_info()[0]
    finally:
        response.close()

def Clear():
    os.system('clear')

def GetGames():
    Clear()
    print "loading..."
    method = 'games/top'
    params = {'limit': gameLimit}
    gamesDict = TwitchCall(method, params)
    count = len(gamesDict['top'])

    games = []
    for i in range(count):
        item = gamesDict['top'][i]
        game = [item['game']['name'].encode('utf-8'), item['viewers'], item['channels']]
        games.append(game)

    return games

def GetStreams(game):
    Clear()
    print "loading..."
    method = 'streams'
    params = {'limit': streamLimit, 'game': game}
    streamsDict = TwitchCall(method, params)
    count = len(streamsDict['streams'])

    streams = []
    for i in range(count):
        item = streamsDict['streams'][i]
        followers = -1
        if 'followers' in item['channel']:
            followers = item['channel']['followers']
        stream = [item['channel']['name'], item['viewers'], followers]
        streams.append(stream)

    return streams

def PrintMenu(rows, selected, title, headers):
    # Print Menu
    Clear()
    print Color.GREEN + title + Color.END
    row_format = "{:<50}" * (len(headers) + 1)
    print Color.BOLD + row_format.format("", *headers) + Color.END

    for i in range(len(rows)):
        row = rows[i]
        if (i == selected):
            print Color.UNDERLINE + row_format.format("", *row) + Color.END
        else:
            print row_format.format("", *row)
        
def StreamMenu(game):
    streams = GetStreams(game)
    done = False
    selected = 0

    while not done:
        PrintMenu(streams, selected, game, ["Name", "Views", "Followers"])
        
        # Get Input
        button = Input.NONE
        while button == Input.NONE:
            action,button = ReadInput()

        if action == Action.BUTTON_DOWN:
            if button == Input.BUTTON_A:
                PlayStream(streams[selected][0])
            if button == Input.BUTTON_B:
                done = True
            elif button == Input.AXIS_DOWN:
                selected = (selected + 1) % len(streams)
            elif button == Input.AXIS_UP:
                selected = max(selected - 1, 0)
            if button == Input.BUTTON_Y:
                streams=GetStreams(game)
                


def GamesMenu():
    games = GetGames()
    done = False
    selected = 0

    while not done:
        PrintMenu(games, selected, "Top Game List", ["Name", "Viewers", "Channels"])
        
        # Get Input
        button = Input.NONE
        while button == Input.NONE:
            action,button = ReadInput()

        if action == Action.BUTTON_DOWN:
            if button == Input.BUTTON_A:
                StreamMenu(games[selected][0])
            elif button == Input.AXIS_DOWN:
                selected = (selected + 1) % len(games)
            elif button == Input.AXIS_UP:
                selected = max(selected - 1, 0)
            if button == Input.BUTTON_Y:
                games=GetGames()
        
    
def PlayStream(stream):
    Clear()
    print "Loading..."
    url = "twitch.tv/%s" % stream
    command = 'livestreamer twitch.tv/%s best -np "%s"' % (stream, player)
    #proc = subprocess.call(['livestreamer', url, 'best', '-np', player])
    p = subprocess.Popen(['livestreamer', url, 'best', '-n'])

    button = Input.NONE
    action = Action.NONE
    while action != Action.BUTTON_DOWN or button != Input.BUTTON_B:
        action,button = ReadInput()

    p.kill()


def main():

    GamesMenu()
    return

#   msg = []

#   while 1:
#       for char in pipe.read(1):
#           msg += [ord(char)]
#           if len(msg) == 8:
#               #print msg
#               

#               if action == Action.BUTTON_DOWN:
#                   if button == Input.BUTTON_A:
#                       print "A"
#                   elif button == Input.BUTTON_B:
#                       print "B"
#                   elif button == Input.BUTTON_X:
#                       print "X"
#                   elif button == Input.BUTTON_Y:
#                       print "Y"
#                   elif button == Input.BUTTON_L:
#                       print "L"
#                   elif button == Input.BUTTON_R:
#                       print "R"
#                   elif button == Input.BUTTON_SELECT:
#                       print "SELECT"
#                   elif button == Input.BUTTON_START:
#                       print "START"

#               msg = []

if __name__ == "__main__":
    main()
