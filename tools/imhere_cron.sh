#!/bin/bash
# Things crash. 
# Instead of having to get up and fix it,
# would like for wife to fix herself,
# and I'll read about it later. 

# Ok, so how shall I do this? I think there can be a cron job that could monitor logs. 
# I need for the wernicke, if the server is connected, every minute or 5 submit a test thing, and if the response don't come back, it's dead and not really connected. 
# If the wernicke stops decoding, that's a sign that it is dead, restart script
# Handle serial port fuck ups. If the wernicke blocks at opening serial port, it's dead, reboot pi. 

# I also considered handling a lot of the monitoring from christine.py. Just like, ask each thread, you alive? 

# Or I could log heartbeat stuff to all the logs. The cron will tail the logs and tell if it's alive. 

# leaning towards adding function to christine.py

# No, now I'm going to have everything that I want monitored log to one log file, and this script will parse it and take certain actions
# So, I can't think of anything else other than wernicke that has ever messed up randomly, so for now this is just to reboot pi when wernicke fucks up

# also this will handle properly when the script is not running
#* * * * * /root/imhere_cron.sh > /dev/null 2> /dev/null
#make sure to chmod 700

cd /root
time_now="$(date +%s)"
time_wernicke="$(tail -n 200 /root/logs/imhere.log | grep wernicke.run | tail -n 1 | cut -d '.' -f 3)"
time_elapsed="$(( time_now - time_wernicke ))"
if [[ "$time_elapsed" -gt "300" ]]; then
    systemctl -q is-active christine.service || echo "It is now $time_now. Wernicke looks dead. Rebooting now!" >> /root/logs/imhere.log; /sbin/reboot
else
    echo "Looks fine!" >> /root/logs/imhere.log
fi
