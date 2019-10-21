import tkinter as tk
from tkinter import ttk
import threading
import time
from time import strftime
import pyautogui # pip install pyautogui
import random
import numpy as np # pip install numpy
import cv2 # pip install opencv-python-headless
import PIL.ImageGrab as ig # pip install Pillow
import keyboard # pip install keyboard
import win32gui # pip install pywin32
import os
import json
try: import winsound
except: pass

class Pokerbot(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self,None)
        self.parent = None
        self.appRunning = True
        self.logMutex = threading.Lock()
        self.logSize = 0
        self.logStrings = []
        self.escapeEvent = False
        self.paused = False
        self.chrome = None
        self.pokerPos = [0, 0, 0, 0]
        self.settings = {'time_limit':3600, 'sound_alert':True, 'sound_file':'alert.wav'}
        self.lastLog = ""
        
        logframe = ttk.Frame(self)
        logframe.grid(row=0, column=0, sticky="nw") # position and width
        logframe.grid_propagate(False)
        scrollbar = tk.Scrollbar(logframe) # the scroll bar
        self.logtext = tk.Text(logframe, width=55, height=35, state=tk.DISABLED, yscrollcommand=scrollbar.set) # the log box itself
        self.logtext.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.config(command=self.logtext.yview)

        self.title('(You) Pokerbot rev.6')
        self.resizable(width=False, height=False)
        self.protocol("WM_DELETE_WINDOW", self.close)

        # START
        self.load()
        self.run()

    def load(self):
        try:
            with open('settings.json') as f:
                data = json.load(f)
                if 'time_limit' in data or data['time_limit'] > 0: self.settings['time_limit'] = data['time_limit']
                else: self.log("Invalid 'time_limit' value in 'settings.json', using default (3600 seconds)")
                if 'sound_alert' in data and (data['sound_alert'] == True or data['sound_alert'] == False): self.settings['sound_alert'] = data['sound_alert']
                else: self.log("Invalid 'sound_alert' value in 'settings.json', using default (true)")
                if 'sound_file' in data: self.settings['sound_file'] = data['sound_file']
                return True
        except Exception as e:
            print('load(): ', e)
            try:
                with open('settings.json', 'w') as outfile:
                    json.dump(self.settings, outfile)
            except Exception as f:
                print('load(): ', f)

    def alert(self):
        try: winsound.PlaySound(self.settings['sound_file'], winsound.SND_FILENAME | winsound.SND_ASYNC)
        except: os.system('beep -f %s -l %s' % (200,100)) # if not windows OR failed to load the sound file

    def close(self): # called by the app when closed
        self.appRunning = False
        self.destroy()

    def run(self):
        loopThread = threading.Thread(target=self.bot_loop)
        loopThread.setDaemon(True)
        loopThread.start()
        keyboard.add_hotkey('Escape', self.quit)
        keyboard.add_hotkey('F7', self.pause)
        while self.appRunning:
            self.update_log()
            self.update()
            time.sleep(0.04)
            self.escape()

    def update_log(self):
        if not self.appRunning:
            return
        self.logMutex.acquire()
        if len(self.logStrings) > 0:
            self.logtext.configure(state="normal") # state set to normal to write in
            for i in range(0, len(self.logStrings)):
                self.logtext.insert(tk.END, self.logStrings[i]+"\n")
                if self.logSize >= 200: # one call = one line, so if the number of line reachs the limit...
                    self.logtext.delete(1.0, 2.0)
                else: # else, increase
                    self.logSize += 1
            self.logtext.configure(state="disabled") # back to read only
            self.logtext.yview(tk.END) # to the end of the text
            del self.logStrings[:] # delete the stored lines
        self.logMutex.release()

    def log(self, text, timestamp=True): # add the text to the queue, to be printed in the windows
        if not self.appRunning or text == self.lastLog:
            return
        self.lastLog = text
        self.logMutex.acquire()
        if timestamp: # append to our list of line (see update_log() for more)
            self.logStrings.append("[" + strftime("%H:%M:%S") + "] " + text)
        else:
            self.logStrings.append(text)
        print(text)
        self.logMutex.release()

    def escape(self):
        if self.escapeEvent:
            self.close()

    def quit(self):
        self.escapeEvent = True

    def pause(self):
        self.paused = not self.paused
        if self.paused: self.log('Pause')
        else: self.log('Resume')

    # https://pyautogui.readthedocs.io/en/latest/cheatsheet.html#mouse-functions
    def resetMouse(self): # to move the mouse out of the pokker buttons (they blink if you hover over them)
        pyautogui.moveTo(random.randint(self.chrome[0], self.chrome[0]+20), random.randint(self.chrome[1], self.chrome[1]+20))
        self.delay(30)

    def click(self, x, y, n=1):
        pyautogui.click(x=x, y=y, clicks=n)

    def randomClickArea(self, minX, minY, maxX, maxY, n=1):
        self.click(random.randint(minX, maxX), random.randint(minY, maxY), n)

    def randomClick(self, area, n=1): # area is [X, Y, W, H]
        if len(area) >= 4:
            self.click(random.randint(area[0], area[0]+area[2]), random.randint(area[1], area[1]+area[3]), n)

    # return true if a and b are close (within the diff value)
    def areClose(self, a, b, diff):
        if abs(a - b) <= diff:
            return True
        return False

    # print a string listing the cards in the array
    def printCards(self, array):
        string = "Card(s): "
        letters = ["c", "d", "h", "s"]
        cards = ["Joker", "???", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for i in range(0, len(array)):
            string += cards[array[i][0]]
            if array[i][0] > 1:
                string += letters[array[i][1]]
            if i < len(array)-1:
                string += ", "
        self.log(string)

    # print the hand strenght
    def printHand(self, value):
        if value == -1:
            self.log("Error, invalid hand")
            return
        hands = [
            "No pairs",
            "One pair",
            "Two pairs",
            "Three of a kind",
            "Straight",
            "Flush",
            "Full House",
            "Four of a kind",
            "Straight Flush",
            "Five of a kind",
            "Royal Straight Flush"
        ]
        self.log(hands[value])

    # calculate the hand strenght
    def checkHand(self, cards):
        if len(cards) != 5:
            return -1
        joker = False
        # same suit?
        suit = -1
        result = True
        for i in range(0, 5):
            if cards[i][0] == 0: # joker
                joker = True
                continue
            if suit == -1:
                suit = cards[i][1]
                continue
            if suit != cards[i][1]:
                result = False
                break
        if result: # is at least a flush
            values = []
            for i in range(0, 5):
                if cards[i][0] == 0:
                    continue
                values.append(cards[i][0])
            values = sorted(values)
            if values[0] >= 10:
                # royal straight flush
                return 10
            if values == range(min(values), max(values)+1):
                # straightflush
                return 8
            # flush
            return 5
        else:
            # check straight
            values = []
            for i in range(0, 5):
                if cards[i][0] == 0:
                    continue
                values.append(cards[i][0])
            values = sorted(values)
            if values == range(min(values), max(values)+1):
                # straight
                return 4
            else:
                same = [0]*15
                best = 0
                pairs = 0
                threes = 0
                for i in values:
                    same[i] += 1
                for i in range(0, len(same)):
                    if same[i] > best:
                        best = same[i]
                    if same[i] == 3:
                        threes += 1
                    if same[i] == 2:
                        pairs += 1
                if best == 4:
                    if joker:
                        # five of a kind
                        return 9
                    # four of a kind
                    return 7
                elif best == 3:
                    if joker:
                        # four of a kind
                        return 7
                    if pairs == 1:
                        # full house
                        return 6
                    # three of a kind
                    return 3
                elif best == 2:
                    if pairs == 2:
                        if joker:
                            # full house
                            return 6
                        else:
                            # two pairs
                            return 2
                    if joker:
                        # three of a kind
                        return 3
                    # pair
                    return 1
        if joker:
            # pair
            return 1
        # no pair
        return 0

    # return the multiplier for each possible hand (royal straigth flush is x250 for example)
    def getWinMultiplier(self, value):
        if value == -1:
            return 1
        hands = [0, 0, 1, 1, 3, 4, 10, 20, 25, 60, 250]
        return hands[value]

    # return a new deck (13x4 cards, true means the card is in the deck)
    def initDeck(self):
        deck = []
        for i in range(0, 13):
            deck .append([True, True, True, True])
        return deck

    # reduce the value in the deck for each card provided
    def updateDeck(self, deck, cards):
        for i in cards:
            if i[0] > 1:
                deck[i[0]-2][i[1]] = False
        return deck

    # read the card on the poker table (DOUBLE UP GAME)
    def readTableDoubleUp(self, array):
        self.log("Reading the Poker table...")
        screen = self.getScreen(True)
        result = []
        for i in range(0, len(array)):
            for j in range(0, len(array[i])):
                elem = self.searchCardImage(array[i][j], screen, 0.80)
                if elem[0] != -1:
                    dontAppend = False
                    for k in range(0, len(result)):
                        if self.areClose(result[k][2][0], elem[0], 1) and self.areClose(result[k][2][1], elem[1], 1):
                            dontAppend = True
                            if elem[4] > result[k][2][4]:
                                result[k] = [i, j, elem]
                            break
                    if not dontAppend:
                        result.append([i, j, elem])
        return result

    # for the double up game: 
    # return probability of a lower card, a draw and a higher card (card must have been removed from the deck beforehand)
    def nextCardProba(self, deck, card):
        count = [0, 0, 0]
        total = 0
        for i in range(0, len(deck)):
            for j in deck[i]:
                if j == True:
                    if card[0]-2 > i: # lower card count
                        count[0] += 1
                    elif card[0]-2 == i: # equal card count
                        count[1] += 1
                    else: # higher card count
                        count[2] += 1
                    total += 1
        total = total * 1.0
        for i in range(0, 3):
            count[i] = 100 * count[i] / total
        return count

    # click on the card to hold it
    def holdCard(self, card):
        print("hold the card ", card[0], ", ", card[1])
        looping = True
        while looping:
            self.randomClick(card[2])
            if self.waitImageRegion("keep.png", [card[2][0]+10, card[2][1]+10, card[2][2]-30, card[2][3]-30], 10, 0.85)[0] != -1:
                looping = False

    # deal game:
    # determine which card to hold and call holdCard
    def handAction(self, cards, score):
        joker = 0
        # act depending on hand strength
        if score == 0:
            # check same suit
            suit = [0]*4
            for i in cards:
                if i[0] == 0:
                    self.holdCard(i)
                    joker = 1
                else:
                    suit[i[1]] += 1
            # check consecutive
            cons = []
            temp = cards
            for i in range(0, len(temp)-1):
                for j in range(i+1, len(temp)):
                    if temp[i][0] > temp[j][0]:
                        temp[i][0], temp[j][0] = temp[j][0], temp[i][0]
            for i in range(joker, len(temp)-1):
                array = [temp[i]]
                usedJoker = False
                avoid = 0
                for j in range(i+1, len(temp)):
                    if temp[j][0] == temp[j-1][0] + 1:
                        array.append(temp[j])
                        continue
                    elif temp[j][0] == temp[j-1][0] + 2:
                        if joker == 1 and not usedJoker:
                            usedJoker = True
                            array.append(temp[j])
                            continue
                        break
                    elif temp[j][0] == temp[j-1][0]:
                        avoid += 1
                        continue
                    else:
                       break
                if len(array) > 1:
                    cons.append(array)
                    i += len(array)-1+avoid
            # decide
            countSuit = 0
            idSuit = None
            countCons = 0
            idCons = None
            for i in range(0, 4):
                if suit[i] > countSuit:
                    countSuit = suit[i]
                    idSuit = i
            countSuit += joker
            for i in cons:
                if len(i) > countCons:
                    countCons = len(i)
                    idCons = i
            if idSuit is None and idCons is None:
                return
            if countSuit >= countCons:
                for i in cards:
                    if idSuit == i[1]:
                        self.holdCard(i)
            else:
                for i in idCons:
                    self.holdCard(i)
        elif score > 3:
            for i in cards:
                self.holdCard(i)
        else:
            same = [0]*15
            for i in cards:
                if i[0] > 1:
                    same[i[0]] += 1
                else:
                    self.holdCard(i)
            for j in range(0, len(same)):
                if same[j] > 1:
                    for i in cards:
                        if i[0] == j:
                            self.holdCard(i)

    def getScreen(self, pokerMode = False):
        if pokerMode: screen = ig.grab(bbox=[self.pokerPos[0],self.pokerPos[1],self.pokerPos[2],self.pokerPos[3]]) # for the poker table
        else: screen = ig.grab(bbox=[self.chrome[0],self.chrome[1],self.chrome[0]+self.chrome[2],self.chrome[1]+self.chrome[3]]) # get the chrome screenshot
        screen = np.array(screen, dtype='uint8').reshape((screen.size[1],screen.size[0],3)) # convert for opencv
        return cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    def searchCardImage(self, template, screen, threshold=0.85):
        if template is None or screen is None:
            return [-1]
        
        w, h = template.shape[::-1] # get the size
        res = cv2.matchTemplate(screen,template,eval('cv2.TM_CCOEFF_NORMED')) # template matching
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val > threshold:
            return [max_loc[0]+self.pokerPos[0], max_loc[1]+self.pokerPos[1], w, h, max_val]
        else:
            return [-1]

    def searchImage(self, filename, threshold=0.85):
        template = cv2.imread("data/" + filename,0) # read the image file
        if template is None:
            return [[-1]]

        img = self.getScreen() # get the screen
        
        w, h = template.shape[::-1] # get the size
        res = cv2.matchTemplate(img,template,eval('cv2.TM_CCOEFF_NORMED')) # template matching
        loc = np.where(res >= threshold) # 0.9 is the default threshold

        coor = []
        for pt in zip(*loc[::-1]):
            coor.append([pt[0]+self.chrome[0], pt[1]+self.chrome[1], w, h]) # get all the matches and add the window position

        if len(coor) == 0:
            return [[-1]] # return -1 if empty
        return coor

    def searchImageRegion(self, filename, region, threshold=0.85):
        if not isinstance(region, list) or len(region) < 4:
            return [[-1]]
        res = self.searchImage(filename, threshold)
        if res[0][0] == -1:
            return res
        ok = []
        for i in range(0, len(res)):
            if res[i][0] >= region[0] and res[i][1] >= region[1] and res[i][0]+res[i][2] <= region[0]+region[2] and res[i][1]+res[i][3] <= region[1]+region[3]:
                ok.append(res[i])
        if len(ok) == 0:
            return [[-1]]
        return ok

    def findImage(self, filename, threshold=0.85):
        if self.searchImage(filename, threshold)[0][0] != -1:
            return True
        return False

    def clickImage(self, filename, dClick = False):
        elems = self.searchImage(filename, 0.85)
        if elems[0][0] != -1:
            if dClick: self.randomClick(elems[0], 2)
            else: self.randomClick(elems[0])
            return True
        return False

    def waitImage(self, filename, max, threshold=0.85):
        for i in range(0, max):
            elems = self.searchImage(filename, threshold)[0]
            if elems[0] != -1:
                return elems
            self.delay(100)
        return [-1]

    def waitImageRegion(self, filename, region, max, threshold=0.85):
        for i in range(0, max):
            elems = self.searchImageRegion(filename, region, threshold)[0]
            if elems[0] != -1:
                return elems
            self.delay(100)
        return [-1]

    def waitAndClickImage(self, filename, max):
        elems = self.waitImage(filename, max)
        if elems[0] != -1:
            self.randomClick(elems)
            return True
        return False

    def waitImageList(self, files, max, threshold=0.85):
        for i in range(0, max):
            for j in files:
                if self.searchImage(j, threshold)[0][0] != -1:
                    return True
            self.delay(100)
        return False

    def checkForChrome(self):
        hwnd = win32gui.GetForegroundWindow() # get the focused window
        if win32gui.GetWindowText(hwnd).find("- Google Chrome") != -1: # check if google chrome
            if self.chrome == None:
                self.log("Chrome detected")
            size = win32gui.GetWindowRect(hwnd) # update the size
            self.chrome = [size[0], size[1], size[2]-size[0], size[3]-size[1]]
            return True
        else:
            if self.chrome != None:
                self.chrome = None
                self.log("Chrome not found")
            return False

    # check if the poker table is in view, return true if that's the case and update pokerPos value (global screen region of the card area)
    def checkPokerTable(self):
        topleft = self.searchImage("board_01a.png")[0]
        bottomright = self.searchImage("board_02.png")[0]
        if topleft[0] == -1:
            topleft = self.searchImage("board_01b.png")[0]
        if topleft[0] == -1 or bottomright[0] == -1:
            self.pokerPos = [0, 0, 0, 0]
            return False
        self.pokerPos = [topleft[0]+18, topleft[1]+156, topleft[0]+302, topleft[1]+276] # rect(18, 156, 284, 120)
        return True

    # read the cards on the poker table (DEAL GAME)
    def readTable(self, array):
        self.log("Reading the Poker table...")
        screen = self.getScreen(True)
        result = []
        ignored = []
        for i in range(0, len(array)):
            for j in range(0, len(array[i])):
                elem = self.searchCardImage(array[i][j], screen, 0.80) # search if the card is on screen
                if elem[0] != -1: # if it is
                    dontAppend = False
                    for k in range(0, len(result)): # compare with existing result
                        if self.areClose(result[k][2][0], elem[0], 1) and self.areClose(result[k][2][1], elem[1], 1):
                            dontAppend = True
                            if elem[4] > result[k][2][4]:
                                ignored.append(result[k])
                                result[k] = [i, j, elem]
                            break
                    if not dontAppend: # and decide to keep the match or not
                        result.append([i, j, elem])
                    else:
                        ignored.append([i, j, elem])
        # mismatch protection
        # if incomplete hand and we have discarded matches :
        while len(result) < 5 and len(ignored) > 0:
            best = [0, ignored[0][2][4]]
            for i in range(1, len(ignored)): # we pick the best ignored match
                if ignored[i][2][4] > best[1]:
                    best[0] = i
                    best[1] = ignored[i][2][4]
            result.append(ignored[best[0]]) # add in the result
            del ignored[best[0]]
        return result

    def randomDelay(self, min, max): # ms
        time.sleep(random.randint(min, max)/1000)

    def delay(self, t): # ms
        time.sleep(t/1000)

    def loadImage(self, filename):
        return cv2.imread("data/" + filename,0)

    def resizeImage(self, image, x, y):
        return cv2.resize(image, (x,y), interpolation = cv2.INTER_AREA)

    # resize the card images from array2 into array1
    def resizeCards(self, array1, array2, x, y):
        for i in range(0, len(array2)):
            temp = []
            for j in range(0, len(array2[i])):
                temp.append(self.resizeImage(array2[i][j], x, y))
            array1.append(temp)

    # load the card image files in memory
    def loadCards(self, cards):
        buffer = self.loadImage("00x.png") # joker
        if buffer is None:
            return False
        cards.append([buffer])
        cards.append([])
        letters = ["c", "d", "h", "s"]
        for i in range(2, 15):
            array = []
            for j in range(0, 4):
                if i < 10: filename = '0{}{}.png'.format(i, letters[j])
                else: filename = '{}{}.png'.format(i, letters[j])
                buffer = self.loadImage(filename) # card
                if buffer is None:
                    return False
                array.append(buffer)
            cards.append(array)
        return True

    def bot_loop(self): # main loop
        state = -1 # state machine
        lastState = 0 # previous state
        cards = []
        resizedCards = []
        doubleupCards = []
        gain = 0
        if not self.loadCards(cards):
            self.log("Failed to load cards")
            return
        self.resizeCards(resizedCards, cards, 51, 72)
        self.resizeCards(doubleupCards, cards, 72, 100)
        deck = self.initDeck()
        doubleupChain = 0
        win = -1
        previousHand = []
        choice = False
        error = False
        startTime = time.time()
        self.log("Click on google chrome to start")
        self.log("GBF must be set to the smallest game size")
        self.log("Time limit is set to {} second(s)".format(self.settings['time_limit']))
        self.log("F7 to toggle the Pause, Escape to stop")
        self.log("_______________________________________________________", False)
        while self.appRunning:
            self.delay(100)
            if time.time() - startTime > self.settings['time_limit']:
                self.log("Time limit reached")
                return
            if self.paused:
                continue
            if error:
                self.log("An error occured")
                return
            if self.checkForChrome():
                if self.findImage("capcha_en.png", 0.7):
                    self.log("_______________________________________________________", False)
                    self.log("Capcha, press F7 to resume")
                    if self.settings['sound_alert']: self.alert()
                    self.paused = True
                    continue
                elif self.checkPokerTable(): # and if poker table
                    if state != -1: # keep track of our previous state, in case the user pause the bot and go do something else
                        lastState = state
                    if state == -1: # -1 is the undetermined state
                        if self.findImage("yes_en.png") and self.findImage("no_en.png"):
                            test = self.readTable(resizedCards)
                            self.printCards(test) # print the cards
                            score = self.checkHand(test) # get the result
                            self.printHand(score) # and print it
                            if len(self.readTable(resizedCards)) == 5:
                                state = 1
                            elif len(self.readTable(doubleupCards)) > 0:
                                state = 3
                            continue
                        elif self.findImage("high_en.png") and self.findImage("low_en.png"):
                            if len(deck) == 0:
                                deck = initDeck()
                            state = 3
                            continue
                        elif self.findImage("deal_en.png") or self.findImage("ok_en.png"):
                            state = 0
                            continue
                        else:
                            state = lastState
                            continue
                    elif state == 0: # starting state (deal game)
                        self.resetMouse()
                        self.log("_______________________________________________________", False)
                        self.log("Deal screen")
                        if self.clickImage("deal_en.png"): # click the deal button
                            self.resetMouse()
                            self.delay(100)
                        if self.waitImage("ok_en.png", 30)[0] != -1: # if the ok button is visible on screen
                            # initialize the stuff
                            gain -= 1
                            errorCount = 0
                            win = -1
                            currentCards = []
                            self.log("Current gain: {}".format(gain))
                            # read the table (10 try max)
                            while errorCount < 10:
                                currentCards = self.readTable(resizedCards)
                                if len(currentCards) != 5:
                                    errorCount += 1
                                else:
                                    break
                            if errorCount < 10:
                                self.resetMouse()
                                self.printCards(currentCards) # print the cards
                                score = self.checkHand(currentCards) # get the result
                                self.printHand(score) # and print it
                                self.handAction(currentCards, score) # choose which card to keep
                                previousHand = currentCards # store our current card (to keep track later)
                                self.clickImage("ok_en.png") # click ok
                                self.resetMouse()
                                if self.waitImageList(["yes_en.png", "no_en.png", "deal_en.png"], 40): # and wait for the cards
                                    state = 1
                                continue
                            else:
                                self.log("Error: Can't read the table, resetting...")
                                state = -1
                                continue
                    elif state == 1: # deal result, after clicking ok
                        self.log("_______________________________________________________", False)
                        self.log("Deal screen: Result")
                        errorCount = 0
                        currentCards = []
                        while errorCount < 10: # same thing again
                            currentCards = self.readTable(resizedCards)
                            if len(currentCards) != 5:
                                errorCount += 1
                            else:
                                break
                        if errorCount < 10:
                            self.resetMouse()
                            clicked = False
                            # click preemptively
                            if self.clickImage("yes_en.png"):
                                state = 2
                                clicked = True
                            elif self.clickImage("deal_en.png"):
                                state = 0
                                clicked = True
                            # check result
                            self.printCards(currentCards)
                            score = self.checkHand(currentCards)
                            self.printHand(score)
                            win = self.getWinMultiplier(score) # store our multiplier
                            array = [] # compare our current cards with the previous one, add the non duplicate in previousHand
                            for i in currentCards:
                                found = False
                                for j in previousHand:
                                    if i[0] == j[0] and i[1] == j[1]:
                                        found = True
                                        break
                                if not found:
                                    array.append(i)
                            previousHand += array
                            waiting = True
                            while waiting and not clicked:
                                if self.findImage("yes_en.png") and self.findImage("no_en.png"): # we won
                                    state = 2
                                    waiting = False
                                    self.clickImage("yes_en.png") # I need to update this part
                                elif self.findImage("deal_en.png"): # we lost
                                    state = 0
                                    waiting = False
                            continue
                        else:
                            self.smartlog("Error: Can't read the table, resetting...")
                            state = -1
                            continue
                    elif state == 2: # preparing for the double up
                        self.log("_______________________________________________________", False)
                        self.log("Starting the Double Up game")
                        doubleupChain = 0
                        state = 3
                        deck = self.initDeck()
                    elif state == 3: # double up game
                        self.log("_______________________________________________________", False)
                        self.log("Double Up screen")
                        self.resetMouse()
                        self.waitImageList(["high_en.png", "low_en.png"], 40)
                        if self.findImage("high_en.png") and self.findImage("low_en.png"): # if high and low buttons on screen
                            if win < 1: # if the win value is lesser than 1, we didn't come here the right way
                                win = 1
                            errorCount = 0
                            currentCards = []
                            while errorCount < 10: # read the table
                                currentCards = self.readTableDoubleUp(doubleupCards)
                                if len(currentCards) != 1: # only one card on screen this time
                                    errorCount += 1
                                else:
                                    break
                            if errorCount < 10:
                                deck = self.updateDeck(deck, currentCards) # update the table
                                proba = self.nextCardProba(deck, currentCards[0]) # get the probability
                                self.log("{:.1f}% Low, {:.1f}% Draw, {:.1f}% High".format(proba[0], proba[1], proba[2]))
                                button = ""
                                if proba[0] > proba[2]: # if the "low" probability is higher than the "high" probability
                                    button = "low_en.png" # we click the low button
                                    choice = False
                                    self.log("I choose Low")
                                else:
                                    button = "high_en.png" # else the high button
                                    choice = True
                                    self.log("I choose High")
                                self.clickImage(button) # click
                                self.resetMouse()
                                previousHand = currentCards # store the card
                                doubleupChain += 1
                                state = 4
                                self.waitImageList(["yes_en.png", "no_en.png", "deal_en.png"], 40)
                                continue
                            else:
                                self.smartlog("Error: Can't read the table, resetting...", 3)
                                state = -1
                                continue
                    elif state == 4: # double up result
                        if self.findImage("yes_en.png") and self.findImage("no_en.png"): # same thing
                            self.log("_______________________________________________________", False)
                            self.log("Double Up screen: Result")
                            errorCount = 0
                            currentCards = []
                            while errorCount < 10:
                                currentCards = self.readTableDoubleUp(doubleupCards)
                                if len(currentCards) < 1: # we should have 2 cards on the screen (the previous one and the new one) but we check for < 1
                                    errorCount += 1
                                else:
                                    break
                            if len(currentCards) == 1: # if only one card on screen, a desync happened, back to state = 3
                                state = 3
                                continue
                            if errorCount < 10:
                                array = [] # same as for state = 1, we compare with the previous card, add the new one to the list
                                for i in currentCards:
                                    if i[0] != previousHand[0][0] or i[1] != previousHand[0][1]:
                                        array.append(i)
                                        break
                                result = choice # check if the result is high, low or draw
                                draw = True 
                                if array[0][0] != previousHand[0][0]:
                                    result = array[0][0] > previousHand[0][0]
                                    draw = False
                                if choice == result: # if we won 
                                    self.log("Chain: {}".format(doubleupChain))
                                    if(doubleupChain >= 10): # chain reached 10, back to the start
                                        state = 1
                                        continue
                                    futureDeck = deck
                                    deck = self.updateDeck(futureDeck, array) # update the deck
                                    proba = self.nextCardProba(futureDeck, array[0]) # get the probability for the next round
                                    button = ""
                                    self.resetMouse()
                                    if win <= 128 or proba[0] > 90 or proba[2] > 90: # decide if we continue or not
                                        button = "yes_en.png"
                                        state = 3
                                    else:
                                        button = "no_en.png"
                                        state = 0
                                    self.clickImage(button) # and press the button
                                    self.resetMouse()
                                    # update the log while waiting
                                    if not draw: # if we didn't get a draw, double the win
                                        win = win * 2
                                        self.log("Current multiplier is x{}".format(win))
                                        if state == 0:
                                            gain += win
                                            win = 0
                                    self.log("{:.1f}% Low, {:.1f}% Draw, {:.1f}% High".format(proba[0], proba[1], proba[2]))
                                    # wait button
                                    self.waitImageList(["yes_en.png", "no_en.png", "deal_en.png"], 40)
                                    continue
                        elif self.findImage("deal_en.png"): # deal button on screen, it's over
                            self.log("_______________________________________________________", False)
                            self.log("Double Up screen: Result")
                            self.log("Game over")
                            state = 0
                else:
                    self.log("No poker table found")
                    state = -1

Pokerbot()