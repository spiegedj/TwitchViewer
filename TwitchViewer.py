#!/usr/bin/python

import urllib
import urllib2
import sys
import os 
import json        
import subprocess
import signal

#------- GLOBALS -----------
twitchApiUrl = 'https://api.twitch.tv/kraken/'
clientID = 'e5yp1mbb10ju6dmag1irayg4ncybz5j'
accessToken = 'a7vx7pwxfhiidyn7zmup202fuxgr3k'
pageLimit = 30
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


def RemoveNonASCII(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def SafeJSONAccess(node, subnode):
    if subnode in node:
        value = node[subnode]
        if isinstance(value, basestring):
            value = RemoveNonASCII(value)
            if len(value) > 80:
                value = value[0:80]
                value += '...'
        elif value is not None:
            value = '{:,}'.format(int(value))
        else:
            value = ''
        return value
    return ''

def GetGames(pageNumber, y):
    Clear()
    print "loading..."
    method = 'games/top'
    offset = pageNumber * pageLimit
    params = {'offset' : offset, 'limit': pageLimit}
    gamesDict = TwitchCall(method, params)
    count = len(gamesDict['top'])

    games = []
    for i in range(count):
        item = gamesDict['top'][i]
        if 'game' not in item: continue

        name = SafeJSONAccess(item['game'], 'name')
        viewers = SafeJSONAccess(item, 'viewers')
        channels = SafeJSONAccess(item, 'channels')

        game = [name, viewers, channels]
        games.append(game)

    return games

def GetMyGames(pageNumber, y):
    Clear();
    games = []
    games.append(['Starcraft II'])
    games.append(['Kerbal Space Program'])
    games.append(['Super Smash Bros. Melee'])
    games.append(['Super Smash Bros. for Wii U'])
    games.append(['Counter-Strike: Global Offensive'])
    games.append(['Planetside 2'])
    return games
    

def GetFollowedStreams(pageNumber, y):
    Clear()
    print "loading..."
    method = 'streams/followed'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit, 'oauth_token' : accessToken}
    streamsDict = TwitchCall(method, params)
    count = len(streamsDict['streams'])

    streams = []
    for i in range(count):
        item = streamsDict['streams'][i]
        if 'channel' not in item: continue

        status = SafeJSONAccess(item['channel'], 'status')
        game = SafeJSONAccess(item, 'game')
        name = SafeJSONAccess(item['channel'], 'name')
        viewers = SafeJSONAccess(item, 'viewers')

        stream = [name, game, status, viewers]
        streams.append(stream)

    return streams

def GetTopStreams(pageNumber, y):
    Clear()
    print "loading..."
    method = 'streams'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit}
    streamsDict = TwitchCall(method, params)
    count = len(streamsDict['streams'])

    streams = []
    for i in range(count):
        item = streamsDict['streams'][i]
        if 'channel' not in item: continue

        status = SafeJSONAccess(item['channel'], 'status')
        game = SafeJSONAccess(item, 'game')
        name = SafeJSONAccess(item['channel'], 'name')
        viewers = SafeJSONAccess(item, 'viewers')

        stream = [name, game, status, viewers]
        streams.append(stream)

    return streams

def GetStreams(pageNumber, game):
    Clear()
    print "loading..."
    method = 'streams'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit, 'game': game}
    streamsDict = TwitchCall(method, params)
    count = len(streamsDict['streams'])

    streams = []
    for i in range(count):
        item = streamsDict['streams'][i]
        if 'channel' not in item: continue

        status = SafeJSONAccess(item['channel'], 'status')
        name = SafeJSONAccess(item['channel'], 'name')
        followers = SafeJSONAccess(item['channel'], 'followers')
        viewers = SafeJSONAccess(item, 'viewers')

        stream = [name, status, viewers, followers]
        streams.append(stream)

    return streams

def PrintMenu(rows, selected, pageNum, table):
    # Print Menu
    Clear()
    print Color.GREEN + table.Title + Color.END
    print Color.BOLD + table.RowFormat.format("", *table.Headers) + Color.END
    if len(rows) == 0:
        print ''
        print Color.BOLD + "NO RESULTS FOUND" + Color.END
        print ''
        return

    for i in range(len(rows)):
        row = rows[i]
        if (i == selected):
            print Color.UNDERLINE + table.RowFormat.format("", *row) + Color.END
        else:
            print table.RowFormat.format("", *row)

    print Color.GREEN + ("Page %s" % (pageNum + 1)) + Color.END

class Table:
    def __init__(self, title, headers, rowFormat):
        self.Title = title
        self.Headers = headers
        self.RowFormat = rowFormat

class Menu:
    def __init__(self, successDel, listDel, table):
        self.SuccessDel = successDel
        self.Table = table
        self.ListDel = listDel
    def Run(self, param):
        self.Table.Title = param
        done = False
        selected = 0
        pageNum = 0
        rows = self.ListDel(pageNum, param)

        while not done:
            PrintMenu(rows, selected, pageNum, self.Table)
            
            # Get Input
            button = Input.NONE
            while 1:
                action,button = ReadInput()

                if action == Action.BUTTON_DOWN:
                    if button == Input.BUTTON_A:
                        self.SuccessDel(rows[selected][0])
                        break;
                    if button == Input.BUTTON_B:
                        done = True
                        break;
                    elif button == Input.AXIS_DOWN:
                        selected = (selected + 1) % len(rows)
                        break;
                    elif button == Input.AXIS_UP:
                        selected = max(selected - 1, 0)
                        break;
                    elif button == Input.AXIS_RIGHT:
                        if len(rows) == pageLimit:
                            pageNum += 1
                            rows = self.ListDel(pageNum, param)
                            break;
                    elif button == Input.AXIS_LEFT:
                        if pageNum > 0:
                            pageNum -= 1
                            rows = self.ListDel(pageNum, param)
                            break;
                    if button == Input.BUTTON_Y:
                        rows = self.ListDel(pageNum, param)
                        break;

def PlayStream(stream):
    Clear()
    print "Loading..."
    url = "twitch.tv/%s" % stream
    p = subprocess.Popen(['livestreamer', url, 'best', '-n'])

    button = Input.NONE
    action = Action.NONE
    while action != Action.BUTTON_DOWN or button != Input.BUTTON_B:
        action,button = ReadInput()

    #p.terminate()
    #process = psutil.Process(p.pid)
    #child_pid = process.get_children(recursive=true)
    #for pid in child_pid:
    #    os.kill(pid.pid, sig)
    sig = signal.SIGTERM
    os.kill(p.pid, sig)


def main():
    
    rowFormat = "{:<10}{:<30}{:<100}{:<15}{:<15}"
    streamTable = Table('', ["Name", "Status", "Viewers", "Followers"], rowFormat)
    streamMenu = Menu(PlayStream, GetStreams, streamTable)

    rowFormat = "{:<10}{:<70}{:<15}{:<15}"
    gameTable = Table('Top Games List', ["Name", "Viewers", "Channels"], rowFormat)
    gameMenu = Menu(streamMenu.Run, GetGames, gameTable)


    rowFormat = "{:<10}{:<30}{:<50}{:<100}{:<15}"
    topStreamTable = Table('', ["Name", "Game", "Status", "Viewers"], rowFormat)
    topStreamsMenu = Menu(PlayStream, GetTopStreams, topStreamTable)

    followedStreamMenu = Menu(PlayStream, GetFollowedStreams, topStreamTable)

    rowFormat ="{:<10}{:<30}"
    myGamesTable = Table('', ["Game"], rowFormat)
    myGamesMenu = Menu(streamMenu.Run, GetMyGames, myGamesTable)

    while 1:
        followedStreamMenu.Run('Followed Stream Menu')
        myGamesMenu.Run('My Games')
        gameMenu.Run('Top Games List')
        topStreamsMenu.Run('Top Streams List')
    return

if __name__ == "__main__":
    main()
