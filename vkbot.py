import sqlite3
import random
import json
import vk_Api
from vk_api.longpoll import VkLongPoll, VkEventType


def write_msg(user_id, message,keyboard=None):
    random_id = random.getrandbits(31) * random.choice([-1, 1])
    vk.method('messages.send', {'user_id': user_id, 'message': message,'random_id':random_id,'keyboard':keyboard})

def cinema_halls(cinema):
    cinema_id=cursor.execute(f"select id from cinema where name='{cinema}'").fetchall()[0][0]
    return [elem[0] for elem in cursor.execute(f"select name from cinema_halls where cinema_id='{cinema_id}'").fetchall()]

def create_keyboard(list_buttons=[],cinema=None,cinema_hall=None,date=None,film=None,next_=0):   
    keyboard={"one_time": True}
    list_buttons=list_buttons[32*next_:]
    if next_:
        payload={'b':cinema,'h':cinema_hall,'d':date,'c':film,'n':next_-1}
        button_previous={"action": {"type": "text","payload": payload,"label": 'Назад'},
                        "color": "negative"}
    else:
        button_previous=None
    if len(list_buttons)>32:
        payload={'b':cinema,'h':cinema_hall,'d':date,'c':film,'n':next_+1}
        button_next={"action": {"type": "text","payload": payload,"label": 'Далее'},
                     "color": "positive"}
    else:
        button_next=None
    list_buttons=list_buttons[:32]
    buttons=[]
    for i,button in enumerate(list_buttons):
        payload={'b':cinema,'h':cinema_hall,'d':date,'c':film,'n':0}
        if not payload['b']:
            payload['b']=button
        elif not payload['h']:
            payload['h']=button
        elif not payload['d']:
            payload['d']=button
        else:
            payload['c']=button
        button={"action": {"type": "text","payload": payload,"label": next_*32+i+1},
                "color": "secondary"}
        buttons.append(button)
    list_buttons=[]
    while buttons:  
        list_buttons.append(buttons[:4])
        buttons=buttons[4:]
    if button_next and button_previous:
        list_buttons.append([button_previous,button_next])
    elif button_next:
        list_buttons.append([button_next])
    elif button_previous:
        list_buttons.append([button_previous])
    else:
        pass
    button={"action": {"type": "text","payload": None,"label": 'В меню'},
                "color": "primary"}
    
    list_buttons.append([button])
    keyboard["buttons"]=list_buttons 
    keyboard=str(json.dumps(keyboard))
    return keyboard

def dates(cinema_hall):
    cinema_hall_id=cursor.execute(f"select id from cinema_halls where name='{cinema_hall}'").fetchall()[0][0]
    date_list=[elem[0] for elem in cursor.execute(f"select date from sessions where hall_id='{cinema_hall_id}'").fetchall()]
    date_list=list(set(date_list))
    date_list.sort()
    return date_list

def films(date,cinema_hall):
    cinema_hall_id=cursor.execute(f"select id from cinema_halls where name='{cinema_hall}'").fetchall()[0][0]
    film_list=cursor.execute(f"select film_id from sessions where (hall_id='{cinema_hall_id}'and date='{date}') ").fetchall()
    for i,film in enumerate(film_list):
        film_list[i]=cursor.execute(f"select name from films where id='{film[0]}'").fetchall()[0][0]
    film_list=list(set(film_list))
    film_list.sort()
    return film_list

def information(cinema,cinema_hall,date,film):
    info=cursor.execute(f"select address,metro,phone,id from cinema_halls where name='{cinema_hall}'").fetchall()[0]
    address=info[0]
    metro=info[1]
    phone=info[2]
    hall_id=info[3]
    info=cursor.execute(f"select duration,genres,id from films where name='{film}'").fetchall()[0]
    duration=info[0]
    genres=info[1]
    film_id=info[2]
    info=cursor.execute(f"select time from sessions where (film_id='{film_id}' and hall_id='{hall_id}' and date='{date}')").fetchall()
    text=f'''Cеть кинотеатров: {cinema}
Кинотеатр: {cinema_hall}
Адрес: {address}
Метро: {metro}
Телефон: {phone}
Информация о фильме:
Фильм: {film}
Продолжительность: {duration} минут
Жанр: {genres}
Сеансы:'''
    for item in info:
        text=text+f'\nсеанс: {item[0]}'
    return text

conn=sqlite3.connect('mydatabase.db')
cursor=conn.cursor()
cinemas=[elem[0] for elem in cursor.execute("select name from cinema").fetchall()]
token = "a0400d450089bcfe69f97ee924ff3696099b9104a863db42ad6654e7175d10e49c3f2bd86496c36410efb"      
vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            payload=json.loads(event.extra_values.get('payload','""'))
            if not(payload):
                write_msg(event.user_id, 'Выберите бренд\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinemas)]),create_keyboard(cinemas))
            elif payload['b']and not payload['h']:
                next_=payload['n']
                cinema=payload['b']
                cinema_hall=cinema_halls(cinema)
                write_msg(event.user_id,'Выберите кинотеатр\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(cinema_hall)]),create_keyboard(cinema_hall,cinema,next_=next_))
            elif payload['b']and payload['h'] and not payload['d']:
                next_=payload['n']
                cinema=payload['b']
                cinema_hall=payload['h']
                date=dates(cinema_hall)
                write_msg(event.user_id,'Выберите дату\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(date)]),create_keyboard(date,cinema,cinema_hall,next_=next_))
            elif payload['b']and payload['h'] and payload['d'] and not payload['c']:
                next_=payload['n']
                cinema=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                film=films(date,cinema_hall)
                write_msg(event.user_id,'Выберите фильм\n'+'\n'.join([str(i+1)+') '+el for i,el in enumerate(film)]),create_keyboard(film,cinema,cinema_hall,date,next_=next_))
            else:
                cinema=payload['b']
                cinema_hall=payload['h']
                date=payload['d']
                film=payload['c']
                text=information(cinema,cinema_hall,date,film)
                write_msg(event.user_id,text,create_keyboard())