import datetime
import json
import requests
import argparse
import logging
from bs4 import BeautifulSoup
from tabulate import tabulate
from slack_client import slacker

FORMAT='[%(asctime)-15s] %(message)s'
# logging.basicConfig(format=FORMAT,level=logging.DEBUG,filename='bot.log',filemode='a')

URL='https://www.mohfw.gov.in/'
SHORT_HEADERS=['Sno','State','In','Fr','Cd','Dt']
FILE_NAME='FILE_NAME'
contents_extracted=lambda row:[x.text.replace('\n','')for x in row]

def save(x):
    with open(FILE_NAME,'w') as f:
        json.dump(x,f)

def load():
    res={}
    with open(FILE_NAME,'r') as f:
        res=json.load(f)
    return res

if __name__=='__main__':

    parser=argparse.ArgumentParser()
    parser.add_argument('--states',default=',')
    args=parser.parse_args()
    states=args.states.split(',')
    current_time = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    info = []

try:
    resp=requests.get(URL).content
    soup=BeautifulSoup(resp,'html.parser')
    header=contents_extracted(soup.tr.find_all('th'))

    stats=[]
    all_rows=soup.find_all('tr')
    for row in all_rows:
        stat=contents_extracted(row.find_all('td'))
        if stat:
            if len(stat)==5:
                stat=['',*stat]
                stats.append(stat)
                break
            elif any([s.lower() in stat[1].lower() for s in states]):
                stats.append(stat)
    past_data=load()
    cur_data={x[1]:{current_time: x[2:]}for x in stats}

    changed=False

    for state in cur_data:
        if state not in past_data:
            info.append(f'New_State {state} got corona virus : {cur_data[state][current_time]}')
            past_data[state]={}
            changed=True
        else:
            past=past_data[state]['latest']
            cur=cur_data[state][current_time]
            if past!=cur:
                print("changed")
                changed=True
                info.append(f'Change for {state}:{past}->{cur}')

    events_info=''
    for event in info:
        logging.warning(event)
        events_info+='\n - '+ event.replace("'","")

    if changed:
        for state in cur_data:
                past_data[state]['latest']=cur_data[state][current_time]
                past_data[state][current_time]=cur_data[state][current_time]
        save(past_data)

        table=tabulate(stats,headers=SHORT_HEADERS,tablefmt='grid')
        slack_text=f'Please Find Summary for India below:\n{events_info}\n```{table}```'
        print(slack_text)
        print("hello1224")
        slacker()(slack_text)
except Exception as e:
    logging.exception("Oops There\'s an Issue With ur Corona Script")
    slacker()(f'Exception Occured:[{e}]')
    print(e)
