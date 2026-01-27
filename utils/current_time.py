import datetime
import pytz

def get_current_time():
    dt = datetime.datetime.now(tz= pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata'))
    return dt.replace(microsecond=0)