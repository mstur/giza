import csv
import codecs
import elasticsearch_connection
import getpass
import json
import pyodbc

from classifications import CLASSIFICATIONS, CONSTITUENTTYPES
import objects_sql

SAMPLE_OBJECTS = ('61198', '15332', '15059', '52264', '50823', '35634', '5614', '46942', '48325', '3461', '25389', '25501')

CURSOR = None

# First update each Object with the latest data
# This is the basic information/metadata that comprises a Object
def process_objects():
	def get_indices():
		id_index = columns.index('ID')
		classification_id_index = columns.index('ClassificationID')
		object_number_index = columns.index('ObjectNumber')
		return (id_index, classification_id_index, object_number_index)

	def process_object_row(object, current_id):
		id = row[id_index]
		classification_key = int(row[classification_id_index])
		classification = CLASSIFICATIONS.get(classification_key)

		#if id not in SAMPLE_OBJECTS:
		#	return (object, current_id)

		# I don't think there are any duplicate rows for objects, but keep it here since it doesn't break anything
		if id != current_id:
			save(object)
			current_id = id
			object = {}

		object['classification'] = classification
		# loop through each row
		for index, value in enumerate(columns):
			key = value.lower()
			row_value = row[index]

			# cleanup row data
			if row_value.isdigit():
				row_value = int(row_value)
			elif row_value == "NULL":
				row_value = None
			else:
				row_value = row_value.replace(',,','')

			if 'title' in key:
				object_title = row_value
				if classification == "diarypages" and object_title is None:
					object_number = row[object_number_index]
					idx = object_number.find('_')
					object_title = object_number[idx+1:]
					object[key] = object_title
				else:
					object[key] = row_value
			else:
				object[key] = row_value
		return (object, current_id)

	print "Starting Objects..."
	if CURSOR:
		sql_command = objects_sql.OBJECTS
		CURSOR.execute(sql_command)
		columns = [column[0] for column in CURSOR.description]
		(id_index, classification_id_index, object_number_index) = get_indices()

		object = {}
		current_id = '-1'
		cursor_row = CURSOR.fetchone()
		while cursor_row is not None:
			row = process_cursor_row(cursor_row)
			(object, current_id) = process_object_row(object, current_id)
			cursor_row = CURSOR.fetchone()
   		# save last object to elasticsearch
		save(object)

	else:
		with open('../data/objects.csv', 'rb') as csvfile:
			# Get the query headers to use as keys in the JSON
			headers = next(csvfile)
			if headers.startswith(codecs.BOM_UTF8):
				headers = headers[3:]
			headers = headers.replace('\r\n','')
			columns = headers.split(',')
			(id_index, classification_id_index, object_number_index) = get_indices()

			rows = csv.reader(csvfile, delimiter=',', quotechar='"')
			object = {}
			current_id = '-1'
			for row in rows:
				(object, current_id) = process_object_row(object, current_id)
			# save last object to elasticsearch
			save(object)
	
	print "Finished Objects..."

def process_object_related_constituents():
	def get_indices():
		id_index = columns.index('ID')
		role_index = columns.index('Role')
		constituent_id_index = columns.index('ConstituentID')
		constituent_type_id_index = columns.index('ConstituentTypeID')
		display_name_index = columns.index('DisplayName')
		display_date_index = columns.index('DisplayDate')
		classification_id_index = columns.index('ClassificationID')
		return (id_index, role_index, constituent_id_index, constituent_type_id_index, display_name_index, display_date_index, classification_id_index)

	def process_object_row(object, current_id):
		id = row[id_index]
		classification_key = int(row[classification_id_index])
		classification = CLASSIFICATIONS.get(classification_key)

		if id != current_id:
			# may have multiple rows for one object because of many related constituents
			save(object)
			current_id = id
			object = {}
			if elasticsearch_connection.item_exists(id, classification):
				object = elasticsearch_connection.get_item(id, classification)
			else:
				print "%s could not be found!" % id
				return(object, current_id)
		if 'relateditems' not in object:
			object['relateditems'] = {}

		constituent_id = row[constituent_id_index]
		display_name = row[display_name_index]
		display_date = ""
		if row[display_date_index] != "NULL":
			display_date = row[display_date_index]

		constituent_dict = {}
		constituent_dict['role'] = row[role_index]
		constituent_dict['id'] = constituent_id
		constituent_dict['displayname'] = display_name
		constituent_dict['displaydate'] = display_date
		constituent_dict['displaytext'] = display_name

		constituent_type_key = int(row[constituent_type_id_index])
		constituent_type = CONSTITUENTTYPES.get(constituent_type_key)
		if constituent_type not in object['relateditems']:
			object['relateditems'][constituent_type] = []
		object['relateditems'][constituent_type].append(constituent_dict)
		return(object, current_id)

	print "Starting Objects Related Constituents..."
	if CURSOR:
		sql_command = objects_sql.RELATED_CONSTITUENTS
		CURSOR.execute(sql_command)
		columns = [column[0] for column in CURSOR.description]
		(id_index, role_index, constituent_id_index, constituent_type_id_index, display_name_index, display_date_index, classification_id_index) = get_indices()

		object = {}
		current_id = '-1'
		cursor_row = CURSOR.fetchone()
		while cursor_row is not None:
			row = process_cursor_row(cursor_row)
			(object, current_id) = process_object_row(object, current_id)
			cursor_row = CURSOR.fetchone()
   		# save last object to elasticsearch
		save(object)
	else:
		with open('../data/objects_constituents_related.csv', 'rb') as csvfile:
			# Get the query headers to use as keys in the JSON
			headers = next(csvfile)
			if headers.startswith(codecs.BOM_UTF8):
				headers = headers[3:]
			headers = headers.replace('\r\n','')
			columns = headers.split(',')
			(id_index, role_index, constituent_id_index, constituent_type_id_index, display_name_index, display_date_index) = get_indices()

			rows = csv.reader(csvfile, delimiter=',', quotechar='"')
			object = {}
			current_id = '-1'
			for row in rows:
				(object, current_id) = process_object_row(object, current_id)
			# save last object to elasticsearch
			save(object)

	print "Finished Objects Related Constituents..."

def process_cursor_row(cursor_row):
	row = []
	for x in cursor_row:
		if isinstance(x, int):
			row.append(str(x))
		elif isinstance(x, unicode):
			row.append(x.encode('utf-8'))
		elif x is None:
			row.append("NULL")
		else:
			row.append(str(x))
	return row

def save(object):
	if object and 'id' in object:
		elasticsearch_connection.add_or_update_item(object['id'], json.dumps(object), object['classification'])

if __name__ == "__main__":
	try:
		dsn = 'gizadatasource'
		user = 'RC\\rsinghal'
		password = getpass.getpass()
		database = 'gizacardtms'

		connection_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
		connection = pyodbc.connect(connection_string)
		CURSOR = connection.cursor()
	except:
		print "Could not connect to gizacardtms, defaulting to CSV files"

	process_objects()
	process_object_related_constituents()