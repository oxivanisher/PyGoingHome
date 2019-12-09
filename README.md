# PyGoingHome
This script uses the transport.opendata.ch API to calculate travel time
(and when to start). Also it caches the queries and fetches new
information every 10 minutes to not hit the [rate limiting](https://timetable.search.ch/api/help).

## Locations
Configure your locations in config/locations.yml like so if you i.e. live
on the mountain of Weissenstein and work at the swiss parliament:
```yaml
---

home: Weissensteinstrasse, 4515 Oberdorf
work: Bundesplatz 3, 3005 Bern
```
