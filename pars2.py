import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('mydatabase.db')          
cursor=conn.cursor()

def delete_tables(cursor):
    try:
        cursor.execute('drop table cinema')
    except sqlite3.OperationalError:
        print('Такой таблицы    нет')
    try:
        cursor.execute('drop table cinema_halls')
    except sqlite3.OperationalError:
        print('Такой таблицы нет')    
    try:
        cursor.execute('drop table films')
    except sqlite3.OperationalError:
        print('Такой таблицы нет')    
    try:
        cursor.execute('drop table sessions')
    except sqlite3.OperationalError:
        print('Такой таблицы нет')    

def create_cinema(cursor):
    try:
        cursor.execute('''CREATE TABLE cinema(
                        id integer PRIMARY KEY,
                        name text NOT NULL)''')
    except sqlite3.OperationalError:
        print('Ошибка! Такая таблица уже существует')
        
def create_cinema_halls(cursor):
    try:
        cursor.execute("""CREATE TABLE cinema_halls(
                    id integer PRIMARY KEY,
                    cinema_id integer Not NULL,
                    website_id integer NULL,
                    name text NOT NULL,
                    address text NOT NULL,
                    metro text NULL,
                    phone text NULL,
                    FOREIGN KEY (cinema_id) REFERENCES cinema(id)
                    )""")
    except sqlite3.OperationalError:
        print('Ошибка! Такая таблица уже существует')

def create_films(cursor):
    try:
        cursor.execute("""CREATE TABLE films(
                    id integer PRIMARY KEY,
                    website_id integer NULL,
                    name text NOT NULL,
                    duration text NULL,
                    genres text NULL
                    )""")
    except sqlite3.OperationalError:
        print('Ошибка! Такая таблица уже существует')
        
def create_sessions(cursor):
    try:
        cursor.execute("""CREATE TABLE sessions(
                    id integer PRIMARY KEY,
                    film_id integer Not NULL,
                    hall_id integer Not NULL,
                    date date NOT NULL,
                    time time NOT NULL,
                    FOREIGN KEY (film_id) REFERENCES films(id),
                    FOREIGN KEY (hall_id) REFERENCES cinema_halls(id)
                    )""")
    except sqlite3.OperationalError:
        print('Ошибка! Такая таблица уже существует')
        
def create_tables(cursor):
    create_cinema(cursor)
    create_cinema_halls(cursor)
    create_films(cursor)
    create_sessions(cursor)
    
def add_cinemas(cursor):
    try:
        cursor.execute("insert into cinema values (1, 'КАРО')")
        cursor.execute("insert into cinema values (2, 'КИНОМАКС')")
        conn.commit()
    except sqlite3.IntegrityError:
        print('Ошибка! id не уникален')

def remove_all(string):
    pattern = re.compile(r'[А-Яа-яёЁ0-9 ]+')
    return pattern.findall(string)[0].strip()

def find_all_theaters_KARO(theatres):
    dicti = {}
    metro_class = 'cinemalist__cinema-item__metro__station-list__station-item'
    for theater in theatres:
        dicti[theater.findAll('h4')[0].text.strip()] = {
            'metro': [remove_all(i.text) for i in theater.findAll('li', class_=metro_class)], 
            'address': theater.findAll('p')[0].text.split('+')[0].strip(),
            'phone': '+' + theater.findAll('p')[0].text.split('+')[-1].strip(),
            'data-id': theater['data-id']}
    return dicti

def film_id_get(name,films):
    for el in films:
        if name==el[2]:
            return el[0]
    for el in films:
        if (name in el[2]) or (el[2] in name):
            return el[0]

def parsing_karo(cursor):
    url = "https://karofilm.ru"
    url_theaters = url + "/theatres"        
    r = requests.get(url_theaters)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        theatres = soup.findAll('li', class_='cinemalist__cinema-item')
        karo_theatres = find_all_theaters_KARO(theatres)
    else:
        print("Страница не найдена")
    id_=1
    for key,item in karo_theatres.items():
        try:
            metro=', '.join(item['metro'])
            if metro:
                metro="'"+metro+"'"
            else:
                metro='NULL'
            elements=[id_,1,item['data-id'],key,item['address'],metro,item['phone']]
            cursor.execute("insert into cinema_halls values ({},{},{},'{}','{}',{},'{}')".format(*elements))
            id_+=1
        except sqlite3.IntegrityError:
            print(f'Ошибка! id({id_}) не уникален')
            break       
    films_all_class='afisha-item'
    r = requests.get(url)
    if r.status_code==200:
        films_all_parser=BeautifulSoup(r.text,'html.parser')
        all_films_list=films_all_parser.findAll('div',class_=films_all_class)
    else:
        print('Страница не найдена')        
    id_=1
    for element in all_films_list:
        data_id=element['data-id']
        name=element.findAll('h3')[0].text.strip()
        duration=element.findAll('span')[0].text
        try:
            genres='"'+element.findAll('p',class_='afisha-genre')[0].text+'"'
        except IndexError:
            genres='NULL'
        try:
            name=name.replace('\"','\'')
            cursor.execute(f'insert into films values ({id_},{data_id}, "{name}", "{duration}", {genres})')
            id_+=1
        except sqlite3.IntegrityError:
            print(f'Ошибка! id({id_}) не уникален')
            break     
    films_class='cinema-page-item__schedule__row'
    table_class='cinema-page-item__schedule__row__board-row'
    left_class=table_class+'__left'
    rignt_class=table_class+'__right'
    date_class='widget-select'
    id_=1
    for theater in karo_theatres:
        dates={}
        url_theater_id=url_theaters+'?id='+karo_theatres[theater]['data-id']
        r = requests.get(url_theater_id)
        if r.status_code==200:
            date_parser=BeautifulSoup(r.text,'html.parser')
            date_list=date_parser.findAll('select',class_=date_class)[0]
            date_list=[i['data-id'] for i in date_list.findAll('option')]
            for date in date_list: 
                url_theater_id_date=url_theater_id+'&date='+date
                r = requests.get(url_theater_id_date)
                session={}
                if r.status_code==200:
                    films_parser=BeautifulSoup(r.text,'html.parser')
                    films_list=films_parser.findAll('div',class_=films_class)
                    for film in films_list:
                        name=film.findAll('h3')
                        if name:
                            name=name[0].text.split(', ')
                            session_time={}
                            session_time['age']=name[1]
                            for i in film.findAll('div',class_=table_class):
                                time_D=i.findAll('div',class_=left_class)[0].text.strip()
                                time=i.findAll('div',class_=rignt_class)[0].findAll('a')
                                time=[j.text for j in time]
                                session_time[time_D]=time
                                for time_element in time:
                                    film_id=film_id_get(name[0].replace('\"','\''),cursor.execute(f'select * from films').fetchall())
                                    hall_id=cursor.execute(f'select id from cinema_halls where name=\'{theater}\'').fetchall()[0][0]
                                    values=[id_,film_id,hall_id,date,time_element,'NULL']
                                    cursor.execute("insert into sessions values ({},{},{},'{}','{}')".format(*values))
                                    id_+=1
                            session[name[0]]=session_time
                else:
                    print('Такой даты нет, url=',url_theater_id_date)
                dates[date]=session
        else:
            print('Такого кинотеатра нет, url=',url_theater_id)
        karo_theatres[theater]['dates']=dates       

def get_id_films(cursor):
    id1=cursor.execute('select max(id) from films').fetchall()[0][0]
    if id1:
        return id1+1
    else:
        return 1
def get_id_sessions(cursor):
    id2=cursor.execute('select max(id) from sessions').fetchall()[0][0]
    if id2:
        return id2+1
    else:
        return 1
def get_id_cinema_halls(cursor):
    id_=cursor.execute('select max(id) from cinema_halls').fetchall()[0][0]
    if id_:
        return id_+1
    else:
        return 1
    

def parse_cities_kinomax():
    url_kinomax="https://kinomax.ru/"
    r = requests.get(url_kinomax)
    if r.status_code==200:
        kinomax_parser=BeautifulSoup(r.text,'html.parser')
        cities=kinomax_parser.find('select', class_='form-control km-control').findAll('option')
        cities=[[item['value'],item.text] for item in cities[1:]]
        return cities
    else:
        print('Сайт не найден')

def parse_halls_kinomax(id_):
    url_kinomax="https://kinomax.ru/?city="+id_
    r = requests.get(url_kinomax)
    if r.status_code==200:
        kinomax_parser=BeautifulSoup(r.text,'html.parser')
        halls=kinomax_parser.find('div',class_='d-flex flex-wrap w-80 pt-2').findAll('a')
        halls=[[item['href'],item.text] for item in halls]
        return halls
    else:
        print('Сайт не найден')
        
def parse_date_kinomax(url,cursor,website_id,name,id_):
    url_kinomax="https://kinomax.ru"+url
    r = requests.get(url_kinomax)
    if r.status_code==200:
        kinomax_parser=BeautifulSoup(r.text,'html.parser')
        dates=kinomax_parser.find('div', class_="d-flex fs-09 schedule-dates-panel").findAll('div')
        dates=[item['data-date'] for item in dates]
        address=kinomax_parser.find('div', class_='d-flex fs-10').text.strip()
        cursor.execute(f"insert into cinema_halls values ({id_},3,{website_id},'{name}','{address}',NULL,NULL)") 
        return dates
    else:
        print('Сайт не найден')

def parse_sessions_kinomax(url,cursor,id1,id2,id_,date):
    url_kinomax="https://kinomax.ru"+url
    r = requests.get(url_kinomax)
    if r.status_code==200:
        kinomax_parser=BeautifulSoup(r.text,'html.parser')
        films=kinomax_parser.findAll('div',class_='d-flex border-bottom-1 border-stack film')
        for film in films:
            name=film.find('div',class_='w-70').text.strip()
            if not(name in [el[0] for el in cursor.execute('select name from films').fetchall()]):
                duration=re.search('\d+ ч.',film.findAll('div',class_='w-70')[1].text)
                if duration:
                    duration=duration.group()
                else:
                    duration=''
                duration=duration+' '+re.search('\d+ мин.',film.findAll('div',class_='w-70')[1].text).group()
                genres=re.search('(\w+, ){0,}\w+',film.findAll('div',class_='w-70')[1].text).group()
                cursor.execute(f'insert into films values({id1},NULL,"{name}","{duration}","{genres}")')
                id1+=1
            times=film.findAll('div',class_='session pr-2 d-flex flex-column pb-3')
            for time in times:
                film_id=cursor.execute(f"select id from films where name='{name}'").fetchall()[0][0]
                time1=time.find('a').text.strip()
                cursor.execute(f"insert into sessions values({id2}, {film_id}, {id_-1},'{date}','{time1}')")
                id2+=1
    else:
        print('Сайт не найден')
    return id1,id2 
        
def parsing_kinomax(cursor):       
    id_=get_id_cinema_halls(cursor)
    id1=get_id_films(cursor)
    id2=get_id_sessions(cursor)
    cities=parse_cities_kinomax()
    for city in cities[0:1]:
        halls=parse_halls_kinomax(city[0])
        for hall in halls:
            dates=parse_date_kinomax(hall[0],cursor,city[0],hall[1],id_)
            id_+=1
            for date in dates:
                id1,id2=parse_sessions_kinomax(hall[0]+'/?date='+date,cursor,id1,id2,id_,date)
                
def main_parsing(cursor,conn):
    delete_tables(cursor)
    create_tables(cursor)
    add_cinemas(cursor)
    parsing_karo(cursor)
    parsing_kinomax(cursor)
    conn.commit()

for i in range(10):
    try:
        main_parsing(cursor,conn)
        break
    except:
        print(f'Что-то пошло не так {i} раз')