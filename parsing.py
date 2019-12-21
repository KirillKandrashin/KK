import requests
from bs4 import BeautifulSoup
import re
import sqlite3
conn=sqlite3.connect('cinemas.db')
cursor=conn.cursor()

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
                    language text NULL,
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
                    date date NOT NULL,
                    time time NOT NULL,
                    price text NULL,
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
        conn.commit()
    except sqlite3.IntegrityError:
        print('id не уникален!')
        
def remove_all(string):                       #функция очистки таблицы
    pattern = re.compile(r'[А-Яа-яёЁ0-9 ]+')
    return pattern.findall(string)[0].strip()
    
def find_all_cinemas_KARO(theatres):
    dicti = {}
    metro_class = 'cinemalist__cinema-item__metro__station-list__station-item'
    for theater in theatres:
        dict[theater.findAll('h4')[0].text.strip()] = {
            'metro': [remove_all(i.text) for i in theater.findAll('li', class_=metro_class)], 
            'address': theater.findAll('p')[0].text.split('+')[0].strip(),
            'phone': '+' + theater.findAll('p')[0].text.split('+')[-1].strip(),
            'data-id': theater['data-id']}
    return dicti

def cinema_id_get(name,cinemas):
    for i in cinemas:
        if name==i[2]:
            return i[0]
    for i in cinemas:
        if (name in i[2]) or (i[2] in name):
            return i[0]


    
    
