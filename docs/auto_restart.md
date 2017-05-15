This page is for a workaround to restart your bot(s).
_(Restarting is superior over reconnecting in case of stability for crashes)_

# MAC OS
1. Open your terminal
Just open it and you finished step 1

2. Create a new apple script
Heres an example to start and restart  bots (in separate folders) adjust it for your needs. (paths, start commands, restart timer, ...)

You can create a start file (if you are lazy :P) and a restart file or just one for both needs

Start script:

        tell application "Terminal"
  activate
  do script "cd desktop" in selected tab of the front window  #edit your path
  do script "cd bots" in selected tab of the front window     #edit your path
  do script "cd bot1" in selected tab of the front window     #edit your path
  do script "python pokecli.py" in selected tab of the front window   #start with your parameters

  #add more bots
  delay 10
  tell application "System Events"
    keystroke "t" using {command down} #open a new tab for next bot
  end tell
  delay 5
  do script "cd .." in selected tab of the front window
  do script "cd bot2" in selected tab of the front window
  do script "python pokecli.py" in selected tab of the front window
  #copy this part for the amount you need
       end tell

restart:

        repeat

  delay 1200  #timer in seconds
  tell application "Terminal"
    activate

    tell application "System Events"
      keystroke "c" using {control down} #close the bot
    end tell
    delay 3
    do script "clear" in selected tab of the front window #not needed just for nice view
    delay 3
    do script "python pokecli.py" in selected tab of the front window #restart with parameters

                #copy for the amount of bots
    delay 10
    tell application "System Events"
      keystroke "ö" using {command down} #going to the previous tab
    end tell
    delay 3

    tell application "System Events"
      keystroke "c" using {control down}
    end tell
    delay 3
    do script "clear" in selected tab of the front window
    delay 3
    do script "python pokecli.py" in selected tab of the front window

               #copy for the amount of bots
    tell application "System Events"
      keystroke "ä" using {command down} #moving the the last tab
    end tell
    delay 3

          end tell

                end repeat
               
 
 # For any other linux distribution
 
 > You can use the this script to make your bot auto-restart
 
 ```
 #!/usr/bin/bash
while true ; do
		#Add your bot start command after this comment
		
		echo "If you want to completely the restart process now, press Ctrl+C before the time is up!"
		echo "Restarting bot in 2 minute" 
		sleep 1m
		echo "Restarting bot in 1 minute"
		sleep 30s
		echo "Restarting bot in 30 seconds"
		sleep 10s
		echo "Restarting bot in 20 seconds"
		sleep 10s
		echo "Restarting bot in 10 seconds"
		sleep 5s  
		echo "Restarting bot in 5 seconds"
		sleep 1s
		echo "Restarting bot in 4 seconds"
		sleep 1s
		echo "Restarting bot in 3 seconds"
		sleep 1s
		echo "Restarting bot in 2 seconds"
		sleep 1s
		echo "Restarting bot in 1 seconds"
		sleep 1s
		echo "Restarting now !"
done

```

You just need to add your command to start the bot after the comment

And after you need to do this:
```
chmod 755 <scriptname>
```
If you get an error like this:
```
-bash: ./loop.sh: /usr/bin/bash^M: bad interpreter: No such file or directory

```
You need to convert the script in dos

```
dos2unix scriptname.sh
```
