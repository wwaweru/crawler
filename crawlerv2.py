import re
import sys
import time
import string
import codecs
import smtplib
import requests
import datetime
import unicodedata
from lxml import html
import mysql.connector
from mysql.connector import Error


dateunf = datetime.date.today()
datef = dateunf.strftime('%d-%m-%Y')
# datef = '10-02-2019'
cnf = mysql.connector.connect(host='localhost',
                            database='',
                            user='',
                            password='')
foretable = 'crawler'


add_fore = ("INSERT INTO {table} "
            "(home,away,ftip,ztip,ttip,vtip,mdate,zweight)"
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")

# Step 1: Crawl forebet matches

def forebet():
    fprob=''
    source='forebet'
    add_fore_init = ("INSERT INTO {table} "
            "(home,away,ftip,mdate,fprob,source)"
            "VALUES (%s,%s,%s,%s,%s,%s)")

    cursor = cnf.cursor()
    pageContentfore=requests.get('https://www.forebet.com/en/football-tips-and-predictions-for-today')
    foretree = html.fromstring(pageContentfore.content)

    trowsfore = ((len(foretree.xpath('//*[@class="schema"]/tr'))))
    for i in range(4, trowsfore):
        j=str(i)
        homeraw=foretree.xpath('//*[@class="schema"]/tr['+j+']/td[1]/div/a/span[1]/span/text()')
        try:
            for home in homeraw:
                hometeam=home.encode('utf-8')
        except ValueError:
            pass
        awayraw=foretree.xpath('//*[@class="schema"]/tr['+j+']/td[1]/div/a/span[2]/span/text()')
        try:
            for away in awayraw:
                awayteam=away.encode('utf-8')
        except ValueError:
            pass

        tip=(str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[5]/span/text()')).strip()).replace(("['"),'').replace(("']"),'')
        if tip=='1':
            fprob=((str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[2]/b/text()')).strip()) \
            + str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[2]/text()')).strip()).replace(("['"),'').replace(("']"),'') \
            .replace(']','').replace('[','').replace("'", '')
        elif tip=='X':
            fprob = ((str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[3]/b/text()')).strip()) \
            + str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[3]/text()')).strip()).replace(("['"),'').replace(("']"),'') \
            .replace(']','').replace('[','')
        elif tip=='2':
            fprob = ((str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[4]/b/text()')).strip()) \
            + str(foretree.xpath('//*[@class="schema"]/tr['+j+']/td[4]/text()')).strip()).replace(("['"),'').replace(("']"),'') \
            .replace(']','').replace('[','')
        else:
            fprob=''
        match_data = (hometeam,awayteam,tip,datef,fprob,source)
        try:
            cursor.execute('SELECT home,away FROM zuluDB.crawler WHERE Match(home) against("'+ hometeam +'") ')
            recordset = cursor.fetchall()
            if len(recordset)==0:
                cursor.execute(add_fore_init.format(table=foretable),match_data)
                cnf.commit()
            else:
                # update_results = ("UPDATE {table} SET ftip='" + tip + "', source='" + source + "', fprob='" + fprob + "' WHERE home='" + hometeam + "'")
                update_results=('UPDATE zuluDB.crawler set ftip="' + tip +'",fprob="' + fprob +'", source="' + source +'" WHERE MATCH(home) AGAINST("'+ hometeam +'")')
                print('UPDATE zuluDB.crawler set ftip="' + tip +'",fprob="' + fprob +'", source="' + source +'" WHERE MATCH(home) AGAINST("'+ hometeam +'")')
                cursor.execute(update_results.format(table=foretable))
                cnf.commit()
        except mysql.connector.Error as err:
            print("Error: {}".format(err))
    cursor.close()

def zulubet():
    zprob=''
    add_fore_zulu = ("INSERT INTO {table} "
        "(home,away,ztip,mdate,zweight,zprob,source)"
        "VALUES (%s,%s,%s,%s,%s,%s,%s)")
    cursor = cnf.cursor()
    tipsdate = 'tips-' + datef + '.html'
    tlink = 'http://www.zulubet.com/' + tipsdate
    pageContent=requests.get(tlink)
    tree = html.fromstring(pageContent.content)
    trows = (1+(len(tree.xpath('//*[@class="content_table"]/tr'))))

    for i in range(3, trows):
        j=str(i)
        gweight=str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[8]/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        yweight=str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[8]/font/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        if gweight=='':
            tweight=yweight
        else:
            tweight=gweight
        # tweight = gweight + yweight
        tip=str(tree.xpath('//*[@class="content_table"]/tr['+j+']//font/b/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        if tip=='1':
            zprob = str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[4]/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        elif tip=='X':
            zprob = str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[5]/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        elif tip =='2':
            zprob = str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[6]/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        else:
            zprob=''
        matches = tree.xpath('//*[@class="content_table"]/tr['+j+']/td[2]/text()')
        result=str(tree.xpath('//*[@class="content_table"]/tr['+j+']/td[13]/text()')).replace('[','').replace(']','').replace('"','').replace("'",'')
        source='zulu'
        try:
            for match in matches:
                match=match.encode('utf-8')
                zhome,zaway = match.split(' - ')
                match_data = ((zhome.lstrip()),(zaway.lstrip()),tip,datef,(tweight.lstrip()),zprob,source)
                try:
                    cursor.execute('SELECT home,away FROM zuluDB.crawler WHERE Match(home) against("'+ (zhome.lstrip()) +'") ')
                    recordset = cursor.fetchall()
                    if len(recordset)==0: # Match not in Forebet or has already been played
                        add_fore_zulu = ("INSERT INTO {table} "
                        "(home,away,ztip,mdate,zweight,ftip,zprob,source)"
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)")
                        ftip=''
                        match_data = ((zhome.lstrip()),(zaway.lstrip()),tip,datef,(tweight.lstrip()),ftip,zprob,source)
                        cursor.execute(add_fore_zulu.format(table=foretable),match_data)
                        cnf.commit()
                    elif len(recordset)<>0:
                        update_results=('UPDATE zuluDB.crawler set ztip="' + tip +'",zprob="' + zprob +'", zweight="' + (tweight.lstrip()) +'", result="' + (result.lstrip()) +'", source="' + source +'" WHERE Match(home) AGAINST("'+ (zhome.lstrip()) +'")')
                        print('UPDATE zuluDB.crawler set ztip="' + tip +'",zprob="' + zprob +'", zweight="' + (tweight.lstrip()) +'", result="' + (result.lstrip()) +'", source="' + source +'" WHERE Match(home) AGAINST("'+ (zhome.lstrip()) +'")')
                        cursor.execute(update_results)
                        cnf.commit()
                except mysql.connector.Error as err:
                    print("Error: {}".format(err))
        except ValueError:
            pass
# def send_email():
#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     server.starttls()
#     server.login("atypical.waweru@gmail.com","")
#     server.sendmail()
def turboscore():
    source='turbo'
    add_fore_turbo = ("INSERT INTO {table} "
            "(home,away,ttip,mdate,source)"
            "VALUES (%s,%s,%s,%s,%s)")
    cursor=cnf.cursor()
    turbolink = 'https://www.turboscores.com/Bets.asp?lang=&mtyp=5'
    pageContent=requests.get(turbolink)
    tree=html.fromstring(pageContent.content)
    tdivs = len(tree.xpath('//*[@id="ts_tips"]/div/div/div'))

    def remove_control_chart(s):
        return re.sub(r'\\x..', '', s)

    home=str(tree.xpath('//*[@id="ts_tips"]/div/div/div/span[1]/span[1]/span//text()')).replace('[','') \
    .replace('"','').replace("'",'').replace(']','')
    tip=str(tree.xpath('//*[@id="ts_tips"]/div/div/div/span[2]/span[1]/span//text()')).replace('[','') \
    .replace('"','').replace("'",'').replace(']','')
    away=str(tree.xpath('//*[@id="ts_tips"]/div/div/div/span[1]/span[3]/span//text()')).replace('[','') \
    .replace('"','').replace("'",'').replace(']','')

    for i in range(0, tdivs):
        matchtipn=''
        matchtipw=''
        hometeam=(remove_control_chart(home).split(',')[i]).lstrip()
        awayteam=(remove_control_chart(away).split(',')[i]).lstrip()
        matchtipw=(remove_control_chart(tip).split(',')[i]).lstrip()
        if matchtipw=='Home Win':
            matchtipn='1'
        elif matchtipw=='Away Win':
            matchtipn='2'
        else:
            matchtipn='X'
        homet = hometeam.strip('u')
        awayt = awayteam.strip('u')
        data_teams = (homet,awayt, matchtipn,datef,source)
        print (homet,awayt, matchtipn,datef,source)
        try:
            cursor.execute('SELECT home,away FROM zuluDB.crawler WHERE Match(home) against("'+ hometeam +'") ')
            recordset = cursor.fetchall()
            if len(recordset)==0:
                ztip=''
                ftip=''
                add_fore_turbo = ("INSERT INTO {table} "
                "(home,away,ttip,mdate,ztip,ftip,source)"
                "VALUES (%s,%s,%s,%s,%s,%s,%s)")
                data_teams = (homet,awayt, matchtipn,datef,ztip,ftip,source)
                cursor.execute(add_fore_turbo.format(table=foretable),data_teams)
                cnf.commit()
            else:
                update_results=('UPDATE zuluDB.crawler set ttip="' + matchtipn +'", source="' + source +'" WHERE Match(home) AGAINST("'+ homet +'")')
                print('UPDATE zuluDB.crawler set ttip="' + matchtipn +'", source="' + source +'" WHERE Match(home) AGAINST("'+ homet +'")')
                cursor.execute(update_results)
                cnf.commit()

        except mysql.connector.Error as err:
            print("Error: {}".format(err))

def olbg():
    cursor = cnf.cursor()
    pageContentfore=requests.get('http://www.olbg.com/betting-tips/Football/1')
    foretree = html.fromstring(pageContentfore.content)
    trowsolbg = ((len(foretree.xpath('//*[@id="tipsListingContainer-Match"]/tbody/tr'))))
    source='olbg'
    for i in range(1, trowsolbg):
        j=str(i)
        match=foretree.xpath('//*[@id="tipsListingContainer-Match"]/tbody/tr['+j+']/td[2]/h5/a/text()')
        winner=foretree.xpath('//*[@id="tipsListingContainer-Match"]/tbody/tr['+j+']/td[3]/h4/a/text()')
        for tip in winner:
            for game in match:
                home = ((game).split(" v "))[0]
                away = ((game).split(" v "))[1]
                for tip in winner:
                    otip=str(tip)
                    if home==otip:
                        vtip='1'
                    elif away==otip:
                        vtip='2'
                    elif otip=='Draw':
                        vtip='X'
                    else:
                        vtip=otip
            try:
                cursor.execute('SELECT home,away FROM zuluDB.crawler WHERE Match(home) against("'+ home +'") ')
                recordset = cursor.fetchall()
                if len(recordset)==0:
                    ztip=''
                    ftip=''
                    ttip=''
                    addolbg = ("INSERT INTO {table} "
                        "(mdate,home,away,otip,ztip,ftip,ttip)"
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)")
                    matchdata = (datef,home,away,vtip,ztip,ftip,ttip)
                    cursor.execute(addolbg.format(table=foretable),matchdata)
                    cnf.commit()
                else:
                    update_results=('UPDATE zuluDB.crawler set otip="' + vtip +'", source="' + source +'" WHERE Match(home) AGAINST("'+ home +'")')
                    print('UPDATE zuluDB.crawler set otip="' + vtip +'", source="' + source +'" WHERE Match(home) AGAINST("'+ home +'")')
                    cursor.execute(update_results)
                    cnf.commit()

            except mysql.connector.Error as err:
                print("Error: {}".format(err))

def verifytip():
    cursor = cnf.cursor()
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("atypical.waweru@gmail.com","")
        cursor.execute("SELECT * FROM zuluDB.crawler where ftip<>'' and ztip<>''")
        #  and ttip<>''")
        recordset = cursor.fetchall()
        for row in recordset:
            try:
                prob1 = str(row[10].strip('%'))
                prob2 = str(row[11].strip('%'))
                tip1 = str(row[4])
                tip2 = str(row[5])
                aveProb = str(int(prob1) + int(prob2))
                print ((row)[2] + ' vs ' + (row)[3] + ' -> ' + aveProb + ' ' + tip1 + '' + tip2)
            except ValueError:
                print("Error: {No Value}")
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
    msg=""
    server.sendmail("atypical.waweru@gmail.com", "walter.waweru@gmail.com",msg)
    server.quit()

if __name__ == '__main__':
  
    while True:
        forebet()
        zulubet()
        turboscore()
        verifytip()
        olbg()
        fl = open("logs","w")
        fl.write(str(datetime.datetime.now()) + "\n")
        f = open("crawler.txt", "r")        
        time.sleep(int(f.read()))
