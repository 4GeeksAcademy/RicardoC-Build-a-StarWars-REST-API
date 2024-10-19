"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, FavoritePerson, FavoritePlanet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():
    users=User.query.all() #Hacemos una consulta a la base de datos con .query y obtenemos todos los registros con .all
    users_serialize=[] #Serializamos cada usuario de la BD y lo agregamos al nuestro array.
    for user in users:
        users_serialize.append(user.serialize())
    return jsonify ({
        'msg': 'Obtained Users!', #Devolvemos el array con los usuarios serializados y un status code ok(200).
        'data': users_serialize}), 200

@app.route('/user/<int:id>/favorites', methods=['GET'])
def get_favorites(id):
#Hacemos una consulta en la BD para buscar los planetas favoritos que coincide con el id del usuario.
    favorite_planets= FavoritePlanet.query.filter_by(user_id = id).all()
    favorite_persons= FavoritePerson.query.filter_by(user_id = id).all()
    if not favorite_planets and not favorite_persons: #Si no tenemos elementos agregados a favoritos devolvemos el siguiente mensaje:
        return jsonify({'msg':"You don't have favorite items"}), 404
    
    favorite_planets_serialize=[] #Serializamos cada planeta de favoritePlanets mediante su relación(planet_relationship).
    for planet_fav in favorite_planets:
        favorite_planets_serialize.append(planet_fav.planet_relationship.serialize())
    favorite_persons_serialize=[]
    for people_fav in favorite_persons:
        favorite_persons_serialize.append(people_fav.people_relationship.serialize())
    #Retornamos los planetas favoritos ya serializados y el usuario que "le gustó" un planeta en específico.
    return jsonify({
        'msg':'ok',
        'user_planet': favorite_planets[0].user_relationship.serialize(),
        'user_people': favorite_persons[0].user_relationship.serialize(),
        'favorite_planets': favorite_planets_serialize,
        'favorite_persons': favorite_persons_serialize
    }), 200 #Status code: ok.

@app.route('/peoples', methods=['GET'])
def all_peoples():
    peoples = People.query.all() #Obtenemos los registros de la tabla.
    peoples_serialize = [] #Creamos un array para almacenarlos.
    for person in peoples: #Almacenamos cada personaje en el array y los serializamos.
        peoples_serialize.append(person.serialize())

    return jsonify({
        'msg':'Characters obtained',
        'data': peoples_serialize
    }), 200

@app.route('/planets', methods=['GET'])
def all_planets():
    planets=Planet.query.all() #Obtenemos todos los planetas y almacenamos en un array.
    planets_serialize=[]
    for planet in planets: #agregamos cada planeta al array y lo serializamos.
        planets_serialize.append(planet.serialize())
        
    return jsonify({
        'msg':'Planets obtained',
        'data': planets_serialize
    }), 200

@app.route('/peoples/<int:id>', methods=['GET'])
def person(id):
    person=People.query.get(id) #Buscamos un personaje por su id.
    if not person: #Si no existe devolvemos el siguiente mensaje:
        return jsonify({'msg':'Character not found.'}), 404
    
    return jsonify({ #Si existe lo serializamos(convertimos en formato json para que sea leido por el front) y retornamos.
        'msg':'Character obtained',
        'data': person.serialize()
    }), 200

@app.route('/planets/<int:id>', methods=['GET'])
def planet(id):
    planet=Planet.query.get(id)
    if not planet:
        return jsonify({'msg':'Planet not found.'}), 404
#Serializamos y agregamos al array los personajes que están en ese planeta, ya que hicimos una relación unidirecional entre planeta(Uno) y personajes(muchos).
    inhabitants_serialize=[]
    for habitant in planet.inhabitants: #Hay que iterar sobre el atributo inhabitants(personajes) del objeto Planet.
        inhabitants_serialize.append(habitant.serialize())
    data = planet.serialize()
    data['inhabitants'] = inhabitants_serialize

    return jsonify({
        'msg':'Planet obtained',
        'data': data
    }), 200

@app.route('/user', methods=['POST'])
def add_user():
    body=request.get_json(silent=True) #Obtenemos los datos del front.
    if not body:
        return jsonify({'msg':'Fields cannot be empty.'}),400 #Verificamos que el body no sea None(vacío).
    
    if 'name' not in body: #Verificamos la existencia de los campos en el body.
        return jsonify({'msg':'The name field is required.'}), 400
    
    if 'email' not in body:
        return jsonify({'msg':'The email field is required.'}), 400
    
    if 'password' not in body:
        return jsonify({'msg': 'The password field is required.'}), 400
    
    email = User.query.filter_by(email=body['email']).first() #Verificamos que el email no exista en la BD.
    if email:
        return jsonify({'msg':'This email is taken; please choose another.'}), 400
    
    user=User() #Instanciamos nuevo usuario.
    user.name=body['name'] #Asignamos los campos del body a los atributos del objeto user(tabla).
    user.email=body['email']
    user.password=body['password']
    user.is_active=True #Asignamos un valor por defecto ya que este campo no es null en la tabla.
    db.session.add(user)#Añadimos la instancia.
    db.session.commit()#Guardamos

    return jsonify({ #serializamos usuario(para ver y usar esa info y retornamos).
        'msg':'User created',
        'data': user.serialize()
    }), 201

@app.route('/planet', methods=['POST'])
def add_planet():
    body=request.get_json(silent=True) #Obtenemos los datos del front.
    if not body:
        return jsonify({'msg':'Fields cannot be empty.'}),400 #Verificamos que el body no sea None(vacío).
    
    if 'name' not in body: #Verificamos la existencia de los campos en el body.
        return jsonify({'msg':'The name field is required.'}), 400
    
    if 'population' not in body:
        return jsonify({'msg':'The population field is required.'}), 400
    
    if 'diameter' not in body:
        return jsonify({'msg': 'The diameter field is required.'}), 400
    
    if 'climated' not in body:
        return jsonify({'msg':'The climated field is required.'}), 400
    
    if 'terrain' not in body:
        return jsonify({'msg': 'The terrain field is required.'}), 400
    
    planet_name = Planet.query.filter_by(name=body['name']).first() #Verificamos que el name no exista en la BD.
    if planet_name:
        return jsonify({'msg':'This name is taken; please choose another.'}), 400
    
    planet=Planet() #Instanciamos nuevo planeta.
    planet.name=body['name'] #Asignamos los campos del body a los atributos del objeto planet(tabla).
    planet.population=body['population']
    planet.diameter=body['diameter']
    planet.climated=body['climated']
    planet.terrain=body['terrain']
    db.session.add(planet)#Añadimos la instancia.
    db.session.commit()#Guardamos

    return jsonify({ #serializamos usuario(para ver y usar esa info y retornamos).
        'msg':'Planet created',
        'data': planet.serialize()
    }), 201

@app.route('/people', methods=['POST'])
def add_person():
    body=request.get_json(silent=True) #Obtenemos los datos del front.
    if not body:
        return jsonify({'msg':'Fields cannot be empty.'}),400 #Verificamos que el body no sea None(vacío).
    
    if 'name' not in body: #Verificamos la existencia de los campos en el body.
        return jsonify({'msg':'The name field is required.'}), 400
    
    if 'specie' not in body:
        return jsonify({'msg':'The specie field is required.'}), 400
    
    if 'gender' not in body:
        return jsonify({'msg': 'The gender field is required.'}), 400
    
    if 'height' not in body:
        return jsonify({'msg':'The height field is required.'}), 400
    
    if 'weight' not in body:
        return jsonify({'msg': 'The weight field is required.'}), 400
    
    if 'age' not in body:
        return jsonify({'msg': 'The age field is required.'}), 400
    
    person_name = People.query.filter_by(name=body['name']).first() #Verificamos que el name no exista en la BD.
    if person_name:
        return jsonify({'msg':'This name is taken; please choose another.'}), 400
    
    person=People() #Instanciamos nueva persona.
    person.name=body['name'] #Asignamos los campos del body a los atributos del objeto People(tabla).
    person.specie=body['specie']
    person.gender=body['gender']
    person.height=body['height']
    person.weight=body['weight']
    person.age=body['age']
    db.session.add(person)#Añadimos la instancia.
    db.session.commit()#Guardamos

    return jsonify({ #serializamos usuario(para ver y usar esa info y retornamos).
        'msg':'Person created',
        'data': person.serialize()
    }), 201

@app.route('/favorite/planet/<int:planet_id>/<int:user_id>', methods=['POST'])
def add_favorite_planet(user_id,planet_id):
    user=User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User Not Found'}),404
    
    planet=Planet.query.get(planet_id) #Obtenemos un registro especifico de la tabla.
    if not planet:
        return jsonify({'msg':'Planet Not Found'}),404
    
#Verificamos que el id del usuario y del planeta coincida con los actuales y obtenemos el primer registro.
    favorite_planet = FavoritePlanet.query.filter_by(user_id = user_id, planet_id = planet_id).first()
    if favorite_planet:
        return jsonify({'msg':f'The planet {planet.name} is already added to favorites'}), 400
    
    favorite = FavoritePlanet() #Instanciamos el nuevo favorito.
    favorite.user_id = user_id #Asignamos el id del usuario al campo user_id del objeto(tabla).
    favorite.planet_id = planet_id
    db.session.add(favorite) #Añadimos la instancia.
    db.session.commit() #Guardamos
    return jsonify({'msg': 'Planet bookmarked'}), 200

@app.route('/favorite/person/<int:people_id>/<int:user_id>', methods=['POST'])
def add_favorite_person(user_id,people_id):
    user=User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User Not Found'}),404
    
    person=People.query.get(people_id)
    if not person:
        return jsonify({'msg':'Person Not Found'}),404
    
    favorite_person = FavoritePerson.query.filter_by(user_id = user_id, people_id = people_id).first()
    if favorite_person:
        return jsonify({'msg':f'The person {person.name} is already added to favorites'}), 400
    
    favorite = FavoritePerson()
    favorite.user_id = user_id
    favorite.people_id = people_id
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'msg': 'Person bookmarked'}), 200

@app.route('/favorite/planet/<int:planet_id>/<int:user_id>', methods=['DELETE'])
def delete_favorite_planet(user_id,planet_id):
    user=User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User Not Found'}),404
    
    planet=Planet.query.get(planet_id) #Obtenemos el registro especifico.
    if not planet:
        return jsonify({'msg':'Planet Not Found'}),404
    
#Verificamos que el favorito no exista ya en la lista.
    favorite_planet = FavoritePlanet.query.filter_by(user_id = user_id, planet_id = planet_id).first()
    if not favorite_planet:
        return jsonify({'msg':'The planet is not in favorites'}), 404
    
    db.session.delete(favorite_planet) #Eliminamos el favorito.
    db.session.commit() #Guardamos.
    return jsonify({'msg': f'Planet {planet.name} removed from watch list'}), 200 #f para colocar atributos

@app.route('/favorite/person/<int:people_id>/<int:user_id>', methods=['DELETE'])
def delete_favorite_person(user_id,people_id):
    user=User.query.get(user_id) #get solo para PK(id)
    if not user:
        return jsonify({'msg': 'User Not Found'}),404
    
    person=People.query.get(people_id)
    if not person:
        return jsonify({'msg':'Person Not Found'}),404
    
    favorite_person = FavoritePerson.query.filter_by(user_id = user_id, people_id = people_id).first()
    if not favorite_person:
        return jsonify({'msg':'The person is not in favorites'}), 404
    
    db.session.add(favorite_person)
    db.session.commit()
    
    return jsonify({'msg': f'Person {person.name} removed from watch list'}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
