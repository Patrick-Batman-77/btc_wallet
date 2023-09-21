from flask import Flask,render_template,redirect,url_for,request
from  flask_login import UserMixin,LoginManager,login_required,login_user,logout_user,current_user
from flask_sqlalchemy import SQLAlchemy
from bitcoin import *
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///data.db'
app.secret_key = 'suiiiiiiiiiiiii'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
LoginManager.login_view = 'login'

class User(db.Model,UserMixin):
      id = db.Column(db.Integer, primary_key=True)
      private_key = db.Column(db.String(100), nullable=False, unique=True)
      public_key = db.Column(db.String(100), nullable=False, unique=True) 
      address = db.Column(db.String(100), nullable=False, unique=True)    
      
def create_wallet():
    private_key = random_key()
    public_key = privtopub(private_key)
    address = pubtoaddr(public_key)

    new_wallet = User(private_key=private_key, public_key=public_key, address=address)
    db.session.add(new_wallet)
    db.session.commit()

    return {
        'private_key': private_key,
        'public_key': public_key,
        'address': address
    }

       
@login_manager.user_loader
def loader(user_id):
      return User.query.get(int(user_id))
      
@app.route('/')
def home ():
      if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
      return render_template('index.html', title='Home')

@app.route('/create', methods=['GET','POST'])
def create():
      if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
      if request.method == 'GET':
            info = create_wallet()
            return render_template('create.html',info=info,title='Create')
            
@app.route('/login', methods=['GET','POST'])
def login():
      if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
      if request.method == 'POST':
            address = request.form['address']
            user = User.query.filter_by(address=address).first()
            if user:
                  login_user(user)
                  return redirect(url_for('dashboard'))
            else:
                  error = 'Address not found or is invalid!'
                  return render_template('login.html',error=error)
      return render_template('login.html', title='Login')

@app.route('/dashboard')
@login_required
def dashboard ():
      address = current_user.address
      url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"

      response = requests.get(url)

      if response.status_code == 200:
          balance = response.json()["balance"]
          btc = balance/100000000
          
          api_url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1&sparkline=false'
          response = requests.get(api_url)
          crypto_data = response.json()
          return render_template('dashboard.html',btc=btc,crypto_data=crypto_data)
    
      else:
          error =f"Failed to retrieve balance for address {address}"
      return render_template('dashboard.html',title='Dashboard',error=error)

@app.route('/account')
@login_required
def account():
      if request.method == 'GET':
            info = {'pv_key':current_user.private_key,'pb_key':current_user.public_key,'address':current_user.address}
            return render_template('account.html', account=info)
      return render_template('account.html',title='Accout')
      
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
    
@app.route('/delete/<int:id>')  
@login_required
def delete(id):
    user = User.query.filter_by(id=id).first()
    if user:
        logout_user()
        db.session.delete(user)
        db.session.commit()

        # Reassign sequential IDs to the remaining users
        users = User.query.all()
        for index, user in enumerate(users, start=1):
            user.id = index

        db.session.commit()

    return redirect(url_for('home'))

      
if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=False)