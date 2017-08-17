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

# To set the RTC hold button A at reset until clock apears 
# use button a to advance hours
# use button b to advance minutes
# hold button a & b down at the same time to write the new time to the RTC

from microbit import *
import radio

#setup global variables 
radio.config(group=7)
TICK_RATE = 1000                                # ticks in a second
HOURS, MINS, SECS, SCROLL = 'h','m','s','r'     # config IDs
next_tick = 0                                   # init tick counter
mst = False                                     # master microbit flag
upd = False                                     # radio update - used to avoide multiple updates

addr = 0x68
buf = bytearray(7)


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
    
#change RTC time setting  - only runs at reset on master
def set_time():
    global hours, mins 
    but_a = True
    but_b = True
    while True:
        if button_a.is_pressed() and button_b.is_pressed():
            display.show(Image.YES)
            sleep(2000)
            break
        elif button_a.is_pressed():
            if but_a:
                display.show('H', clear=True)
                hours -=1
                but_a = False
                but_b = True
            hours +=1
            if hours > 23:
                hours = 0
            display.show(img(hours))
        elif button_b.is_pressed():
            if but_b:
                display.show('M', clear=True)
                mins -=1
                but_b = False
                but_a = True
            mins +=1
            if mins > 59:
                mins = 0 
            display.show(img(mins))
        sleep(250)
    
    # to set time manually    
    # s,m,h,w,dd,mm,yy - array format for time
    
    # t=bytes([0,58,0,01,17,08,17])  # coment out following line, uncoment this line
    
    t = bytes([0,mins,hours,01,01,01,17])
    for i in range(0,7):
        i2c.write(addr, bytes([i,dec2bcd(t[i])]), repeat=False)        
    
    return
    
#identify which config the microbit will be
def read_config():
    global config
    
    if pin2.read_digital() == 1:
        config = SCROLL
    elif pin0.read_digital() == 1:
        config = HOURS
    elif pin1.read_digital() == 1:
        config = MINS
    else:
        config = SECS

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
        print('Time update ok')
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
        if secs%6 == 0:
            if secs != 0:
                display.scroll(str(hours)+':'+str(mins)+'   ', wait=False, delay=180)
    
        
# unless master microbit check for time re-cal
def check_time_radio():
    if mst == False:
        try:
            t = radio.receive()
            if t is not None:
                set_clock(t)
        except:
            print("radio error reseting")
            radio.off()
            radio.on()
            
#sent time cal to all slave microbits        
def pass_on_time():
    t = "%02d:%02d:%02d" % (hours, mins, secs)
    radio.send(t)

# check if 1 second since last 'tick'
# also every minute check RTC and update
def check_update():
    global next_tick, upd
    global hours, mins, secs
    now = running_time()
    if now >= next_tick:
        tick()
        
        if mst == True:
            if secs == 5 and upd == False:
                try:
                    hours,mins,secs = get_time() 
                    upd = True
                    pass_on_time()
                except:   
                    upd = False
            else:
                upd = False
                
        next_tick = now + TICK_RATE
        refresh_display()
 
 
        
# main running routine
# setup
read_config()
radio.on()
# global hours, mins, secs
# global mst
try:
    hours,mins,secs = get_time()
    print('master')
    mst = True
    pass_on_time()
except:
    print('Not Master')
    hours,mins,secs = 0,0,0
 
# check to RTC update request 
if button_a.is_pressed():
    display.show(Image.ALL_CLOCKS, loop=True, delay=150, wait=False)
    while button_a.is_pressed():
        sleep(100)    
    set_time()
#main running loop    
while True:
    check_time_radio()
    check_update()
   
 
