from datetime import datetime
from application import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

def log(command, user_id):
	log = LogBook(command=command, user_id=user_id)
	db.session.add(log)
	db.session.commit()


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(10), unique=True, nullable=False)
	email = db.Column(db.String(90), unique=True, nullable=False)
	password = db.Column(db.String(200), nullable=False)
	log = db.relationship('LogBook', backref='author', lazy=True)

	def __repr__(self):
		return f"User('{self.username}', '{self.email}')"


class LogBook(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_logged = db.Column(db.DateTime, nullable=False, default=datetime.now)
	command  = db.Column(db.String(200), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f"LogBook('{self.command}', '{self.date_logged}')"
