from depotapp import app, mongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import requests

Stock_API = app.config["STOCK_URI"]

# Add a new User
@app.route('/user', methods=['POST'])
def add_user():
	_json = request.json
	_name = _json['name']
	_email = _json['email']
	_password = _json['pwd']
	# validate the received values
	if _name and _email and _password and request.method == 'POST':
		#do not save password as a plain text
		_hashed_password = generate_password_hash(_password)
		# save details
		mydict = {'name': _name, 'email': _email, 'pwd': _hashed_password}
		id = mongo.db.user.insert_one(mydict)
		result = jsonify({'user': str(id.inserted_id) })
		resp = result
		resp.status_code = 200
		return resp
	else:
		return not_found()
		
# return all users		
@app.route('/user', methods=['GET'])
def users():
	users = mongo.db.user.find()
	resp = dumps(users)
	return resp

# JSON enthält UserID, email, name, Passwort
# update User data
@app.route('/user', methods=['PUT'])
def update_user():
	_json = request.json
	_id = _json['id']
	_name = _json['name']
	_email = _json['email']
	_password = _json['pwd']		
	# validate the received values
	if _name and _email and _password and _id and request.method == 'PUT':
		#do not save password as a plain text
		_hashed_password = generate_password_hash(_password)
		# save edits
		query = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}
		values = {'$set': {'name': _name, 'email': _email, 'pwd': _hashed_password}}
		id = mongo.db.user.update_one(query, values)
		result = jsonify({'user': str(_id)})
		resp = result
		resp.status_code = 200
		return resp
	else:
		return not_found()

# return all data to a specific user
@app.route('/user/<id>', methods=['GET'])
def user(id):
	user = mongo.db.user.find_one({'_id': ObjectId(id)})
	resp = dumps(user)
	#resp.status_code = 200
	return resp

@app.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
	myquery = {'_id': ObjectId(id)}
	mongo.db.user.delete_one(myquery)
	result = jsonify({'user': str(id)})
	resp = result
	resp.status_code = 200
	return resp

# body enthält UserID und UserBudget
@app.route('/depot', methods=['POST'])
def add_depot():
	_json = request.json
	_userid = _json['id']
	_budget = _json['budget']
	# validate the received values
	if _userid and _budget and request.method == 'POST':
		# save details
		#results = mongo.db.depot.find()
		mydict = {'userID':_userid,'budget':_budget,"equities":[]}
		id = mongo.db.depot.insert_one(mydict)
		result = jsonify({'depot': str(id.inserted_id)})
		resp = result
		resp.status_code = 200
		return resp
	else:
		return not_found()

# body user id
@app.route('/depot', methods=['GET'])
def depot():
	depot = mongo.db.depot.find()
	resp = dumps(depot)
	#resp.status_code = 200
	return resp

# return all depot data to a specific user
@app.route('/depot/user/<id>', methods=['GET'])
def depots(id):
	depot = mongo.db.depot.find({'userID': id})
	resp = dumps(depot)
	#resp.status_code = 200
	return resp

# Buy or sell
@app.route('/depot/<id>', methods=['PUT'])
def change_share(id):
	_json = request.json
	_id = id
	_type = _json['type']
	_share = _json['share']
	_amount = _json['amount']
	if _type == 'buy':
		# validate the received values
		if _id and request.method == 'PUT':
			# is Share already in the depot?
			exist = mongo.db.depot.find({'_id': ObjectId(id), "equities.share": _share})
			# exist will be 0 if there is no entry with this ID which contains these share
			if exist.count() == 0:
				# missing: get the current value of one share
				r = requests.get(Stock_API + "/equities/" +_share + "/latest")
				_json = r.json()
				_buyValue = _json["Global Quote"]["05. price"]
				# save edits
				query = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}
				values = { '$push': { 'equities': { '$each': [ { 'share': _share, 'stock': [{'amount': _amount, 'buyValue': _buyValue, 'sellValue': 0, 'date': datetime.now() }] }],}}}
				result = mongo.db.depot.update_one(query, values)
				resp = jsonify({'depotID': str(result.upserted_id)})
				resp.status_code = 200
				return resp
			elif len(exist[0]['equities']) > 0:
				r = requests.get(Stock_API + "/equities/" +_share + "/latest")
				_json = r.json()
				_buyValue = _json["Global Quote"]["05. price"]

				# update into database
				query = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.share': _share}
				values = { '$push': {"equities.$.stock": { '$each': [{'amount': _amount, 'buyValue': _buyValue, 'sellValue': 0, 'date': datetime.now()}] }}}
				result = mongo.db.depot.update_one(query, values)
				resp = jsonify({'depotID': str(result.upserted_id)})
				resp.status_code = 200
				return resp
			else:
				return not_found()
		else:
			return not_found()

	elif _type == 'sell':
		# validate the received values
		if _id and request.method == 'PUT':
			# is Share already in the depot?
			exist = mongo.db.depot.find({'_id': ObjectId(id), "equities.share": _share})
			if len(exist[0]['equities']) > 0:
				r = requests.get(Stock_API + "/equities/" +_share + "/latest")
				_json = r.json()
				_sellValue = _json["Global Quote"]["05. price"]
				mymatch = {"$match": {"$and": [ { "_id": ObjectId(_id) }, {"equities.share": _share}]}}
				myunwind = {"$unwind": "$equities"}
				myproject = {"$project": {"share": "$equities.share", "amount_total": {"$sum": "$equities.stock.amount"}, "stock": "$equities.stock" }}
				pipeline= [myunwind, mymatch, myproject]		
				query = mongo.db.depot.aggregate(pipeline)
				query_results = list(query)
				print(query_results[0])
				total_amount = query_results[0]['amount_total']
				# wie viele Aktien noch zu verkaufen sind
				shares_to_sell = _amount
				# können alle Aktien verkauft werden? 
				if total_amount > _amount:
					for each in query_results[0]['stock']:
						# check how many shares are in the first buy
						available_shares_depot = each['amount']
						# können alle Aktien aus einem Buy verkauft werden?
						if available_shares_depot > shares_to_sell:
							buy_date = each['date']
							# neue Aktienanzahl in dem buy
							new_amount = available_shares_depot - shares_to_sell
							# der Wert, der mit dem Verkauf auf das Budget gerechnet wird
							budget = float(exist[0]['budget'])
							share_value_sell = float(_sellValue) * float(shares_to_sell)
							new_budget = budget + share_value_sell
							# in diesem if können alle Aktien verkauft werden, daher wird shares_to_sell auf 0 gesetzt.
							shares_to_sell -= 0
							# update der DB
							newvalues = { '$set': {'budget': new_budget,  'equities.$[eq].stock.$[st].amount': new_amount}}
							myfilter = [ {"eq.share": _share},{"st.date": buy_date}]
							myquery = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}
							query = mongo.db.depot.update_one(filter=myquery, update=newvalues, array_filters=myfilter, upsert=True )
							resp = jsonify({'depotID': str(query.upserted_id)})
							resp.status_code = 200
							return resp
							# wenn alle Aktien verkauft wurden, müssen die anderen buys nicht mehr durchlaufen werden
							break
						# alle Aktien aus einem buy werden verkauft, also wird er buy gelöscht. /oder amount erstmal auf null gesetzt.
						elif available_shares_depot == shares_to_sell:
							buy_date = each['date']
							# neue Aktienanzahl in dem buy
							new_amount = available_shares_depot - shares_to_sell
							# der Wert, der mit dem Verkauf auf das Budget gerechnet wird
							budget = float(exist[0]['budget'])
							share_value_sell = float(_sellValue) * float(shares_to_sell)
							new_budget = budget + share_value_sell
							# in diesem if können alle Aktien verkauft werden, daher wird shares_to_sell auf 0 gesetzt.
							shares_to_sell -= 0
							# update der DB
							myquery = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.stock.date': buy_date}
							newvalues = {'$pull':{'equities.$.stock':{'date': buy_date}} }
							query = mongo.db.depot.update_one(myquery, newvalues)
							
							newvalues = { '$set': {'budget': new_budget}}
							myquery = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}
							query = mongo.db.depot.update_one(myquery, newvalues)

							resp = jsonify({'depotID': str(query.upserted_id)})
							resp.status_code = 200
							return resp
							# wenn alle Aktien verkauft wurden, müssen die anderen buys nicht mehr durchlaufen werden
							break
						# alle Aktien aus einem buy werden verkauft, also wird er buy gelöscht. /oder amount erstmal auf null gesetzt.
						elif available_shares_depot < shares_to_sell:
							buy_date = each['date']
							# neue Aktienanzahl in dem buy
							new_amount = 0
							# der Wert, der mit dem Verkauf auf das Budget gerechnet wird
							budget = float(exist[0]['budget'])
							share_value_sell = float(_sellValue) * float(shares_to_sell)
							new_budget = budget + share_value_sell
							# in diesem if können alle Aktien verkauft werden, daher wird shares_to_sell auf 0 gesetzt.
							shares_to_sell = shares_to_sell - available_shares_depot
							# update der DB							
							myquery = {'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.stock.date': buy_date}
							newvalues = {'$pull':{'equities.$.stock':{'date': buy_date}} }
							query = mongo.db.depot.update_one(myquery, newvalues)
				elif total_amount < _amount:
					resp = jsonify('You cannot sell more shares than you have!')
					resp.status_code = 403
					return resp
			else:
				return not_found()
		else:
			return not_found()
		
@app.route('/test', methods=['GET'])
def test():
	print("test")
	print("http://host.docker.internal" + "/equities/SAP/latest")
	r = requests.get(Stock_API + "/equities/SAP/latest")
	_json = r.json()
	_sellValue = _json["Global Quote"]["05. price"]
	resp = jsonify(_json)
	resp.status_code = 200
	return resp

@app.route('/', methods=['GET'])
def index():
	resp = jsonify("hallo??")
	print(app.config)
	print("test")
	resp.status_code = 200
	return resp
		
@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0')