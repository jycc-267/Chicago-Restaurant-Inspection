from os import path
import logging # Logging Library
from errors import KeyNotFound, BadRequest, InspError
from datetime import datetime
import string
import jellyfish

# Utility factor to allow results to be used like a dictionary
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def to_json_list(cursor):
    """
    # helper function that converts query result to json list, after cursor has executed a query
    # this will not work for all endpoints directly, just the ones where you can translate
    # a single query to the required json.
    """
    results = cursor.fetchall()
    headers = [d[0] for d in cursor.description]
    return [dict(zip(headers, row)) for row in results] # list of dicts where dict is a record of a relation


class DB:
    """
    Wraps a single connection to the database with higher-level functionality.
    """
    def __init__(self, connection):
        self.conn = connection

    def execute_script(self, script_file):
        with open(script_file, "r") as script:
            c = self.conn.cursor()
            # Only using executescript for running a series of SQL commands.
            c.executescript(script.read())
            self.conn.commit()
    
    def create_script(self):
        """
        Calls the schema/create.sql file
        """
        script_file = path.join("schema", "create.sql")
        if not path.exists(script_file):
            raise InspError("Create Script not found")
        self.execute_script(script_file)

    def seed_data(self):
        """
        Calls the schema/seed.sql file
        """
        script_file = path.join("schema", "seed.sql")
        if not path.exists(script_file):
            raise InspError("Seed Script not found")
        self.execute_script(script_file)


    def find_restaurant(self, restaurant_id):
        """
        Searches for the restaurant with the given ID. Returns None if the
        restaurant cannot be found in the database.
        """
        if not restaurant_id:
            raise InspError("No Restaurant Id", 404)
        # TODO milestone 1
        c = self.conn.cursor() # ? placeholder is used to bind data to the query
        c.execute("select * from ri_restaurants where id = ?", (restaurant_id,))
        res = to_json_list(c)
        self.conn.commit()
        if res == None:
            httpResponseCode = 404
            return None, httpResponseCode 
        else:
            res = res[0] # simply extract the first restaurant from the json list (all records refer to same restaurant)
            httpResponseCode = 200
            return res, httpResponseCode

    def find_restaurant_by_inspection_id(self, inspection_id):
        if not inspection_id:
            raise InspError("No inspection_id", 404)
        """
        Searches for the inspection with the given ID. Returns None if the
        inspection cannot be found in the database.
        """
        # TODO milestone 1
        c = self.conn.cursor()
        c.execute("select * from ri_restaurants where id in (select restaurant_id from ri_inspections where id = ?)", (inspection_id,))
        res = to_json_list(c)
        self.conn.commit()
        if not res:
            httpResponseCode = 404
            return None, httpResponseCode 
        else:
            res = res[0]
            httpResponseCode = 200
            return res, httpResponseCode
    
    def find_linked_restaurants_by_inspection_id(self, inspection_id):
        if not inspection_id:
            raise InspError("No inspection_id", 404)
        c = self.conn.cursor()
        primary = """SELECT DISTINCT primary_rest_id FROM ri_linked WHERE original_rest_id IN (SELECT restaurant_id FROM ri_inspections WHERE id = ?)"""
        #primary = """SELECT restaurant_id FROM ri_inspections WHERE id = ?"""
        linked = """SELECT original_rest_id FROM ri_linked WHERE primary_rest_id = ? AND original_rest_id != primary_rest_id"""
        ids = []

        c.execute(primary, (inspection_id,))
        primary_id = c.fetchone()[0]
       
        c.execute("""SELECT * FROM ri_restaurants WHERE id = ?""", (primary_id,))
        primary_rest = to_json_list(c)[0]

        # has not been cleaned
        if primary_rest["clean"] == False:
            linked_rests = []
            return primary_rest, linked_rests, ids

        c.execute(linked, (primary_id,))
        linked_ids = c.fetchall()
        for id in linked_ids:
            ids.append(id[0])
        
        questionmarks = ['?'] * len(ids)
        matchID = """SELECT * FROM ri_restaurants WHERE id in (%s) order by id""" % (",").join(questionmarks)
        c.execute(matchID, ids)
        linked_rests = to_json_list(c)
        ids.append(primary_id)
        ids.sort()
        return primary_rest, linked_rests, ids

    def find_restaurant_tweet_by_restaurant_id(self, restaurant_id):
        c = self.conn.cursor()
        c.execute("select tkey, match from ri_tweetmatch where restaurant_id = ? order by tkey", (restaurant_id,))
        res = to_json_list(c)
        self.conn.commit()
        # if not res:
        #     httpResponseCode = 404
        #     return None, httpResponseCode 
        # else:
        httpResponseCode = 200
        return res, httpResponseCode

    def find_inspections(self, restaurant_id):
        """
        Searches for all inspections associated with the given restaurant.
        Returns an empty list if no matching inspections are found.
        """
        if not restaurant_id:
            raise InspError("Not Restaurant Id", 404)
        # TODO milestone 1
        c = self.conn.cursor()
        c.execute("select id, risk, inspection_date, inspection_type, results, violations from ri_inspections where restaurant_id = ? order by id", (restaurant_id,))
        res = to_json_list(c) # fetchall() returns [] if the output of execute() is empty
        self.conn.commit()
        if len(res) == 0:
            return None
        else:
            return res
    

    def add_inspection_for_restaurant(self, inspection, restaurant):
        """
        Finds or creates the restaurant then inserts the inspection and
        associates it with the restaurant. Note that the arguments 
        inspection and restaurant originate from a same post body.
        Refer to load_inspection() and https://people.cs.uchicago.edu/~aelmore/class/30235/RestInsp.html#tag/MS1
        """
        # TODO milestone 1
        c = self.conn.cursor()

        # extract test restaurant and inspection data from json dicts by key of attributes
        try:
            # attributes belong to restaurant
            name = restaurant["name"]
            facType = restaurant["facility_type"]
            address = restaurant["address"]
            city = restaurant["city"]
            state = restaurant["state"]
            zip = restaurant["zip"]
            lat = restaurant["latitude"]
            long = restaurant["longitude"]

            # attributes belong to inspection
            id = inspection["inspection_id"]
            risk = inspection["risk"]
            insDate = datetime.strptime(inspection["date"], "%m/%d/%Y")
            insType = inspection["inspection_type"]
            results = inspection["results"]
            violations = inspection["violations"]
        except KeyError as e:
            raise BadRequest(message="Required attribute is missing")
        
        # match restaurant and inspection records on their names and addresses
        matchRestaurant = """SELECT * FROM ri_restaurants WHERE name = ? AND address = ?"""
        matchInspection = """SELECT * FROM ri_inspections WHERE id = ?"""

        c.execute(matchRestaurant, (name, address))
        resRestaurant = c.fetchone()
        c.execute(matchInspection, (id,))
        resInspection = to_json_list(c) # fetcll all the results of query and parse them into a list of dicts
        
        if not resRestaurant and not resInspection: # both restaurant and its inspetion not recorded in DB 
            addRestaurant = """INSERT INTO ri_restaurants
                                    (name, facility_type, address,
                                    city, state, zip,
                                    latitude, longitude)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            c.execute(addRestaurant, (name, facType, address, city, state, zip, lat, long)) # the content of cursor will change dynamically whenever the execute() runs
            restaurant_id = c.lastrowid # read-only attribute that provides the row id of the last inserted row.
            
            addInspection = """INSERT INTO ri_inspections
                                    (id, risk, inspection_date,
                                    inspection_type, results,
                                    violations, restaurant_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)"""
            c.execute(addInspection, (id, risk, insDate, insType, results, violations, restaurant_id))
            httpResponseCode = 201
            return ({"restaurant_id": restaurant_id}, httpResponseCode)
        elif resRestaurant and not resInspection: # restaurant recorded but without inspection in DB
            restaurant_id = resRestaurant[0]
            addInspection = """INSERT INTO ri_inspections
                                    (id, risk, inspection_date,
                                    inspection_type, results,
                                    violations, restaurant_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)"""
            c.execute(addInspection, (id, risk, insDate, insType, results, violations, restaurant_id))
            httpResponseCode = 200
            return ({"restaurant_id": restaurant_id}, httpResponseCode)
        else: # both restaurant and its inspection are already included in DB
            # do nothing and return restaurant_id
            restaurant_id = resRestaurant[0]
            httpResponseCode = 200
            return ({"restaurant_id": restaurant_id}, httpResponseCode)

    def count_inspection_records(self):
        c = self.conn.cursor()
        countRecords = """SELECT count(*) FROM ri_inspections"""
        c.execute(countRecords)
        res = c.fetchone()
        httpResponseCode = 200
        return res[0], httpResponseCode

    def rollback(self):
        c = self.conn.cursor()
        abort = """ROLLBACK"""
        c.execute(abort)

    def add_tweet(self, tweet):
        c = self.conn.cursor()
        rest_names = []

        try:
            # attributes belong to a tweet
            key = tweet["key"]
            lat = tweet["lat"]
            long = tweet["long"]
            text = tweet["text"]
        except KeyError as e:
            raise BadRequest(message="Required attribute is missing")

        # n-gram for loop n = 1-4
        for i in range(1,5):
            rest_name = ngrams(text, i)
            rest_names.extend(rest_name)

        questionmarks = ['?'] * len(rest_names)
        matchGeo = """SELECT id FROM ri_restaurants WHERE latitude <= ? AND latitude >= ? and longitude <= ? and longitude >= ?"""
        matchName = """SELECT id FROM ri_restaurants WHERE name in (%s)""" % (",").join(questionmarks)
        #Insert the tweet onto ri_tweetmatch
        addTweet = """INSERT INTO ri_tweetmatch
                            (tkey, restaurant_id, match)
                            VALUES (?, ?, ?)"""
        
        c.execute(matchName, rest_names)
        nameRestID = c.fetchall()
        geoRestID = None
        if lat and long:
            c.execute(matchGeo, (float(lat)+0.00225001, float(lat)-0.00225001, float(long)+0.00302190, float(long)-0.00302190))
            geoRestID = c.fetchall()
        

        if nameRestID and geoRestID:
             # match by both
            restID = []
            bothID = []
            both = "both"
            
            set_name = set(nameRestID)
            set_geo = set(geoRestID)
            interID = list(set_name.intersection(set_geo)) # if name or geo = interID = []
            unionID = list(set_name.intersection(set_geo))
            difGeoID = list(set_geo.difference(set_name)) # if both difgeoid = [] if geo difgeoid = geoid if name difgeoid = []
            difNameID = list(set_name.difference(set_geo))
            
            if difGeoID:
                geo = "geo"
                for i in difGeoID:
                    res = int(''.join(map(str, i)))
                    restID.append(res)
                for id in restID:
                    c.execute(addTweet, (key, id, geo))
                    self.conn.commit()
                restID = []
            if difNameID:
                name = "name"
                for i in difNameID:
                    res = int(''.join(map(str, i)))
                    restID.append(res)
                for id in restID:
                    c.execute(addTweet, (key, id, name))
                    self.conn.commit()
                restID = []
            for i in interID:
                res = int(''.join(map(str, i)))
                restID.append(res)
            for id in restID:
                c.execute(addTweet, (key, id, both))
                self.conn.commit()
            for i in unionID:
                res = int(''.join(map(str, i)))
                bothID.append(res)
            return bothID
        elif (nameRestID and not geoRestID):
            # match by name
            restID = []
            name = "name"
            #restID.append(nameRestID[0])
            for i in nameRestID:
                res = int(''.join(map(str, i)))
                restID.append(res)
            for id in restID:
                c.execute(addTweet, (key, id, name))
                self.conn.commit()
            return restID
        elif (not nameRestID and geoRestID):
            # match by latitude and longitude
            restID = []
            geo = "geo"
            
            # restID.append(geoRestID[0])
            for i in geoRestID:
                res = int(''.join(map(str, i)))
                restID.append(res)
            for id in restID:
                c.execute(addTweet, (key, id, geo))
                self.conn.commit()
            return restID
        else:
            return []


    def create_temporary_tables(self):
        c = self.conn.cursor()
        c.execute("DROP TABLE IF EXISTS temp_block")
        c.execute("""
            CREATE TEMP TABLE temp_block AS
            SELECT *,
                   substr(zip, 1, 5) AS zip_block,
                   substr(name, 1, 1) AS name_block
            FROM ri_restaurants 
            WHERE clean = FALSE
        """)
        self.conn.commit()


    def match_restaurant_blocking(self):
        c = self.conn.cursor()
        self.create_temporary_tables()

        # Create an index on the temporary table for blocking
        c.execute("""CREATE INDEX idx_zip ON temp_block(zip_block)""")
        self.conn.commit()

        c.execute("SELECT DISTINCT zip_block, name_block FROM temp_block")
        blocks = to_json_list(c)
        
        primary_id_tracker = []

        for block in blocks:
            name_block, zip_block = block["name_block"], block["zip_block"], 
            
            # Fetch all records within the current block
            c.execute("SELECT * FROM temp_block WHERE name_block = ? AND zip_block = ?", (name_block, zip_block))
            block_records = to_json_list(c)


            # Iterate through each dirty restaurant
            for restaurant in block_records:
                # Compare against every other record in the block
                potential_matches = [r for r in block_records if r["id"] != restaurant["id"]]

                # Initialize list to store linked records
                linked_records = []

                for match in potential_matches:
                    # Calculate similarity scores for selected attributes
                    name_similarity = jellyfish.jaro_winkler_similarity(restaurant["name"], match["name"])  
                    address_similarity = jellyfish.jaro_winkler_similarity(restaurant["address"], match["address"])  
                    city_similarity = jellyfish.jaro_winkler_similarity(restaurant["city"], match["city"]) 
                    state_similarity = 1 if restaurant["state"] == match["state"] else 0  
                    zip_similarity = 1 if restaurant["zip"] == match["zip"] else 0 

                    # Combine similarity scores using a linear model by average
                    overall_similarity = (0.3*name_similarity + 0.3*address_similarity + 0.15*city_similarity + 
                                        0.15*state_similarity + 0.1*zip_similarity)

                    if overall_similarity > 0.8: # Similarity threshold for considering a match
                        linked_records.append(match) # Add matching record to linked list

                # Check if any linked records were found
                if linked_records:
                    linked_records.append(restaurant)
                    primary_record = choose_primary_record(linked_records) # dict

                    # Insert entries into ri_linked table if primary record is dirty
                    if primary_record["id"] not in primary_id_tracker:
                        for linked_record in linked_records:
                                # Insert into ri_linked table
                                c.execute("INSERT INTO ri_linked (primary_rest_id, original_rest_id) VALUES (?, ?)", 
                                        (primary_record["id"], linked_record["id"]))

                                # Update ri_inspections for all linked records to point to the selected primary record
                                c.execute("UPDATE ri_inspections SET restaurant_id = ? WHERE restaurant_id = ?", 
                                        (primary_record["id"], linked_record["id"]))
                        # Mark the set of selected records as clean
                        c.execute("UPDATE ri_restaurants SET clean = TRUE WHERE id IN ({})".format(','.join([str(r["id"]) for r in linked_records])))
                        primary_id_tracker.append(primary_record["id"])
                        self.conn.commit()

                # If a record has no candidate matches, mark the record as clean.
                else:
                    c.execute("INSERT INTO ri_linked (primary_rest_id, original_rest_id) VALUES (?, ?)", 
                                    (restaurant["id"], restaurant["id"]))
                    c.execute("UPDATE ri_restaurants SET clean = TRUE WHERE id = ?", (restaurant["id"],))
                    c.execute("UPDATE ri_inspections SET restaurant_id = ? WHERE restaurant_id = ?", 
                                    (restaurant["id"], restaurant["id"]))
                    primary_id_tracker.append(restaurant["id"])
                    self.conn.commit()

    def match_restaurant(self):
        c = self.conn.cursor()

        # Fetch all dirty and claened restaurants
        dirty = """SELECT * FROM ri_restaurants WHERE clean = FALSE"""
        clean = """SELECT * FROM ri_restaurants WHERE clean = TRUE"""

        c.execute(dirty)
        dirty_restaurants = to_json_list(c) # list of dicts

        c.execute(clean)
        cleaned_restaurants = to_json_list(c)

        all_restaurants = dirty_restaurants + cleaned_restaurants

        primary_id_tracker = []
        # Iterate through each dirty restaurant
        for restaurant in dirty_restaurants:
            # Compare against every other record in the ri_restaurant (clean and dirty)
            potential_matches = [r for r in all_restaurants if r["id"] != restaurant["id"]]

            # Initialize list to store linked records
            linked_records = []

            for match in potential_matches:
                # Calculate similarity scores for selected attributes
                name_similarity = jellyfish.jaro_winkler_similarity(restaurant["name"], match["name"])  
                address_similarity = jellyfish.jaro_winkler_similarity(restaurant["address"], match["address"])  
                city_similarity = jellyfish.jaro_winkler_similarity(restaurant["city"], match["city"]) 
                state_similarity = 1 if restaurant["state"] == match["state"] else 0  
                zip_similarity = 1 if restaurant["zip"] == match["zip"] else 0 

                # Combine similarity scores using a linear model by average
                overall_similarity = (0.3*name_similarity + 0.3*address_similarity + 0.15*city_similarity + 
                                      0.15*state_similarity + 0.1*zip_similarity)

                if overall_similarity > 0.8: # Similarity threshold for considering a match
                    linked_records.append(match) # Add matching record to linked list

            # Check if any linked records were found
            if linked_records:
                linked_records.append(restaurant)
                primary_record = choose_primary_record(linked_records) # dict

                # Insert entries into ri_linked table if primary record is dirty
                if primary_record["id"] not in primary_id_tracker:
                    for linked_record in linked_records:
                            # Insert into ri_linked table
                            c.execute("INSERT INTO ri_linked (primary_rest_id, original_rest_id) VALUES (?, ?)", 
                                    (primary_record["id"], linked_record["id"]))

                            # Update ri_inspections for all linked records to point to the selected primary record
                            c.execute("UPDATE ri_inspections SET restaurant_id = ? WHERE restaurant_id = ?", 
                                    (primary_record["id"], linked_record["id"]))
                    # Mark the set of selected records as clean
                    c.execute("UPDATE ri_restaurants SET clean = TRUE WHERE id IN ({})".format(','.join([str(r["id"]) for r in linked_records])))
                    primary_id_tracker.append(primary_record["id"])
                    self.conn.commit()

            # If a record has no candidate matches, mark the record as clean.
            else:
                c.execute("INSERT INTO ri_linked (primary_rest_id, original_rest_id) VALUES (?, ?)", 
                                  (restaurant["id"], restaurant["id"]))
                c.execute("UPDATE ri_restaurants SET clean = TRUE WHERE id = ?", (restaurant["id"],))
                c.execute("UPDATE ri_inspections SET restaurant_id = ? WHERE restaurant_id = ?", 
                                  (restaurant["id"], restaurant["id"]))
                primary_id_tracker.append(restaurant["id"])
                self.conn.commit()

    # Simple example of how to execute a query against the DB.
    # Again NEVER do this, you should only execute parameterized query
    # See https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.execute
    # This is the qmark style:
    # cur.execute("insert into people values (?, ?)", (who, age))
    # And this is the named style:
    # cur.execute("select * from people where name_last=:who and age=:age", {"who": who, "age": age})
    def run_query(self, query):
        c = self.conn.cursor()
        c.execute(query)
        res =to_json_list(c)
        self.conn.commit()
        return res

def ngrams(tweet, n):
        """
        A helper function that will take text and split it into n-grams based on spaces.
        """
        single_word = tweet.translate(
            str.maketrans('', '', string.punctuation)).split()
        output = []
        for i in range(len(single_word) - n + 1):
            output.append(' '.join(single_word[i:i + n]))
        return output

def choose_primary_record(linked_records):
    # choose the record with smallest restaurant id as primary record
    # replace the "name" and "address" with the longest name and address among all linked records
    new_name = max(linked_records, key=lambda x: len(x["name"]))["name"]
    new_address = max(linked_records, key=lambda x: len(x["address"]))["address"]
    primary_record = min(linked_records, key=lambda x: x["id"])
    primary_record["name"] = new_name
    primary_record["address"] = new_address
    return primary_record