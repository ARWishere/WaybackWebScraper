# generates wayback links
from datetime import datetime, timedelta
from waybackpy import WaybackMachineCDXServerAPI


# returns list of snapshots, with 3 per time interval
# input: url to get wayback links, start_date timestamp, end_date timestamp, interval in days between snapshots
def collect_urls(main_url, start_date, end_date, interval):
    url = main_url
    user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
    cdx = WaybackMachineCDXServerAPI(url, user_agent, start_timestamp=start_date, end_timestamp=end_date)
    collected_snapshots = []
    seeking_stamp = start_date
    for item in cdx.snapshots():
        # add to usable snapshots if the timestamp were seeking is >= seeking one
        # we only want one for every month, so the seeking time stamp will change
        # to the first of the next month upon addition to the collection
        if item.timestamp >= seeking_stamp and item.statuscode.startswith("2"):
            # add the snapshot to the list
            collected_snapshots.append(item)
            seeking_stamp = to_timestamp(to_datetime(seeking_stamp) + timedelta(days=interval))

    return collected_snapshots

def to_datetime(timestamp):
    return datetime(int(timestamp[:4]), int(timestamp[4:6]), int(timestamp[6:8]))

def to_timestamp(datetime_obj):
    dt_string = str(datetime_obj)
    # datetime object str in the format: yyyy-mm-dd hhmmss
    # convert to a str timestamp we used previously
    return dt_string[:4] + dt_string[5:7] + dt_string[8:10] + "000000"



