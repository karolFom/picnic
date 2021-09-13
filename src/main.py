import datetime as dt
from fastapi import FastAPI, HTTPException, Query
from database import engine, Session, Base, City, User, Picnic, PicnicRegistration
from external_requests import CheckCityExisting, GetWeatherRequest
from models import RegisterUserRequest, UserModel

app = FastAPI()


@app.post('/create-city/', summary='Create City', description='Создание города по его названию',
          tags=['city'])
def create_city(city: str = Query(description="Название города", default=None)):
    if city is None:
        raise HTTPException(status_code=400, detail='Параметр city должен быть указан')
    check = CheckCityExisting()
    if not check.check_existing(city):
        raise HTTPException(status_code=404, detail='Параметр city должен быть существующим городом')

    city_object = Session().query(City).filter(City.name == city.capitalize()).first()
    if city_object is None:
        city_object = City(name=city.capitalize())
        s = Session()
        s.add(city_object)
        s.commit()

    return {'id': city_object.id, 'name': city_object.name, 'weather': city_object.weather}


@app.get('/get-cities/', summary='Get Cities', tags=['city'])
def cities_list(q: str = Query(description="Название города", default=None)):
    """
    Получение списка городов
    """
    cities = Session().query(City)
    if q:
        cities = cities.filter(City.name == q.capitalize())

    return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city in cities]


@app.get('/get-users/', summary='Get Users', tags=['user'])
def users_list(min_age: int = Query(description="Минимальный возраст пользователя", default=None),
               max_age: int = Query(description="Максимальный возраст пользователя", default=None)):
    """
    Список пользователей
    """
    users = Session().query(User)
    if min_age:
        users = users.filter(User.age >= min_age)
    if max_age:
        users = users.filter(User.age <= max_age)
    return [{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'age': user.age,
    } for user in users]


@app.post('/create-user/', summary='Create User', response_model=UserModel, tags=['user'])
def create_user(user: RegisterUserRequest):
    """
    Регистрация пользователя
    """
    user_object = User(**user.dict())
    s = Session()
    s.add(user_object)
    s.commit()

    return UserModel.from_orm(user_object)


@app.get('/get-picnics/', summary='Get All Picnics', tags=['picnic'])
def all_picnics(datetime: dt.datetime = Query(default=None, description='Время пикника (по умолчанию не задано)'),
                past: bool = Query(default=True, description='Включая уже прошедшие пикники')):
    """
    Список всех пикников
    """
    picnics = Session().query(Picnic)
    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())

    return [{
        'id': pic.id,
        'city': Session().query(City).filter(City.id == pic.id).first().name,
        'time': pic.time,
        'users': [
            {
                'id': pr.user.id,
                'name': pr.user.name,
                'surname': pr.user.surname,
                'age': pr.user.age,
            }
            for pr in Session().query(PicnicRegistration).filter(PicnicRegistration.picnic_id == pic.id)],
    } for pic in picnics]


@app.post('/create-picnic/', summary='Create Picnic', tags=['picnic'])
def picnic_add(city_id: int = None, datetime: dt.datetime = None):
    p = Picnic(city_id=city_id, time=datetime)
    s = Session()
    s.add(p)
    s.commit()

    return {
        'id': p.id,
        'city': Session().query(City).filter(City.id == p.city_id).first().name,
        'time': p.time,
    }


@app.post('/register-user-to-picnic/', summary='Register User To Picnic', tags=['picnic'])
def register_to_picnic(user_id: int, picnic_id: int):
    """
    Регистрация пользователя на пикник
    (Этот эндпойнт необходимо реализовать в процессе выполнения тестового задания)
    """
    registered_to_picnic = PicnicRegistration(user_id=user_id, picnic_id=picnic_id)
    s = Session()
    s.add(registered_to_picnic)
    s.commit()

    return {
        'id': registered_to_picnic.id,
        'user': Session().query(User).filter(User.id == registered_to_picnic.id).first().name,
        'picnic_id': registered_to_picnic.picnic_id
    }

