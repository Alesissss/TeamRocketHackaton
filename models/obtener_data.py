import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid")
import urllib
import urllib.parse as urlp
import io
import warnings
warnings.filterwarnings("ignore")

LAT = -145.1953
LONG = 60.1598

def get_time_series(start_date,end_date,latitude,longitude,variable):
    """
    Calls the data rods service to get a time series
    """
    base_url = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
    query_parameters = {
        "variable": variable,
        "type": "asc2",
        "location": f"GEOM:POINT({longitude}, {latitude})",
        "startDate": start_date,
        "endDate": end_date,
    }
    full_url = base_url+"?"+ \
         "&".join(["{}={}".format(key,urlp.quote(query_parameters[key])) for key in query_parameters])
    print(full_url)
    iteration = 0
    done = False
    while not done and iteration < 5:
        r=requests.get(full_url)
        if r.status_code == 200:
            done = True
        else:
            iteration +=1
    
    if not done:
        raise Exception(f"Error code {r.status_code} from url {full_url} : {r.text}")
    
    return r.text

def parse_time_series(ts_str):
    """
    Parses the response from data rods.
    """
    lines = ts_str.split("\n")
    parameters = {}
    for line in lines[2:11]:
        key,value = line.split("=")
        parameters[key] = value
    
    
    df = pd.read_table(io.StringIO(ts_str),sep="\t",
                       names=["time","data"],
                       header=10,parse_dates=["time"])
    return parameters, df

# total precipitation [kg m-2]
df_precip = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=-LONG,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf"
            )
        )

# 2-meter above ground temperature [k]
df_tair = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Tair"
            )
        )

# 2-meter above ground specific humidity [kg kg-1]
df_qair = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Qair"
            )
        )

# Soil moisture content (0-100cm) [kg m-2]
df_soil = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:SoilM_0_100cm"
          )
        )

# sensible heat flux [w m-2]
df_Qh = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:Qh"
          )
        )

# ground heat flux [w m-2]
df_Qg = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:Qg"
          )
        )

# total evapotranspiration [kg m-2]
df_Evap = parse_time_series(
            get_time_series(
                start_date="2022-07-01T00", 
                end_date="2025-09-01T00",
                latitude=LAT,
                longitude=LONG,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:Evap"
          )
        )

d = {
    'time': pd.to_datetime(df_precip[1]['time']),
    'Rainf': df_precip[1]['data'],
    'Tair': df_tair[1]['data'],
    'Qair': df_qair[1]['data'],
    'SoilM_0_100cm': df_soil[1]['data'],
    'Qh': df_Qh[1]['data'],
    'Qg': df_Qg[1]['data'],
    'Evap': df_Evap[1]['data']
}

df = pd.DataFrame(data=d)
print(df.shape)
print(df.head())