import requests
import pandas as pd
import numpy as np

urls=list()

file=open('MTA Turnstyle html.txt')  #html text of the links to the MTA data

#parse text
for line in file:
    urls=line.split("href")
for x in urls:
    if 'data/nyct/turnstile' not in x:
        urls.pop(urls.index(x))
for i in range(len(urls)):
    urls[i]='http://web.mta.info/developers/'+urls[i][2:urls[i].index('txt')+3]
    
    
#scrape data from the web and write data to text files
for i in range(0,52):
    res = requests.get(urls[i])
    file = open(urls[i][len(urls[i])-20:], "w")
    file.write(res.text)
    file.close()
    

#read off list of text files
urls=list()
file=open('MTA Turnstyle html.txt')
for line in file:
    urls=line.split("href")
for x in urls:
    if 'data/nyct/turnstile' not in x:
        urls.pop(urls.index(x))
for i in range(len(urls)):
    urls[i]='http://web.mta.info/developers/'+urls[i][2:urls[i].index('txt')+3]


#The collection times for the data don't always line up, so we bin them in 4 hour chunks with this function
def fitintobin(s):    
    if s[0:2]=='01' or s[0:2]=='02' or s[0:2]=='03' or s[0:2]=='00':
        return '00:00:00'
    elif s[0:2]=='05' or s[0:2]=='06' or s[0:2]=='07' or s[0:2]=='04':
        return '04:00:00'
    elif s[0:2]=='09' or s[0:2]=='10' or s[0:2]=='11' or s[0:2]=='08':
        return '08:00:00'
    elif s[0:2]=='13' or s[0:2]=='14' or s[0:2]=='15' or s[0:2]=='12':
        return '12:00:00'
    elif s[0:2]=='17' or s[0:2]=='18' or s[0:2]=='19' or s[0:2]=='16':
        return '16:00:00'
    elif s[0:2]=='21' or s[0:2]=='22' or s[0:2]=='23' or s[0:2]=='20':
        return '20:00:00'
    else:
        return s

#For stations that service many different lines, the list of subway lines can appear in several ways.
# This function deals with these special cases to ensure that the data for each station is aggregated correctly.
def sortLine(row):
    #Times square
    if row['LINENAME']=='ACENGRS1237':
        return '1237ACENQRS'
    #Penn station
    if row['STATION']=='34 ST-PENN STA':
        return '123ACE'
    #Roosevelt
    #Court SQ
    if 'COURT SQ' in row['STATION']:
        return '7EMG'
    return ''.join(sorted(row['LINENAME']))
#The same station can sometimes show up with 2 different names.  
#This function deals with these cases
def sortStation(row):
    if row['STATION']=='ROOSEVELT AVE':
        return '74 ST-BROADWAY'
    if 'COURT SQ' in row['STATION']:
        return 'COURT SQ'
    return row['STATION']

    
#This function creates a pandas dataframe from a text file containing the raw turnstile data             
def createdataframe(i):
    if i<=55:
        data=pd.read_csv(urls[i][len(urls[i])-20:])
        data['DATE']=pd.to_datetime(data['DATE'],format='%m/%d/%Y')
        data.columns=['C/A','UNIT','SCP','STATION','LINENAME','DIVISION','DATE','TIME','DESC','ENTRIES','EXITS']
        data['TIME']=data['TIME'].apply(fitintobin)
        data['STATION']=data.apply(sortStation,axis=1)
        data['LINENAME']=data.apply(sortLine, axis=1)
        data['WEEKDAY']=data['DATE'].apply(lambda x: x.weekday())    
        print(urls[i][len(urls[i])-20:])
    if i>55:
        data=pd.read_csv("m_"+str(urls[i][len(urls[i])-20:]))
        data['STATION']=ata.apply(sortStation,axis=1)
        data['LINENAME']=data.apply(sortLine, axis=1)
        data['DATE']=pd.to_datetime(data['DATE'],format='%m/%d/%Y')
        print("m_"+urls[i][len(urls[i])-20:])
        data['TIME']=data['TIME'].apply(fitintobin)
        data['WEEKDAY']=data['DATE'].apply(lambda x: x.weekday())
    return data

# Create one gigantic frame containing all of the data over the specified range of MTA files.
frames = [ createdataframe(i) for i in range(0,52) ]
data = pd.concat(frames,ignore_index=True)


#Grouping the data by weekday

stations=data['STATION'].unique()
coords=pd.read_csv("TurnstileStationCoords12.16.csv")

#Make one large csv file containing all of the daily medians

#Process the data for a single station
def processStation(s):
    sframes=[processStationandLine(s,l) for l in data[data['STATION']==s]['LINENAME'].unique()]
    return pd.concat(sframes,ignore_index=True)

def processStationandLine(s,l):
    datas=data.sort(['DATE','WEEKDAY','TIME'])[(data['STATION']==s) & (data['LINENAME']==l)&(data['DESC']=='REGULAR')].groupby(['DATE','WEEKDAY','TIME','STATION','LINENAME']).agg({'ENTRIES':np.sum,'EXITS':np.sum})
    datas['dENTRIES']=datas['ENTRIES'].diff()
    datas['dEXITS']=datas['EXITS'].diff()
    datas.loc[abs(datas['dENTRIES'])>200000,'dENTRIES']=np.nan
    datas.loc[abs(datas['dEXITS'])>200000,'dEXITS']=np.nan
    datas.loc[datas['dENTRIES']<0,'dENTRIES']=np.nan
    datas.loc[datas['dEXITS']<0,'dEXITS']=np.nan
    datas.reset_index(inplace=True)  
    datasw=datas.sort(['WEEKDAY','TIME']).groupby(['STATION','LINENAME','WEEKDAY','TIME']).agg({'dENTRIES':np.nanmedian,'dEXITS':np.nanmedian})
    datasw.reset_index(inplace=True)  
    #datasw.to_csv(path_or_buf='dailyaveragesNEW_'+s.replace('/','$')+'_'+l)
    print("Finished station "+s+" "+l)
    total=pd.merge(datasw,coords,on=['STATION','LINENAME'])
    return total

#Combine all of the station data into one file

finframes=[processStation(s) for s in stations]
findata = pd.concat(finframes,ignore_index=True)
findata=findata.drop(findata.columns[8:], axis=1)
findata.to_csv('MedianUsagebyDayDec2014toDec2015')
