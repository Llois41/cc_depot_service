from depotapp import app, mongo, Stock_API
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import jsonify, request
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime

import requests

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
		id = mongo.db.user.insert_one({'name': _name, 'email': _email, 'pwd': _hashed_password})
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
		id = mongo.db.user.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, {'$set': {'name': _name, 'email': _email, 'pwd': _hashed_password}})
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
	return resp

@app.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
	mongo.db.user.delete_one({'_id': ObjectId(id)})
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
		id = mongo.db.depot.insert_one({'userID':_userid,'budget':_budget,"equities":[]})
		result = jsonify({'user': str(id.inserted_id) })
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
	return resp

# return all depot data to a specific user	
@app.route('/depot/user/<id>', methods=['GET'])
def depots(id):
	depot = mongo.db.depot.find({'userID': id})
	resp = dumps(depot)
	return resp

@app.route('/depot/<id>', methods=['PUT'])
def buy_share(id):
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
				r = requests.get(Stock_API + "/equities/MSFT/latest")
				_json = r.json()
				_buyValue = _json["Global Quote"]["05. price"]
				# save edits
				# mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, { '$push': { 'equities': { '$each': [ { 'share': _share, 'amount': _amount, 'buyValue': _buyValue, 'sellValue': 0 }],}}})
				mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, { '$push': { 'equities': { '$each': [ { 'share': _share, 'stock': [{'amount': _amount, 'buyValue': _buyValue, 'sellValue': 0, 'date': datetime.now() }] }],}}})
				resp = jsonify('Share ' + str(_share) + ' added successfully!')
				resp.status_code = 200
				return resp
			elif len(exist[0]['equities']) > 0:
				r = requests.get(Stock_API + "/equities/MSFT/latest")
				_json = r.json()
				_buyValue = _json["Global Quote"]["05. price"]

				# update into database
				mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.share': _share}, { '$push': {"equities.$.stock": { '$each': [{'amount': _amount, 'buyValue': _buyValue, 'sellValue': 0, 'date': datetime.now()}] }}})
				resp = jsonify('Share ' + str(_share) + ' updated successfully!' + str(_buyValue))
				resp.status_code = 200

				# # find out current amount
				# query = mongo.db.depot.aggregate([{ "$match": { "_id": ObjectId(_id) }},{'$project':{"equities":{'$filter':{'input':"$equities", 'as':"equities", 'cond': {'$eq':['$$equities.share', _share]}}}}}])
				# query_results = list(query)
				# current_amount = query_results[0]['equities'][0]['amount']
				# # assign new value
				# new_amount = current_amount + _amount
				# # update into database
				# mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.share': _share}, { '$set': { 'equities.$.amount': new_amount}})
				# resp = jsonify('Share ' + str(_share) + ' updated successfully! Old amount: ' + str(current_amount) + ' New amount:' + str(new_amount))
				# resp.status_code = 200
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
				# query = mongo.db.depot.aggregate([{ "$match": { "_id": ObjectId(_id) }},{'$project':{"equities":{'$filter':{'input':"$equities", 'as':"equities", 'cond': {'$eq':['$$equities.share', _share]}}}}}])
				# query_results = list(query)
				#query = mongo.db.depot.aggregate([{ "$match": {  "$and": [  {"_id": ObjectId(_id)  }, {"equities.share": _share }]      }} ])
								
				query = mongo.db.depot.aggregate([{ "$match":   {"share": _share } }     ])

				# query = mongo.db.depot.aggregate([{"$group": { "_id": ObjectId(_id)}}, {"total_amount": {"$sum": {'$equities.stock.amount'}}}])
				query_results = list(query)
				print(query_results)
				# current_amount = query_results[0]['equities'][0]['amount']
				# new_amount = current_amount - _amount
				# print(new_amount)
				if new_amount > 0:
					mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.share': _share}, { '$set': { 'equities.$.amount': new_amount}})
					# request current value of share
					# shareValue = 100
					# update budget
					# request current budget
					# add newBudget = budget = shareValue * _amount
					new_budget = 200
					mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, { '$set': { 'budget': new_budget}})
					resp = jsonify(str(_amount) + ' Share ' + str(_share) + ' deleted successfully!')
					resp.status_code = 200
					return resp
				elif new_amount < 0:
					resp = jsonify('You cannot sell more shares than you have!')
					resp.status_code = 403
					return resp
				elif new_amount == 0:
					# delete row
					mongo.db.depot.update({}, { '$pull': {'equities': {'share':_share, 'amount':_amount}}})
					# request current value of share
					# shareValue = 100
					# update budget
					# request current budget
					# add newBudget = budget = shareValue * _amount
					new_budget = 200
					mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, { '$set': { 'budget': new_budget}})
					resp = jsonify('Share ' + str(_share) + ' deleted successfully!')
					resp.status_code = 200
					return resp
			else:
				return not_found()
		else:
			return not_found()
		
@app.route('/test', methods=['GET'])
def test():
	r = requests.get(Stock_API + "/equities/MSFT/latest")
	_json = r.json()
	_price = _json["Global Quote"]["05. price"]
	resp = jsonify(_json)
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
    app.run(debug=True)