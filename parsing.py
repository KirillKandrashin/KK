import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('mydatabase.db')                    #создаем базу данных с именем mydatabase
cursor=conn.cursor()                                    #cursor позволяет нам работать с базой данных

def delete_tables(cursor):                            #удаляем таблицы, созданные ранее
    try:
        cursor.execute('drop table brand')            #поочередно удаляем все таблицы, если они существуют
    except sqlite3.OperationalError:
        print('Еще не создана')
    try:
        cursor.execute('drop table cinema_halls')     #поочередно удаляем все таблицы, если они существуют
    except sqlite3.OperationalError:
        print('Еще не создана')    
    try:
        cursor.execute('drop table cinemas')          #поочередно удаляем все таблицы, если они существуют
    except sqlite3.OperationalError:
        print('Еще не создана')    
    try:
        cursor.execute('drop table sessions')         #поочередно удаляем все таблицы, если они существуют
    except sqlite3.OperationalError:
        print('Еще не создана') 
        
def create_cinemas(cursor):                #создаем таблицу с названиями всех сетей кинотеатров для парсинга, если такой еще не существует
    try:                                            #таблица содержит номер(индекс/id) каждой сети кинотеатров и ее название
        cursor.execute('''CREATE TABLE cinemas(         
                        id integer PRIMARY KEY,
                        name text NOT NULL)''')
    except sqlite3.OperationalError:
        print('Ошибка! Таблица уже создана')
        
def create_cinema_halls(cursor):                     #создаем таблицу со всей информацией про каждое здание кинотеатра(номер в таблице, номер сети, номера на сайте, имя, адрес, метро, телефон)
    try:
        cursor.execute("""CREATE TABLE cinema_halls(
                    id integer PRIMARY KEY,
                    cinemas_id integer Not NULL,
                    website_id integer NULL,
                    name text NOT NULL,
                    address text NOT NULL,
                    metro text NULL,
                    phone text NULL,                                
                    FOREIGN KEY (brand_id) REFERENCES brand(id)  
                    )""")                               #объект brand_id берет свое значение по ссылке в таблице, где оно уже есть
    except sqlite3.OperationalError:
        print('Что делаешь? Таблица то уже создана!')        

def create_films(cursor):                     #создаем таблицу со всеми характеристиками всего кино(номер, номер на сайте, название, продолжительность, язык и жанр фильма)
    try:
        cursor.execute("""CREATE TABLE films(
                    id integer PRIMARY KEY,
                    website_id integer NULL,
                    name text NOT NULL,
                    duration text NULL,
                    genres text NULL
                    )""")
    except sqlite3.OperationalError:
        print('Ошибка! Таблица уже создана')   
        
def create_table_sessions(cursor):                    #создаем таблицу со всеми харктеристиками идущего в кинотеатрах кино(номер, номер кино на сайте, номер кинотеатра, дата, время, цена билета)
    try:                                    
        cursor.execute("""CREATE TABLE sessions(
                    id integer PRIMARY KEY,
                    films_id integer Not NULL,
                    hall_id integer Not NULL,
                    age integer NOT NULL,
                    type text NOT NULL,
                    date date NOT NULL,
                    time time NOT NULL,
                    FOREIGN KEY (films_id) REFERENCES films(id),    
                    FOREIGN KEY (hall_id) REFERENCES cinema_halls(id)
                    )""")                                                           #объекты cinema_id и hall_id ссылаются на значения в таблицах, в которых они уже записаны
    except sqlite3.OperationalError:
        print('Ошибка! Таблица уже создана')     
        
def create_tables(cursor):     #создаем все вышеперечисленные таблицы
    create_table_cinemas(cursor)
    create_cinema_halls(cursor)
    create_table_films(cursor)
    create_sessions(cursor)     
    
def add_cinemas(cursor):    #заполняю таблицу сетей кинотеатров
    try:
        cursor.execute("insert into brand values (1, 'КАРО')")
        cursor.execute("insert into brand values (2, 'КИНОМАКС')")
        cursor.execute("insert into brand values (3, '')")
        conn.commit()                          #сохраняем изменения
    except sqlite3.IntegrityError:
        print('такое уже есть')
        
def remove_all(string):                       #функция очистки таблицы
    pattern = re.compile(r'[А-Яа-яёЁ0-9 ]+')
    return pattern.findall(string)[0].strip()
    
def find_all_cinemas_KARO(theaters):            #получаем всю информацию о кинотеатрах КАРО и записываем в словарь
    dicti = {}
    metro_class = 'cinemalist__cinema-item__metro__station-list__station-item'
    for theater in theaters:
        dict[theater.findAll('h4')[0].text.strip()] = {
            'metro': [remove_all(i.text) for i in theater.findAll('li', class_=metro_class)], 
            'address': theater.findAll('p')[0].text.split('+')[0].strip(),
            'phone': '+' + theater.findAll('p')[0].text.split('+')[-1].strip(),
            'data-id': theater['data-id']}      #id кинотеатра на сайте
    return dicti

def cinema_id_get(name,films):    #получаем id по данному названию фильма
    for obj in films:
        if name==obj[2]:
            return obj[0]
   # for ob in films:    не уверен, что это надо
    #    if (name in obj[2]) or (obj[2] in name):
     #       return obj[0]
        
def parsing_karo(cursor):
    link = "https://karofilm.ru"
    link_theaters = url + "/theaters"        
    r = requests.get(link_theaters)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")                     #начинаем анализировать страницу(создаем синтаксическое дерево страницы, из которого выдергиваем нужную информацию)
        theaters = soup.findAll('li', class_='cinemalist__cinema-item') #ищем класс, в котором содержится нужная информация
        karo_theaters = find_all_theaters_KARO(theaters)                #словарь всей информации по каждому кинотеатру
    else:
        print("Страница не найдена")
    id_=1                                   #ставим счетчик нумерации
    for key,item in karo_theaters.items():  #просматриваем поочередно каждый кинотеатр в словаре
        try:
            metro=', '.join(item['metro'])  #отдельно ищем метро, тк около кинотеатра его может и не быть
            if metro:
                metro="'"+metro+"'"
            else:
                metro='NULL'
            elements=[id_,1,item['data-id'],key,item['address'],metro,item['phone']]        #получаем информацию по каждому кинотеатру
            cursor.execute("insert into cinema_halls values ({},{},{},'{}','{}',{},'{}')".format(*elements))   #втавляем полученную информацию в таблицу
            id_+=1
        except sqlite3.IntegrityError:
            print(f'id({id_}) уже существует')   не уверен, что надо
            break       
    films_class='afisha-item'   #afisha-item классы с инфой о фильмах
    r = requests.get(link)
    if r.status_code==200:
        films_parser=BeautifulSoup(r.text,'html.parser')
        all_films_list=films_parser.findAll('div',class_=films_class)   #создаем список со всей инфой о фильмах
    else:
        print('Страницы нет')        
    id_=1                           #ставим счетчик нумерации
    for element in all_films_list:  #выковыриваем нужную инфу из списка
        data_id=element['data-id']                  
        name=element.findAll('h3')[0].text.strip()  #удаляем пробелы справа и слева
        duration=element.findAll('span')[0].text
        try:
            genres='"'+element.findAll('p',class_='afisha-genre')[0].text+'"'  #отдельно ищем жанр фильма
        except IndexError:
            genres='NULL'
        try:
            name=name.replace('\"','\'')
            cursor.execute(f'insert into films values ({id_},{data_id}, "{name}", "{duration}", {genres})')
            id_+=1
        except sqlite3.IntegrityError:
            print(f'id({id_}) уже существует')
            break     
    films_class='cinema-page-item__schedule__row'       #в коде о каждом кинотеатре
    table_class='cinema-page-item__schedule__row__board-row'
    left_class=table_class+'__left'
    rignt_class=table_class+'__right'
    date_class='widget-select'
    id_=1
    for theater in karo_theatres:
        dates={}
        link_theater_id=link_theaters+'?id='+karo_theatres[theater]['data-id']
        r = requests.get(link_theater_id)
        if r.status_code==200:
            date_parser=BeautifulSoup(r.text,'html.parser')
            date_list=date_parser.findAll('select',class_=date_class)[0]
            date_list=[i['data-id'] for i in date_list.findAll('option')]   #ограненный список со всеми датами
            for date in date_list: 
                link_theater_id_date=link_theater_id+'&date='+date
                r = requests.get(link_theater_id_date)
                session={}
                if r.status_code==200:
                    films_parser=BeautifulSoup(r.text,'html.parser')
                    films_list=films_parser.findAll('div',class_=films_class)
                    for film in films_list:
                        name=film.findAll('h3')
                        if name:
                            name=name[0].text.split(', ')
                            session_info={}
                            session_info['age']=name[1]                     #находим возраст
                            for i in film.findAll('div',class_=table_class):
                                film_type=i.findAll('div',class_=left_class)[0].text.strip()        #находим тип
                                session_info['type']=film_type
                                time=i.findAll('div',class_=rignt_class)[0].findAll('a')
                                time=[j.text for j in time]
                                #session_info['time']=time
                                for time_element in time:
                                    cinema_id=cinema_id_get(name[0].replace('\"','\''),cursor.execute(f'select * from films').fetchall())
                                    hall_id=cursor.execute(f'select id from cinema_halls where name=\'{theater}\'').fetchall()[0][0]
                                    values=[id_,cinema_id,hall_id,session_info['age'],session_info['type'],date,time_element,'NULL']
                                    cursor.execute("insert into sessions values ({},{},{},'{}','{}','{}','{}',{})".format(*values))
                                    id_+=1
                            session[name[0]]=session_info
                else:
                    print('Нет такой даты, link=',link_theater_id_date)
                dates[date]=session
        else:
            print('Такого кинотеатра нет, link=',link_theater_id)
        karo_theatres[theater]['dates']=dates               


    
    
def main_parse(cursor,conn):
    delete_tables(cursor)
    create_tables(cursor)
    add_brands(cursor)
    main_parse_karo(cursor)
    conn.commit()

for i in range(10):
    try:
        main_parse(cursor,conn)
        break
    except:
        print(f'Что-то пошло не так {i} раз')
