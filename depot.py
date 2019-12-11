from depotapp import app, mongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import jsonify, request
from werkzeug import generate_password_hash, check_password_hash

@app.route('/depot/addUser', methods=['POST'])
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
		resp = jsonify('User added successfully!')
		resp.status_code = 200
		return resp
	else:
		return not_found()
		
@app.route('/depot/users')
def users():
	users = mongo.db.user.find()
	resp = dumps(users)
	return resp
		
@app.route('/depot/user/<id>')
def user(id):
	user = mongo.db.user.find_one({'_id': ObjectId(id)})
	resp = dumps(user)
	return resp

@app.route('/depot/update', methods=['PUT'])
def update_user():
	_json = request.json
	_id = _json['_id']
	_name = _json['name']
	_email = _json['email']
	_password = _json['pwd']		
	# validate the received values
	if _name and _email and _password and _id and request.method == 'PUT':
		#do not save password as a plain text
		_hashed_password = generate_password_hash(_password)
		# save edits
		mongo.db.user.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, {'$set': {'name': _name, 'email': _email, 'pwd': _hashed_password}})
		resp = jsonify('User updated successfully!')
		resp.status_code = 200
		return resp
	else:
		return not_found()
		
@app.route('/depot/delete/<id>', methods=['DELETE'])
def delete_user(id):
	mongo.db.user.delete_one({'_id': ObjectId(id)})
	resp = jsonify('User deleted successfully!')
	resp.status_code = 200
	return resp

@app.route('/depot/add', methods=['POST'])
def add_depot():
	_json = request.json
	_userid = _json['id']
	_budget = _json['budget']
	# validate the received values
	if _userid and _budget and request.method == 'POST':
		# save details
		results = mongo.db.depot.find()
		print(results.count())
		id = mongo.db.depot.insert_one({'userID':_userid,'budget':_budget,"equities":[]})
		resp = jsonify('Depot added successfully!')
		resp.status_code = 200
		return resp
	else:
		return not_found()

@app.route('/depot')
def depot():
	depot = mongo.db.depot.find()
	resp = dumps(depot)
	return resp

@app.route('/depot/user/<id>')
def depots(id):
	depot = mongo.db.depot.find({'userID': id})
	resp = dumps(depot)
	return resp

@app.route('/depot/buy/<id>', methods=['PUT'])
def buy_share(id):
	_json = request.json
	_id = id
	_share = _json['share']
	_amount = _json['amount']
	# validate the received values
	if _id and request.method == 'PUT':
		# is Share already in the depot?
		exist = mongo.db.depot.find({'_id': ObjectId(id), "equities.share": _share})
		# exist will be 0 if there is no entry with this ID which contains these share.
		if exist.count() == 0:
			# missing: get the current value of one share
			# _buyValue = API
			_buyValue = 10
			# save edits
			mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id)}, { '$push': { 'equities': { '$each': [ { 'share': _share, 'amount': _amount }],}}})
			resp = jsonify('Share ' + str(_share) + ' added successfully!')
			resp.status_code = 200
			return resp
		elif len(exist[0]['equities']) > 0:
			# find out current amount
			query = mongo.db.depot.aggregate([{ "$match": { "_id": ObjectId(_id) }},{'$project':{"equities":{'$filter':{'input':"$equities", 'as':"equities", 'cond': {'$eq':['$$equities.share', _share]}}}}}])
			query_results = list(query)
			current_amount = query_results[0]['equities'][0]['amount']
			# assign new value
			new_amount = current_amount + _amount
			# update into database
			mongo.db.depot.update_one({'_id': ObjectId(_id['$oid']) if '$oid' in _id else ObjectId(_id), 'equities.share': _share}, { '$set': { 'equities.$.amount': new_amount}})
			resp = jsonify('Share ' + str(_share) + ' updated successfully! Old amount: ' + str(current_amount) + ' New amount:' + str(new_amount))
			resp.status_code = 200
			return resp
		else:
			return not_found()
	else:
		return not_found()

@app.route('/depot/sell/<id>', methods=['PUT'])
def sell_share(id):
	_json = request.json
	_id = id
	_share = _json['share']
	_amount = _json['amount']
	# validate the received values
	if _id and request.method == 'PUT':
		# is Share already in the depot?
		exist = mongo.db.depot.find({'_id': ObjectId(id), "equities.share": _share})
		print(exist[0])
		print("test")
		if len(exist[0]['equities']) > 0:
			query = mongo.db.depot.aggregate([{ "$match": { "_id": ObjectId(_id) }},{'$project':{"equities":{'$filter':{'input':"$equities", 'as':"equities", 'cond': {'$eq':['$$equities.share', _share]}}}}}])
			query_results = list(query)
			current_amount = query_results[0]['equities'][0]['amount']
			new_amount = current_amount - _amount
			print(new_amount)
			if new_amount > 0:
				print("test2")
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
				resp = jsonify('Share ' + str(_share) + ' deleted successfully!')
				resp.status_code = 200
				return resp
		else:
			return not_found()
	else:
		return not_found()



		
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