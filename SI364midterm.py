###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
import requests
import json

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'hardtoguessstring'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/wminckMidterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)

######################################
######## HELPER FXNS (If any) ########
######################################



##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Company(db.Model):
    __tablename__ = "Companies"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String())
    symbol = db.Column(db.String())
    stock_id = db.Column(db.Integer,db.ForeignKey("Stocks.id"))
    industry = db.Column(db.String())
    industry_id = db.Column(db.Integer,db.ForeignKey("Industries.id"))

class Stock(db.Model):
    __tablename__ = "Stocks"
    id = db.Column(db.Integer,primary_key=True)
    symbol = db.Column(db.String())
    price = db.Column(db.Float)
    companies = db.relationship("Company", backref="Stock")

class Industry(db.Model):
    __tablename__ = 'Industries'
    id = db.Column(db.Integer,primary_key=True)
    industry = db.Column(db.String())
    count = db.Column(db.Integer)
    companies = db.relationship("Company", backref="Industry")


###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()

class StockForm(FlaskForm):
    name = StringField("What is the name of the company?",validators=[Required()])
    symbol = StringField("What is the stock symbol of the company?",validators=[Required()])
    industry = StringField("What industry is the company in?",validators=[Required()])
    submit = SubmitField('Submit')

    def validate_symbol(self, field):
        if len(field.data.split()) != 1:
            raise ValidationError("Invalid stock symbol. There should be no spaces.")

class FactsForm(FlaskForm):
    ceo = StringField("Who is the head of the company?",validators=[Required()])
    hq = StringField("Where is the company's headquarters?",validators=[Required()])
    launch = StringField("When did the company launch?",validators=[Required()])
    submit = SubmitField('Submit')

#######################
###### VIEW FXNS ######
#######################
@app.route('/',methods=["GET","POST"])
def home():
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html', form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/entry_page', methods=['GET', 'POST'])
def data_entry():
    form = StockForm()
    if form.validate_on_submit():
        stock = db.session.query(Stock).filter_by(symbol=form.symbol.data).first()
        if stock:
            pass
        else:
            response = requests.get('https://api.iextrading.com/1.0/stock/{}/price'.format(form.symbol.data))
            data = json.loads(response.text)
            stock = Stock(symbol=form.symbol.data, price=data)
            db.session.add(stock)
            db.session.commit()

        industry = db.session.query(Industry).filter_by(industry=form.industry.data).first()
        if industry:
            industry.count += 1
            db.session.commit()
        else:
            industry = Industry(industry=form.industry.data, count = 1)
            db.session.add(industry)
            db.session.commit()

        if db.session.query(Company).filter_by(name=form.name.data, symbol=form.symbol.data, industry=form.industry.data).first():
            flash("This company already exists in the database")
            return redirect(url_for("see_all_companies"))

        else:
            company = Company(name=form.name.data, symbol=form.symbol.data, stock_id=stock.id, industry=form.industry.data, industry_id=industry.id)
            db.session.add(company)
            db.session.commit()
            flash("Company was successfully added to the database")
            return redirect(url_for("data_entry"))

    return render_template('input.html',form=form)

@app.route('/facts_form')
def facts():
    form = FactsForm()
    return render_template('facts_form.html', form=form)

@app.route('/fun_facts')
def company_info(methods=['GET']):
    ceo = request.args.get("ceo")
    hq = request.args.get("hq")
    launch = request.args.get("launch")
    return render_template('fun_facts.html', ceo=ceo, hq=hq, launch=launch)

@app.route('/all_companies')
def see_all_companies():
    companies = Company.query.all()
    return render_template('all_companies.html',companies=companies)

@app.route('/all_stocks')
def see_all_stocks():
    stocks = Stock.query.all()
    return render_template('all_stocks.html',stocks=stocks)

@app.route('/all_industries')
def see_all_industries():
    industries = Industry.query.all()
    return render_template('all_industries.html',industries=industries)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
