# microbit clock application, using WhaleySans font to show 2 digits per microbit
# David Saul copyright 2017 @david_ms, www.meanderingpi.wordpress.com
# Inspired by utilising code by David Whale [@whaleygeek] and M Atkinson [multiWingSpan.co.uk]
# Available under MIT License via github.com/DavidMS51

# this version devloped to use a 2331 RTC module connected via the I2C port
# s/w will identify which microbit has the RTC connected and make that the master
# microbit with p0 taken high will display hours  [ 24 hour clock ] 
# microbit with p1 taken high will display minutes
# microbit with p0 & 1 taken low will display seconds
# microbit with p3 taken high will display scrolling time

# All microbit work from the same code, and you have have as many as you want
# running at the same time but keep it to one mast !
# It can take up to a minute for all the microbit to sort themsleves out from startup

# updateing RTC time - have not written that code yet
# currently you have to do it manually by enabling the set_time call in
# global variable init section of the code

from microbit import *
import radio

#setup global variables 
radio.config(group=7)
TICK_RATE = 1000                                # ticks in a second
HOURS, MINS, SECS, SCROLL = 'h','m','s','r'     # main counting variables
next_tick = 0                                   # init tick counter
mst = False                                     # master microbit flag
upd = False                                     # update flag

addr = 0x68
buf = bytearray(7)
#set_time(0,42,22,3,14,6,2017)

#I2C read and write code
def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units
    
def get_time():
    i2c.write(addr, b'\x00', repeat=False)
    buf = i2c.read(addr, 7, repeat=False)
    ss = bcd2dec(buf[0])
    mm = bcd2dec(buf[1])
    if buf[2] & 0x40:
        hh = bcd2dec(buf[2] & 0x1f)
        if buf[2] & 0x20:
            hh += 12
    else:
        hh = bcd2dec(buf[2])
    wday = buf[3]
    DD = bcd2dec(buf[4])
    MM = bcd2dec(buf[5] & 0x1f)
    YY = bcd2dec(buf[6])+2000
    print(DD,MM,YY,hh,mm,ss,wday)
    return hh,mm,ss
    
def set_time(s,m,h,w,dd,mm,yy):
    t = bytes([s,m,h,w,dd,mm,yy-2000])
    for i in range(0,7):
        i2c.write(addr, bytes([i,dec2bcd(t[i])]), repeat=False)
    return

#identify which config the microbit will be

def read_config():
    global config
    
    if pin2.read_digital() == 1:
        config = SCROLL
        print('SCROLL display')
    elif pin0.read_digital() == 1:
        config = HOURS
        print('HOURS display')
    elif pin1.read_digital() == 1:
        config = MINS
        print('MINUTES display')
    else:
        config = SECS
        print('SECONDS display')

# Image cade for 2 digit display options

FONT = ( # WhaleySans font, 2x5 digits only
("99","99","99","99","99"),
("09","09","09","09","09"),
("99","09","99","90","99"),
("99","09","99","09","99"),
("90","90","99","09","09"),
("99","90","99","09","99"),
("99","90","99","99","99"),
("99","09","09","09","09"),
("99","99","00","99","99"),
("99","99","99","09","99")
)

def img(n):
    lg = FONT[int(n/10)]
    rg = FONT[int(n%10)]
    c = ""
    for r in range(5):
        c += lg[r] + "0" + rg[r]
        if r != 4:
            c += ':'
    return Image(c)


def set_clock(t):
    global hours, mins, secs
    #hh:mm:ss\n
    try:
        t2 = t.strip()
        hours, mins, secs = t2.split(':')
        hours = int(hours)
        mins = int(mins)
        secs = int(secs)
    except:
        print("Invalid time set:%s" % str(t))

# Create counting logic    
def tick():
    global hours, mins, secs
    secs += 1
    if secs >= 60:
        secs = 0
        mins += 1
        if mins >= 60:
            mins = 0
            hours += 1
            if hours >= 24:
                hours = 0

#update the microbit display depenind on the config option    
def refresh_display():
    if config == HOURS:
        display.show(img(hours))
    elif config == MINS:
        display.show(img(mins))
    elif config == SECS:
        display.show(img(secs))
    elif config == SCROLL:
        # This option needs a bit more work to avoid upsetting the wider opperation
        # The scroll command has to be run in the background to avoid slowing everything down
        # To avoid unsightly jumps the scroll command only runs every 6 seconds
        # Also you can get a jump a secs = 0 so this is jumped as well
        if secs%6 == 0:
            if secs != 0:
                display.scroll(str(hours)+':'+str(mins)+'   ', wait=False, delay=180)
    
#def check_time_usb():
#    t = uart.readline()
#    if t is not None:
 #       set_clock(t)
  #      radio.send(t)
        
# unless master microbit check for time re-cal
def check_time_radio():
    if mst == False:
        try:
            t = radio.receive()
            if t is not None:
                set_clock(t)
        except:
            # reset radio on error
            print("radio reset")
            radio.off()
            radio.on()
            
#sent time cal to all slave microbits        
def pass_on_time():
    t = "%02d:%02d:%02d" % (hours, mins, secs)
    print('Sending time update')
    radio.send(t)

#check if 1 second since last 'tick'
#also every minute check RTC and update
def check_update():
    global next_tick, upd
    global hours, mins, secs
    now = running_time()
    if now >= next_tick:
        tick()
        
        if mst == True:
            if secs == 5 and upd == False:
                print ('calibrating the RTC')
                try:
                    hours,mins,secs = get_time()
                    print ('RTC update good')
                    upd = True
                    pass_on_time()
                except:
                    print('RTC update fail')    
                    upd = False
            
            else:
                upd = False
                
        next_tick = now + TICK_RATE
        refresh_display()
 
 
        
#main running routine
def run():
    #set things up and check it this is the master microbit or a slave
    read_config()
    radio.on()
    global hours, mins, secs
    global mst
    try:
        hours,mins,secs = get_time()
        print('master identified')
        mst = True
        pass_on_time()
    except:
        print('Not Master, setting default values')
        hours,mins,secs = 0,0,0
    
    #main running loop    
    while True:
        #check_time_usb()
        check_time_radio()
        check_update()
 
run()
