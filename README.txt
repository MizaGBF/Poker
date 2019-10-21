##### (You) Pokerbot - README #####
- This script requires python 3.6 or higher
  https://www.python.org/downloads/

##### INFORMATIONS #####
- The game must be set to the smallest size (first "diamond" on the game bottom bar, or go in the settings)
- Only compatible with the english language (for now)
- The capcha detection system is NOT tested (I never ran the bot that long)

##### INSTALLATION #####
- Some python modules must be installed to run this script, follow those steps (for Windows):
1) Start Menu > Search cmd > open the command prompt
2) Type 'pip'. If you see a bunch of options appear, go to step 4). Else, if the command isn't found, go to step 3).
3) Either your python installation has an issue (example, you have two versions installed) or your python folder isn't in your system path. Search where python is installed (example in my case: C:\Python36 ) and now, everytime you must input a command, you'll add '<the path to python>\python.exe -m' before (example: 'pip install numpy' becomes 'C:\Python36\python.exe -m pip install numpy' in my previous example)
4) Install those modules with those commands (Right click to paste in cmd):
    pip install pyautogui
    pip install numpy
    pip install opencv-python-headless
    pip install Pillow
    pip install keyboard
    pip install pywin32

##### USAGE #####
- click gbfpoker.pyw and start a poker game in granblue fantasy

##### SETTINGS #####
- Edit settings.json with a notepad :
time_limit = time limit in second before stopping (default: 3600)
sound_alert = to enable the sound alert (default: true)
sound_file = sound file used by the capcha alert (WINDOWS ONLY) (default: "alert.wav")

A new file is generated if it's missing.

##### HOTKEYS #####
- Escape : Stop and exit the script
- F7 : toggle Pause/Resume (the script will finish its current action before pausing)

##### ISSUE #####
- If the bot doesn't start at all, try renaming the file to 'gbfpoker.py' (without W), this will open an additional command prompt. Or you can open a command prompt of your own (like during the installation) and type 'python gbfpoker.pyw' to run directly and see any message.
- If the image recognition doesn't work, you might have to retake some screenshots in the data folder.