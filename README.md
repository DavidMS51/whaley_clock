# whaley_clock
micro:bit master slave clock application using whaleysans
This clock application is designed to work across multiple micro:bits using the whaleysans font to display 2 digits per micro:bit.
Inspired by and utilising code by David Whale [@whaleygeek] and M Atkinson [multiWingSpan.co.uk]

Uses uses a DS3231 RTC module connected via the microbits I2C port to provide an accuate time
s/w will identify which microbit has the RTC connected and make that the master

micorbits auto configure bases on connections to P0-2, checked at reset only
P0 taken high will display hours  [ 24 hour clock ] 
P1 taken high will display minutes
P0 & P1 taken low will display seconds
P3 taken high will display scrolling time

All micro:bits work from the same code, and you have have as many as you want running at the same time but keep it to one master !
It can take up to a minute for all the micro:bits to sort themsleves out from startup

** updateing RTC time - now added
