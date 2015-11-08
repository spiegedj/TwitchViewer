#!/usr/bin/python

import errno
import urllib
import urllib2
import sys
import os, tempfile
import json        
import subprocess
import threading
import signal
import time
import datetime
from LivestreamerPlayer import LivestreamerPlayer
from livestreamer import Livestreamer

#------- GLOBALS -----------
twitchApiUrl = 'https://api.twitch.tv/kraken/'
clientID = 'e5yp1mbb10ju6dmag1irayg4ncybz5j'
accessToken = 'a7vx7pwxfhiidyn7zmup202fuxgr3k'
pageLimit = 30
pipe = open('/dev/input/js0', 'r')
ACCEPTABLE_ERRNO = (errno.EPIPE, errno.EINVAL, errno.ECONNRESET)
livestreamer = Livestreamer()
stopLSThread = False;
pipeStreamPath = '/tmp/stream'
lrThreads = None

#-------- GLOBAL ROWS ---------
topStreams = []
topGames = []
myGames = []
myFollows = []
streamsForGame = []

class Color:
    PURPLE = '\033[0;35m'
    CYAN = '\033[1;36m'
    BLUE = '\033[1;34m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[1;31m'
    UNDERLINE = '\033[4m'
    BOLD = '\033[1m'
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


# Calls the twitch API. Method and params are passed in.
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
    method = 'games/top'
    offset = pageNumber * pageLimit
    params = {'offset' : offset, 'limit': pageLimit}
    gamesDict = TwitchCall(method, params)
    count = min(len(gamesDict['top']), pageLimit)

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
    games = []
    games.append(['Starcraft II'])
    games.append(['Kerbal Space Program'])
    games.append(['Super Smash Bros. Melee'])
    games.append(['Super Smash Bros. for Wii U'])
    games.append(['Counter-Strike: Global Offensive'])
    games.append(['Planetside 2'])
    return games
    

def GetFollowedStreams(pageNumber, y):
    method = 'streams/followed'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit, 'oauth_token' : accessToken}
    streamsDict = TwitchCall(method, params)
    count = min(len(streamsDict['streams']), pageLimit)

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
    method = 'streams'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit}
    streamsDict = TwitchCall(method, params)
    count = min(len(streamsDict['streams']), pageLimit)

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
    method = 'streams'
    offset = pageNumber * pageLimit
    params = {'offset': offset, 'limit': pageLimit, 'game': game}
    streamsDict = TwitchCall(method, params)
    count = min(len(streamsDict['streams']), pageLimit)

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


class Table:
    def __init__(self, title, headers, rowFormat):
        self.Title = title
        self.Headers = headers
        self.RowFormat = rowFormat

class LRThreads:
    def __init__(self):
        self.RefreshRate = 5 * 60
        self.UpdateRate = 60

        self.ShortRT = []
        self.LongRT = threading.Timer(self.RefreshRate, self.LoadRowsLong, [])
        self.LongRT.start()
        self.UpdateT = threading.Timer(self.UpdateRate, self.Update, [])
        self.UpdateT.start()
        self.Menu = None
        self.Lock = threading.Lock()

    def LoadRowsLong(self):
        self.Lock.acquire()
        curMenu = self.Menu
        if curMenu is not None: 
            curMenu.Rows = curMenu.ListDel(curMenu.PageNum, curMenu.Param)
            curMenu.ts = time.time()

            if curMenu is self.Menu:
                curMenu.Print()
        self.LongRT = threading.Timer(self.RefreshRate, self.LoadRowsLong, [])
        self.LongRT.start()
        self.Lock.release()

    def Update(self):
        self.Lock.acquire()
        if self.Menu is not None:
            self.Menu.Print()
        self.UpdateT = threading.Timer(self.UpdateRate, self.Update, [])
        self.UpdateT.start()
        self.Lock.release()

    def LoadRowsShort(self):
        curMenu = self.Menu
        if curMenu is not None: 
            curMenu.Rows = curMenu.ListDel(curMenu.PageNum, curMenu.Param)
            curMenu.ts = time.time()

            self.Lock.acquire()
            if curMenu is self.Menu:
                curMenu.Print()
            self.Lock.release()

    def SetMenu(self, menu):
        self.Lock.acquire()
        self.Menu = menu
        if self.Menu is not None:
            # Only reload rows if a significant amount of time has passed
            curTime = time.time()
            #print "MS Passed: %d" % ((curTime - self.Menu.ts))
            if (curTime - self.Menu.ts) > self.RefreshRate:
                self.Menu.Rows = []
                shortRT = threading.Thread(target=self.LoadRowsShort)
                self.ShortRT.append(shortRT)
                shortRT.start()
        self.Lock.release()

    def Stop(self):
        print "Stopping..."
        self.Lock.acquire()
        self.LongRT.cancel()
        self.UpdateT.cancel()
        self.Lock.release()

        self.UpdateT.join()
        self.LongRT.join()
        print len(self.ShortRT)
        i = 0
        for thread in self.ShortRT:
            print "Joining " + str(i)
            thread.join()
            i += 1
        print "Stopped"
        

def formatTimeAgo(then):
    hString = ""
    mString = ""
    now = time.time()
    diff = now - then

    hrs = diff // (60 * 60)
    diff -= (hrs * 60 * 60)
    mins = diff // (60)
    diff -= (mins * 60)
    secs = diff

    
    if hrs > 0:
        plural = ""
        if hrs > 1: plural = "s"
        hString = "%d hour%s " % (hrs, plural)
        plural = ""
        if mins > 1: plural = "s"
        mString = "%d minute%s " % (mins, plural)

    plural = ""
    if mins is not 1: plural = "s"
    mString = "%d minute%s " % (mins, plural)

    return hString + mString + "ago"


class Menu:
    def __init__(self, successDel, listDel, table, rows, threadedRowsLoad):
        self.SuccessDel = successDel
        self.Table = table
        self.ListDel = listDel
        self.Rows = rows
        self.Selected = 0
        self.PageNum = 0
        self.ThreadedRowsLoad = threadedRowsLoad
        self.ts = None
        self.Lock = threading.Lock()

    def PrintBanner(self, f):
        print Color.PURPLE + f.format("mdyyyymmo.                 /mhyyyhmhyyyhm-          .ommyyyydm        ") + Color.END
        print Color.PURPLE + f.format("mo    mmmms::::::::::::::::om/:::om.   /m+::- .::::smmmm    om::::-   ") + Color.END
        print Color.PURPLE + f.format("mo    +++smo+++smo+++smo+++smo+++sm.   .+++ddsdo++++++hm    -+++++hy:`") + Color.END
        print Color.PURPLE + f.format("mo       /m.   /m.   /m.   /m.   /m.       hm+`       om          `/dh") + Color.END
        print Color.PURPLE + f.format("mo    /++sm.   /m.   /m.   /m.   /m.   .+++dh    :++++hm    -++/    om") + Color.END
        print Color.PURPLE + f.format("mo    mmmmm.   /m.   /m.   /m.   /m.   /mmmmh    hmmmmmm    ommm    om") + Color.END
        print Color.PURPLE + f.format("mo    ///sm.   ./`   ./`   /m.   /m.   .///dh    :////ym    ommm    om") + Color.END
        print Color.PURPLE + f.format("yd/`     /m.              :hm.   /ms-      hm+`       om    ommm    om") + Color.END
        print Color.PURPLE + f.format("`:yh+++++smo+++++++++++++hmmmo+++smmmy+++++dmmdo++++++hm++++hmmm++++hm") + Color.END
        print Color.PURPLE + f.format("   -ohmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmdo-") + Color.END
        print Color.PURPLE + f.format("      ./smmmmmdydmmmmmmmmmd/ymmmmmh:ymmmmmm-smmmmmmmo+mmmdo-mmmmh+-   \n\n") + Color.END

    def Print(self):
        self.Lock.acquire()
        rows = self.Rows
        selected = self.Selected
        pageNum = self.PageNum
        table = self.Table

        (height, width) = os.popen('stty size', 'r').read().split()
        #width = int(width) - 36
        center = '{:^' + str(width) + '}'
        rightAlign = '{:>' + str(width) + '}'

        # Print Menu
        Clear()
        self.PrintBanner(center)
        print Color.RED + center.format(table.Title) + '\n' + '\n' + Color.END
        print Color.BOLD + center.format(table.RowFormat.format("", *table.Headers)) + Color.END

        lineCount = 13 + 3 + 1
        for i in range(len(rows)):
            row = rows[i]
            if (i == selected):
                print Color.YELLOW + center.format(table.RowFormat.format("", *row)) + Color.END
            else:
                print center.format(table.RowFormat.format("", *row))
            lineCount += 1

        print Color.GREEN + '\n' + center.format(("Page %s" % (pageNum + 1))) + Color.END
        lineCount += 2

        for i in range(lineCount, int(height) - 3):
            print ""

        if self.ts is not None:
            timestamp = "Last Updated: %s which was %s" % (datetime.datetime.fromtimestamp(self.ts).strftime('%m/%d %l:%M:%S %p'), formatTimeAgo(self.ts))
            print Color.RED + rightAlign.format(timestamp) + Color.END

        self.Lock.release()

    def Run(self, param):
        global lrThreads
        self.Param = param
        self.Table.Title = param
        done = False
        if self.ThreadedRowsLoad:
            if len(self.Rows) == 0:
                Clear()
                print "Loading..."
                self.Rows = self.ListDel(self.PageNum, param)
                self.ts = time.time()
            self.Stopped = False
            lrThreads.SetMenu(self)
        else:
            self.Rows = self.ListDel(self.PageNum, param)
            self.ts = time.time()
            lrThreads.SetMenu(None)


        while not done:
            self.Print()
            
            # Get Input
            button = Input.NONE
            while 1:
                action,button = ReadInput()

                if action == Action.BUTTON_DOWN:
                    if button == Input.BUTTON_A:
                        self.SuccessDel(self.Rows[self.Selected][0])
                        break;
                    if button == Input.BUTTON_B:
                        done = True
                        break;
                    elif button == Input.AXIS_DOWN:
                        if len(self.Rows) > 0:
                            self.Selected = (self.Selected + 1) % len(self.Rows)
                        break;
                    elif button == Input.AXIS_UP:
                        self.Selected = max(self.Selected - 1, 0)
                        break;
                    elif button == Input.AXIS_RIGHT:
                        if len(self.Rows) == pageLimit:
                            self.PageNum += 1
                            Clear()
                            print "Loading..."
                            self.Rows = self.ListDel(self.PageNum, param)
                            self.ts = time.time()
                            break;
                    elif button == Input.AXIS_LEFT:
                        if self.PageNum > 0:
                            self.PageNum -= 1
                            Clear()
                            print "Loading..."
                            self.Rows = self.ListDel(self.PageNum, param)
                            self.ts = time.time()
                            break;
                    if button == Input.BUTTON_Y:
                        Clear()
                        print "Loading..."
                        self.Rows = self.ListDel(self.PageNum, param)
                        self.ts = time.time()
                        break;

def PlayStreamWS(stream):
    Clear()
    print "Loading..."
    url = "twitch.tv/%s" % stream
    p = subprocess.Popen(['livestreamer', url, 'best', '-n'])

    button = Input.NONE
    action = Action.NONE
    while action != Action.BUTTON_DOWN or button != Input.BUTTON_B:
        action,button = ReadInput()

    sig = signal.SIGTERM
    # Kill the video player
    KillProcessByName("omxplayer.bin", sig)
    # kill livestreamer
    os.kill(p.pid, sig)

def KillProcessByName(name, sig):
    try:
        omxPid = int(subprocess.check_output(["pidof", name]))
        os.kill(omxPid, sig)
    except subprocess.CalledProcessError:
        print "Unable to close Omxplayer"

def PlayStream(stream):
    global stopLSThread, player
    stopLSThread = False
    Clear()
    url = "twitch.tv/%s" % stream
    print "Loading... %s" % url

    player = subprocess.Popen(['omxplayer', '/tmp/stream'])

    lsThread = threading.Thread(target=ReadWriteStream, args=(url,))
    lsThread.start()

    button = Input.NONE
    action = Action.NONE
    while action != Action.BUTTON_DOWN or button != Input.BUTTON_B:
        action,button = ReadInput()

    stopLSThread = True
    sig = signal.SIGTERM
    KillProcessByName("omxplayer.bin", sig)
    os.kill(player.pid, sig)

    os.unlink(pipeStreamPath)
    MakeFIFOPipe()

def ReadWriteStream(url):
    print "LSThread Start"
    global stopLSThread
    stream = livestreamer.streams(url)
    stream = stream['best']
    fd = stream.open()

    try:
        with open("/tmp/stream", "wb") as f:
            while not stopLSThread:
                data = fd.read(8192)
                f.write(data)
    except IOError as err:
        if err.errno in ACCEPTABLE_ERRNO:
            print "Player closed"
        else:
            print "Error when writing to output: %s" % err

    stopLSThread = False;
    print "LSThread Complete"

def MakeFIFOPipe():
    if os.path.exists(pipeStreamPath):
        return

    try:
        os.mkfifo(pipeStreamPath)
    except OSError, e:
        print "Failed to create FIFO: %s" % e
        exit(0)

def main():
    global topStreams, topGames, myGames, myFollows, streamForGame, lrThreads
    MakeFIFOPipe()
    lrThreads = LRThreads()

    try:
    
        # Streams per game menu
        rowFormat = "{:<10}{:<30}{:<100}{:<15}{:<15}"
        streamTable = Table('', ["Name", "Status", "Viewers", "Followers"], rowFormat)
        streamMenu = Menu(PlayStream, GetStreams, streamTable, streamsForGame, True)

        # Top Games menu
        rowFormat = "{:<10}{:<70}{:<15}{:<15}"
        gameTable = Table('Top Games List', ["Name", "Viewers", "Channels"], rowFormat)
        gameMenu = Menu(streamMenu.Run, GetGames, gameTable, topGames, True)

        # Top Streams menu
        rowFormat = "{:<10}{:<30}{:<50}{:<100}{:<15}"
        topStreamTable = Table('', ["Name", "Game", "Status", "Viewers"], rowFormat)
        topStreamsMenu = Menu(PlayStream, GetTopStreams, topStreamTable, topStreams, True)

        # My followed streams menu
        followedStreamMenu = Menu(PlayStream, GetFollowedStreams, topStreamTable, myFollows, True)

        # MY games menu
        rowFormat ="{:<10}{:<100}"
        myGamesTable = Table('', ["Game"], rowFormat)
        myGamesMenu = Menu(streamMenu.Run, GetMyGames, myGamesTable, myGames, False)

        while 1:
            followedStreamMenu.Run('Followed Stream Menu')
            myGamesMenu.Run('My Games')
            gameMenu.Run('Top Games List')
            topStreamsMenu.Run('Top Streams List')
        return

    except KeyboardInterrupt:
        print "Closing..."
    finally:
        lrThreads.Stop()
        pipe.close()
        os.unlink(pipeStreamPath)
        os.system('stty sane')

if __name__ == "__main__":
    main()
