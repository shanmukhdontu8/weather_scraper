import requests
from datetime import datetime,timedelta
import pytz
import pprint
from dateutil import parser
import calendar

cal = calendar.TextCalendar()
pp = pprint.PrettyPrinter(indent=1)

def get_location_search(query):
    url = "https://api.weather.com/v3/location/search?apiKey=d522aa97197fd864d36b418f39ebb323&format=json&language=en-IN&query={}".format(query)
    response = requests.get(url)
    if response.status_code != 200:
        return []
    response = response.json()
    data = zip(response["location"]["address"],response["location"]["latitude"],response["location"]["longitude"],[pytz.timezone(x) for x in response["location"]["ianaTimeZone"]]) 

    return list(data)

def get_weather_date(date,lat,long,timezone = None, num_days = 1):
    lat = round(lat,2)
    long = round(long,2)
    now = datetime.today().astimezone(timezone)
    days_left = num_days
    data = []
    if date <= now:
        date_diff = now - date
        url = "https://dsx.weather.com/wxd/v2/PastObsAvg/en_IN/{}/{}/{},{}?api=7bb1c920-7027-4289-9c96-ae5e263980bc".format(date.strftime("%Y%m%d"),min(num_days,abs(date_diff.days)+1),lat,long)
        res = requests.get(url)
        
        if res.status_code == 200:
            res = res.json()
            data.extend(
                [{"temp_hi":x["Temperatures"]["highC"],"temp_lo":x["Temperatures"]["lowC"], "date" : date + timedelta(i)} for i,x in  enumerate(res)]
            )
        days_left = num_days - min(num_days,abs(date_diff.days)+1)
    

    if days_left > 0:
        start_dt = date if date > now else (now+timedelta(1)) 
        end_dt = start_dt + timedelta(days_left-1)
        url = "https://api.weather.com/v1/geocode/{}/{}/almanac/daily.json?apiKey=d522aa97197fd864d36b418f39ebb323&end={}&start={}&units=m".format(lat,long,end_dt.strftime("%m%d"),start_dt.strftime("%m%d"))
        res = requests.get(url)

        if res.status_code == 200:
            res = res.json()["almanac_summaries"]
            data.extend(
                [{"temp_hi":x["avg_hi"],"temp_lo":x["avg_lo"], "date": start_dt + timedelta(i)} for i,x in enumerate(res)]
            )

    return data

def get_turbo_data(lat,long):
    lat = round(lat,2)
    long = round(long,2)
    url = "https://api.weather.com/v2/turbo/vt1dailyForecast?apiKey=d522aa97197fd864d36b418f39ebb323&format=json&geocode={}%2C{}&language=en-IN&units=m".format(lat,long)
    res = requests.get(url)
    data = []
    if res.status_code == 200:
        res = res.json()["vt1dailyForecast"]
        data = zip(res["day"]["temperature"],res["day"]["phrase"],res["day"]["windSpeed"],res["night"]["temperature"],res["night"]["phrase"],res["night"]["windSpeed"],res["validDate"])
        data = [{"validDate":parser.parse(x[6]),"day":{"temperature":x[0],"phrase":x[1],"windSpeed":x[2]},"night":{"temperature":x[3],"phrase":x[4],"windSpeed":x[5]}} for x in data]
    return data

def get_turbo_data_hourly(lat,long):
    lat = round(lat,2)
    long = round(long,2)

    url = "https://api.weather.com/v2/turbo/vt1hourlyForecast?apiKey=d522aa97197fd864d36b418f39ebb323&format=json&geocode={}%2C{}&language=en-IN&units=m".format(lat,long)
    res = requests.get(url)
    data = []
    if res.status_code == 200:
        res = res.json()["vt1hourlyForecast"]
        data = zip(res["processTime"],res["temperature"],res["windSpeed"])
        data = [{"processTime":parser.parse(x[0]),"temperature":x[1],"windSpeed":x[2]} for x in data]
    
    return data

def get_turbo_data_15_mins(lat,long):
    lat = round(lat,2)
    long = round(long,2)

    url = "https://api.weather.com/v2/turbo/vt1fifteenminute?apiKey=d522aa97197fd864d36b418f39ebb323&format=json&geocode={}%2C{}&language=en-IN&units=m".format(lat,long)
    res = requests.get(url)
    data = []
    if res.status_code == 200:
        # import ipdb; ipdb.set_trace()
        res = res.json()["vt1fifteenminute"]
        data = zip(res["processTime"],res["temperature"],res["windSpeed"])
        data = [{"processTime":parser.parse(x[0]),"temperature":x[1],"windSpeed":x[2]} for x in data]
    
    return data


def get_5_day(lat,long):
    data = get_turbo_data(lat,long)
    return data[:5]

def get_10_day(lat,long):
    data = get_turbo_data(lat,long)
    return data[:10]

def get_today(lat,long):
    data = get_turbo_data(lat,long)
    return [data[0]]

def get_weekends(lat,long):
    data = get_turbo_data(lat,long)

    data = list(filter(lambda x: x["validDate"].weekday() >= 5, data))
    return data

def get_month(year, month, lat, long, timezone = None):
    _, days = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1, tzinfo = timezone)
    data = get_weather_date(start_date, lat, long, num_days = days, timezone = timezone)
    return data

def print_calender(year, month, lat, long, timezone = None, width = 12):
    start_week, num_days = calendar.monthrange(year, month)
    start_date = datetime(year, month, 1, tzinfo = timezone)    
    data = get_weather_date(start_date, lat, long, num_days=num_days, timezone = timezone)

    print(cal.formatmonthname(year,month, 7*(width+1)-1))
    print("\n")
    print(cal.formatweekheader(width))

    min_strs = [" ".join(["Min :",str(x["temp_lo"] if x["temp_lo"] else "")+ u"\u00b0C"]).center(width) for x in data]
    max_strs = [" ".join(["Max :",str(x["temp_hi"] if x["temp_hi"] else "")+ u"\u00b0C"]).center(width) for x in data]
    print("\n")

    if start_week > 0:
        min_strs = ["".center(width)]*start_week + min_strs
        max_strs = ["".center(width)]*start_week + max_strs
    if len(min_strs)%7 != 0:
        min_strs = min_strs + ["".center(width)]*(7-len(min_strs)%7)
        max_strs = max_strs + ["".center(width)]*(7-len(min_strs)%7)

    for i,dates in enumerate(cal.monthdays2calendar(year,month)):
        min_str = " ".join(min_strs[i*7:(i+1)*7])
        max_str = " ".join(max_strs[i*7:(i+1)*7])
        print(cal.formatweek(dates,width))
        print(max_str)
        print(min_str)
        print("\n")

def print_dates(data, width = 20):
    print("|".join(map(lambda x: x.center(width), ["Date","High Temp","Low Temp"])))
    print("+".join( ["-"*width]*3))
    for x in data:
        date_str = x["date"].strftime("%Y/%m/%d").center(width)
        
        for key in ["temp_lo","temp_hi"]:
            if not x[key]:
                x[key] = ""

        low_temp = (str(x["temp_lo"])+ u"\u00b0C").center(width)
        high_temp = (str(x["temp_hi"])+ u"\u00b0C").center(width)
        print("|".join([date_str, high_temp, low_temp]))

def print_turbo_data(data, temp_width = 15, phrase_width = 40):
    total_width = 2*temp_width + phrase_width + 2
    print("||".join(map(lambda x: x.center(total_width) if x != "Date" else x.center(20), ["Date","Day","Night"])))
    print("++".join(["-"*20,"-"*total_width, "-"*total_width]))
    sub_header_str = "|".join(["Temp".center(temp_width),"Comment".center(phrase_width),"Wind Speed".center(temp_width)])
    sub_header_dash = "+".join(["-"*temp_width,"-"*phrase_width,"-"*temp_width])
    print("||".join([" "*20,sub_header_str, sub_header_str]))
    print("++".join(["-"*20,sub_header_dash, sub_header_dash]))

    for x in data:
        date_str = x["validDate"].strftime("%Y/%m/%d").center(20)

        for key1 in ["day","night"]:
            for key2 in ["temperature","phrase","windSpeed"]:
                if not x[key1][key2]:
                    x[key1][key2] = ""

        day_str = "|".join([(str(x["day"]["temperature"])+u"\u00b0C").center(temp_width),x["day"]["phrase"].center(phrase_width),(str(x["day"]["windSpeed"])+" km/h").center(temp_width)])
        night_str = "|".join([(str(x["night"]["temperature"])+u"\u00b0C").center(temp_width),x["night"]["phrase"].center(phrase_width),(str(x["night"]["windSpeed"])+" km/h").center(temp_width)])

        print("||".join([date_str,day_str,night_str]))

def print_date_time(data, width = 30):
    print("|".join(map(lambda x: x.center(width), ["Datetime","Temperature","Wind speed"])))
    print("+".join( ["-"*width]*3))

    for x in data:
        date_str = x["processTime"].strftime("%Y/%m/%d, %I:%M:%S %p").center(width)
        
        for key in ["temperature","windSpeed"]:
            if not x[key]:
                x[key] = ""

        temp_str = (str(x["temperature"])+"\u00b0C").center(width)
        wind_str = (str(x["windSpeed"])+" km/h").center(width)
        
        print("|".join([date_str,temp_str,wind_str]))
