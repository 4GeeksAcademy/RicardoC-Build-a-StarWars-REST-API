from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(25), nullable=False )
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    favorite_planets=db.relationship('FavoritePlanet', back_populates='user_relationship')
    favorite_persons=db.relationship('FavoritePerson', back_populates='user_relationship')

    def __repr__(self): #Sirve para imprimir en la terminal de Postgresql.
        return '<User %r>' % self.name
    
    def serialize(self): #Sirve para transformar la info en diccionarios python.
        return {
            "id": self.id,
            'name': self.name,
            "email": self.email
            # do not serialize the password, its a security breach
        }
class Planet(db.Model):
    __tablename__='planets'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20), unique=True, nullable=False)
    population=db.Column(db.Integer, nullable=False)
    diameter=db.Column(db.Integer, nullable=False)
    climated=db.Column(db.String(15), nullable=False)
    terrain=db.Column(db.String(15), nullable=False)
    favorite_by=db.relationship('FavoritePlanet', back_populates='planet_relationship')#Relación bidireccional con FavoritePlanet
    inhabitants=db.relationship('People', back_populates='planet_relationship')

    def __repr__(self):
        return f'<Planet {self.name}>'
    
    def serialize(self):
        return{
            'id':self.id,
            'name':self.name,
            'population':self.population,
            'diameter':self.diameter,
            'climated':self.climated,
            'terrain':self.terrain
        }
    
class People(db.Model):
    __tablename__='peoples'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20),unique=True, nullable=False)
    specie=db.Column(db.String(15), nullable=False)
    gender=db.Column(db.String(15), nullable=False)
    height=db.Column(db.Integer, nullable=False)
    weight=db.Column(db.Integer, nullable=False)
    age=db.Column(db.Integer, nullable=False)
    favorite_by=db.relationship('FavoritePerson', back_populates='people_relationship')
    planet_id=db.Column(db.Integer, db.ForeignKey('planets.id'))#Relación uno(Planet) a muchos(People)."Un planeta tiene muchos personajes".
    planet_relationship=db.relationship(Planet) #Relación unidireccional(ya que desde planetas puedo acceder a personajes pero no visceversa).
    #Ya que el back_populates lo defino solamente en Planet. Fk en relación uno a muchos siempre va en el lado muchos(People).
    
    def __repr__(self):
        return f'<People {self.name}>'
    
    def serialize(self):
        return{
            'id':self.id,
            'name':self.name,
            'specie':self.specie,
            'gender':self.gender,
            'height':self.height,
            'weight':self.weight,
            'age':self.age
        }
    
class FavoritePlanet(db.Model): #Tabla de unión que relaciona usuario con planets(Muchos a Muchos).
    __tablename__='favoritePlanets'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id')) #Llave foránea que apunta al id de la tabla user.
    user_relationship=db.relationship(User, back_populates='favorite_planets') #Relación que apunta a la clase User y a la variable que contiene la relación.
    planet_id=db.Column(db.Integer, db.ForeignKey('planets.id'))
    planet_relationship=db.relationship(Planet, back_populates='favorite_by')

    def __repr__(self):
        return f'<User {self.user_id} liked the planet{self.planet_id}>'
    
    def serialize(self):
        return{
            'id':self.id,
            'user_id':self.user_id,
            'planet_id':self.planet_id
        }

class FavoritePerson(db.Model):
    __tablename__='favoritePersons'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey('users.id'))
    user_relationship=db.relationship(User, back_populates='favorite_persons')
    people_id=db.Column(db.Integer, db.ForeignKey('peoples.id'))
    people_relationship=db.relationship(People, back_populates='favorite_by')

    def __repr__(self):
        return f'<User {self.user_id} liked the person {self.people_id}>'
    
    def serialize(self):
        return{
            'id':self.id,
            'user_id':self.user_id,
            'people_id':self.people_id
        }

























