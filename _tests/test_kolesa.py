from bs4 import BeautifulSoup
import requests
import psycopg2 as pg
import datetime
from random import choice
import time
import re
from sshtunnel import SSHTunnelForwarder
import sys
import os
import uuid

from settings import ssh_conf

#initial settings
# 1. change links
base_url = 'https://kolesa.kz' #5
search_url = base_url + '/cars/' #2
show_url = base_url + '/a/show/' #4
phones_url = base_url + '/a/ajaxPhones' #2

# 2. change logfile name
log_file_prefix = 'logs/cars_' #2

# 3. change db table names
db_table_name = 'kolesa.cars' #3 

#proxies = open('files/_proxies_kz.txt', 'r').read().split('\n')
#useragents = open('files/_useragents.txt', 'r').read().split('\n')
proxy = {}
uagent = {} 

sleep_time_get_request = 0.2 #seconds
sleep_time_while = 7200 #seconds

loop_start = 1
loop_end = 5000

def creatDirectory(directory):
    directory = directory[:directory.rfind('/')]
    if not os.path.exists(directory):
        os.makedirs(directory)
'''
def getProxy():
    return {'https': choice(proxies)}
def getUAgent():
    return {'User-Agent': choice(useragents)}     
'''

def makeGetRequest(url, params, headers):
    # sending requests through proxy is not done here 
    # as kolesa is not blocking(or current cofigurations are enough to avoid blocking)
    try:
        time.sleep(sleep_time_get_request)
        result = requests.get(url=url, params=params, headers=headers)
    except Exception as ex:
        try:
            print("sleep300, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
            time.sleep(300)
            result = requests.get(url=url, params=params, headers=headers)
        except Exception as ex:
            try:
                print("sleep1200, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
                time.sleep(1200)  
                result = requests.get(url=url, params=params, headers=headers)
            except Exception as ex:
                print("blocked, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
                return 'blocked'

    return result.text

def getAdsListPage(page_id):
    url = search_url
    params = {'page':page_id}
    result = makeGetRequest(url=url, params=params, headers=None)
    return result
    
def getAdDetailsPage(ad_id):
    url = show_url + str(ad_id)
    result = makeGetRequest(url=url, params=None, headers=None)
    return result

def getPhones(ad_id):
    url = phones_url
    params = {
        'id': str(ad_id)
    }
    headers = {
        'x-requested-with':'XMLHttpRequest'
    }    
    result = makeGetRequest(url=url, params=params, headers=headers)
    return result

def getListOfAdLinksFromPage(full_page):
    soup = BeautifulSoup(full_page, features="html.parser")
    try:
        ads_section = soup.find_all('div', {'id': 'results'})
        list_of_divs = ads_section[0].find_all('div', {'class': 'a-info-top'})
    except:
        return []    
    list_of_links = []
    for ad in list_of_divs:
        href = ad.find('a', href=True)['href']
        list_of_links.append(base_url + href)
    return list_of_links

def getAdData(ad_id):
    
    ad_page = getAdDetailsPage(ad_id)
    if ad_page == 'blocked':
        return 'blocked'

    ad_link = show_url + str(ad_id)
    
    soup = BeautifulSoup(ad_page, features="html.parser")
    ad_details = soup.find('div', {'class': 'offer'})

    price = re.sub('[\n\t ]', '', ad_details.find('div', {'class': 'offer__price'}).text.strip())
    ad_location = ad_details.find_all('dd', {'class':'value'})[0].text.strip()

    try:
        brand = ad_details.find('h1', {'class': 'offer__title'}).find('span', {'itemprop':'brand'}).text.strip()
    except:
        brand = ''
    try:
        model = ad_details.find('h1', {'class': 'offer__title'}).find('span', {'itemprop':'name'}).text.strip()
    except:
        model = ''
    try:
        year = ad_details.find('h1', {'class': 'offer__title'}).find('span', {'class':'year'}).text.strip()
    except:
        year = ''
    try:
        condition = ad_details.find('div', {'class':'offer__parameters-mortgaged'}).text.strip()
    except:
        condition = 'used'
    try:
        ad_owner = ad_details.find('a', {'class':'shop__info-title'}).text.strip()
    except:
        ad_owner = 'private'

    phones = re.sub('[\{\}\[\]"phones: ]', '', getPhones(ad_id))
    if phones == 'blocked':
        return 'blocked'
    
    descr = ''
    descr_list = ad_details.find_all('dl')
    length = len(descr_list)
    for i in range(1, length):
        descr = descr+descr_list[i].find('dt', {'class': 'value-title'}).text.strip()+':'+descr_list[i].find('dd', {'class': 'value'}).text.strip()
        if i != length-1:
            descr = descr+'|'
    
    descr_detailed = ''
    try:
        descriptions = ad_details.find('div', {'class': 'offer__description'}).find_all('div', {'class': 'text'})
        for d in descriptions:
            descr_detailed = descr_detailed + d.text.strip() + '. '
    except:
        descr_detailed = ''
    descr_detailed = descr_detailed.replace('\n', '').replace('..', '.')
    
    date_db = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    date_kolesa = ad_details.find('span', {'class': 'nb-views'}).next_sibling
    date_kolesa = date_kolesa[date_kolesa.find('с')+1:].strip()
    
    return {
        'ad_id':ad_id,
        'ad_link': ad_link,
        'ad_location': ad_location,
        'ad_owner': ad_owner,
        'phones': phones,
        'price': price,
        'brand': brand,
        'model': model,
        'manufacture_year': year,
        'condition': condition,
        'descr': descr,
        'descr_detailed': descr_detailed,
        'date_kolesa': date_kolesa,
        'date_db': date_db
    }

def test():
    links = getListOfAdLinksFromPage(getAdsListPage(1))
    #links = []

    for i, link in enumerate(links, start=1):
        print(i, link)

    ad_id = links[0].replace(show_url, '')
    print()
    for k, v in getAdData(ad_id).items():
        print("{}: {}".format(k, v))    

##############################################################################

to_sleep = False
'''
while True:
    print('kolesa/cars')
    print("started, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")))
    if to_sleep:
        print("sleep while, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")))
        loop_start = 1
        time.sleep(sleep_time_while) 

    #connecting to server, creating ssh tunnel
    try:
        server = SSHTunnelForwarder(
                (ssh_conf['ssh_ip'], ssh_conf['ssh_port']),
                ssh_private_key=ssh_conf['ssh_private_key'],
                ssh_username=ssh_conf['ssh_user'],
                remote_bind_address=(ssh_conf['remote_bind_address'], ssh_conf['remote_bind_address_port'])
            )
        server.start()
        # if python version > 3.7 set block_on_close = False
        # otherwise server.stop() will hang
        if sys.version_info[0] == 3 and sys.version_info[1] >= 7:
            server._server_list[0].block_on_close = False #2
        ssh_server_started = True    
        print ("server connected")

    except Exception as ex:
        print("server connection error, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
        continue
        ## print Exception to log

    #connecting to db
    try:   
        params = {
                'database': ssh_conf['ssh_db'],
                'user': ssh_conf['ssh_db_user'],
                'password': ssh_conf['ssh_db_pass'],
                'host': ssh_conf['ssh_db_host'],
                'port': server.local_bind_port
        }
        conn = pg.connect(**params)
        cursor = conn.cursor()
        print ("database connected")

    except Exception as ex:
        print("db error, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
        ## print to log
        try:   
            conn = pg.connect(**params)
            cursor = conn.cursor()
            print ("database connected")
        except Exception as ex:
            print("db error, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
            ## print to log
            try:   
                conn = pg.connect(**params)
                cursor = conn.cursor()
                print ("database connected")
            except Exception as ex:
                print("db error, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
                ## print to log
                continue
    
    #making set for ids in db
    ids = set()
    #retrieving ids of already fetched ads from db
    cursor.execute('select ad_id from ' + db_table_name)
    db_ids = cursor.fetchall()    
    for row in db_ids:
        ids.add(row[0])   
    
    creatDirectory(log_file_prefix)
    logfile = open(log_file_prefix + str(datetime.datetime.now().strftime("%Y%m%d_%H"))+".txt", "a")
    commit_counter = 0
    indb_pages = 0
    inpage_ads = 0

    # iterating web site ad pages
    for i in range(loop_start, loop_end):
        inpage_ads = 0
        #get the links of the ads on current page
        links = getListOfAdLinksFromPage(getAdsListPage(i))
        if len(links) == 0:
            print("no ad, page {}".format(i))
            to_sleep = True
            break

        retry = False
        retryCount = 0

        for link in links:
            if not retry:
                ad_id = link.replace(show_url, '')
            elif retryCount < 3:
                retryCount = retryCount+1
            else:
                retry = False
                retryCount = 0
                continue

            if not ids.__contains__(ad_id):
                indb_pages = 0
                try:
                    ad = getAdData(ad_id)
                    cursor.execute("insert into " + db_table_name + " values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", (
                        ad['ad_id'], ad['ad_link'], ad['ad_location'], ad['ad_owner'], ad['phones'], ad['price'], ad['brand'], ad['model'], 
                        ad['manufacture_year'], ad['condition'], ad['descr'], ad['descr_detailed'], ad['date_kolesa'], ad['date_db'], str(uuid.uuid1()) ))
                    #commiting every 5 executes
                    commit_counter = commit_counter+1
                    if commit_counter%5 == 0: 
                        conn.commit()
                    ids.add(ad_id)
                    ad = ''
                    retry = False
                    retryCount = 0

                except Exception as ex:  
                    print("error, {}, page {}, ad {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), i, ad_id, ex))
                    retry = True    
                
            else:
                inpage_ads = inpage_ads+1
                date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                logfile.write("{}, ad {}, page {}, already in db\n".format(date,ad_id, i)) 
        
        if inpage_ads == 20:
            indb_pages = indb_pages + 1
        
        if indb_pages == 5:
            print("go to beginning, {}, page {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), i))      
            to_sleep = True
            break

    try:        
        conn.commit()
        logfile.close()
        server.stop()
    except Exception as ex:
        print("error, while, {}, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), ex))
            
    ssh_server_started = False
    print("finished, {}".format(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")))
    print("----------------------- ")
'''
       
test()    