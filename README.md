# PyGoingHome
This script uses the transport.opendata.ch API to calculate travel time
(and when to start) in Switzerland. Also it caches the queries and fetches new
information every 10 minutes to not hit the [rate limiting](https://timetable.search.ch/api/help).

## Locations
Configure your locations in config/locations.yml like so if you i.e. live
on the mountain of Weissenstein and work at the swiss parliament:
```yaml
---

home: Weissensteinstrasse, 4515 Oberdorf
work: Bundesplatz 3, 3005 Bern
```

## Arduino
The arduino display project in `arduino/` is based on source code from
[Drone Mesh - DIY Wireless Youtube Subscriber Counter 2018 // ESP8266 Subscriber Counter](https://www.youtube.com/watch?v=yfDWCga7iP4).
The attached `LiquidCrystal.zip` is also a reupload, but it was difficult to find the correct
version of this library.
