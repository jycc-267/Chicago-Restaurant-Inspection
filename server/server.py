import json  # For reading and writing results
from flask import current_app, g, Flask, flash, jsonify, redirect, render_template, request, session, Response
import requests  # Used for web/html wrapper
import argparse  # Used for getting arguments for creating server
import sqlite3  # Our DB
import logging  # Logging Library
from db import DB  # our custom data access layer
from errors import KeyNotFound, BadRequest, InvalidUsage # Custom Error types
import string  # for ngram generation


# Configure application
app = Flask(__name__)

app.config['JSON_SORT_KEYS'] = False

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Track transaction size
app.config["TRANSACTION_SIZE"] = 1

# Track the number of times inspections are called
app.config["INSPECTION_IN_TRANSACTION"] = 0

# Track the state of transaction
app.config["ACTIVE_TRANSACTION"] = False

# Needed to flash messages
app.secret_key = b'mEw6%7BPK'

# Static variables
DATABASE = 'insp.db' # path to database
KEY_RESTAURANT = ["name", "facility_type", "address", "city", "state", "zip", "latitude", "longitude"] # attributes of restaurant records 
KEY_INSPECTION = ["inspection_id", "risk", "date", "inspection_type", "results", "violations"] # attributes of inspection records
KEY_TWEET = ["key", "author", "created_at", "source", "lat", "long", "text"] # keys of tweet json objects

def get_db_conn():
    """ 
    gets connection to database
    """
    if "_database" not in app.config:
        # create a connection to the DB insp.db in the current working directory
        app.config["_database"] = sqlite3.connect(DATABASE)
        return app.config["_database"] 
    else:
        return app.config["_database"] 

# default path
@app.route('/')
def home():
    return render_template("home.html")

# Hello, World
@app.route("/hello", methods=["GET"])
def hello():
    return "Hello, World!"


@app.route("/create", methods=["GET"])
@app.route("/reset", methods=["GET"])
def create():
    logging.debug("Running Create/Reset")
    db = DB(get_db_conn())
    db.create_script()
    return {"message": "created"}


@app.route("/seed", methods=["GET"])
def seed():
    db = DB(get_db_conn())
    db.seed_data()
    return {"message": "seeded"}


@app.route("/restaurants/<int:restaurant_id>", methods=["GET"])
def find_restaurant(restaurant_id):
    """
    Returns a restaurant and all of its associated inspections.
    """
    db = DB(get_db_conn())

    # TODO milestone 1
    try:
        restaurant, httpResponseCode = db.find_restaurant(restaurant_id)
        inspections = db.find_inspections(restaurant_id)
        restaurant["inspections"] = inspections
        return jsonify(restaurant), httpResponseCode
    except KeyNotFound as e:
        logging.error(e)
        raise InvalidUsage(e.message, status_code=404)
    except sqlite3.Error as e:
        logging.error(e)
        raise InvalidUsage(str(e))


@app.route("/restaurants/by-inspection/<inspection_id>", methods=["GET"])
def find_restaurant_by_inspection_id(inspection_id):
    """
    Returns a restaurant associated with a given inspection.
    """
    db = DB(get_db_conn())

    # TODO milestone 1
    try:
        restaurant, httpResponseCode = db.find_restaurant_by_inspection_id(inspection_id)
        return jsonify(restaurant), httpResponseCode
    except KeyNotFound as e:
        logging.error(e)
        raise InvalidUsage(e.message, status_code=404)
    except sqlite3.Error as e:
        logging.error(e)
        raise InvalidUsage(str(e))
    
@app.route("/restaurants/all-by-inspection/<inspection_id>",methods=["GET"])
def find_all_restaurants_by_inspection_id(inspection_id):
    # TODO milestone 3
    db = DB(get_db_conn())
    rest_set = {}
    try:
        primary_restaurant, linked_restaurants, ids = db.find_linked_restaurants_by_inspection_id(inspection_id)
        rest_set["primary"] = primary_restaurant # dict
        rest_set["linked"] = linked_restaurants # list of dicts
        rest_set["ids"] = ids # list of int
        return jsonify(rest_set), 200
    except KeyNotFound as e:
        logging.error(e)
        raise InvalidUsage(e.message, status_code=404)
    except sqlite3.Error as e:
        logging.error(e)
        raise InvalidUsage(str(e))


@app.route("/inspections", methods=["POST"])
def load_inspection():
    """
    Loads a new inspection (and possibly a new restaurant) into the database.
    Note that if db or server throws a KeyNotFound, BadRequest or InvalidUsage error
    the web framework will automatically generate the right error response.
    """
    db = DB(get_db_conn())

    # TODO milestone 1
    post_body = request.get_json() # parse the incoming JSON request data into dicts
    if not post_body:
        logging.error("No post body")
        return Response(status=400)
    
    # extract restaurant and inspection data respectively from the post body
    restaurant = {key:value for key, value in post_body.items() if key in KEY_RESTAURANT}
    inspection = {key:value for key, value in post_body.items() if key in KEY_INSPECTION}
    
    try:
        # add a record via the DB class
        resp, httpResponseCode = db.add_inspection_for_restaurant(inspection, restaurant)
        app.config["INSPECTION_IN_TRANSACTION"] += 1
        if app.config["INSPECTION_IN_TRANSACTION"] == app.config["TRANSACTION_SIZE"]:
            commit_txn()
        logging.info("Response : %s" % resp)
        return resp, httpResponseCode
    except BadRequest as e:
        abort_txn()
        raise InvalidUsage(e.message, status_code=e.error_code)
    except sqlite3.Error as e:
        abort_txn()
        logging.error(e)
        raise InvalidUsage(str(e))


@app.route("/txn/<int:txnsize>", methods=["GET"])
def set_transaction_size(txnsize):
    # TODO milestone 2
    app.config["TRANSACTION_SIZE"] = txnsize
    if app.config["ACTIVE_TRANSACTION"]:
        commit_txn()
    else:
        app.config["ACTIVE_TRANSACTION"] = True
    return Response(status=200)
    


@app.route("/commit")
def commit_txn():
    logging.info("Committing active transactions")
    # TODO milestone 2
    db = DB(get_db_conn())
    if app.config["ACTIVE_TRANSACTION"]:
        db.conn.commit()
        app.config["ACTIVE_TRANSACTION"] == False
        app.config["INSPECTION_IN_TRANSACTION"] = 0
        return Response(status=200)
    #    return str(httpResponseCode)
    # do the branching based on def set_transaction_size(txnsize)
    # still need a counter to track whether the time calling add_inspection_for_restaurant reaches txnsize


@app.route("/abort")
def abort_txn():
    logging.info("Aborting/rolling back active transactions")
    # TODO milestone 2
    db = DB(get_db_conn())
    if app.config["INSPECTION_IN_TRANSACTION"] == 0:
        return Response(status=200)
    else:
        db.rollback()
        app.config["ACTIVE_TRANSACTION"] = False            
        app.config["INSPECTION_IN_TRANSACTION"] = 0
        return Response(status=200)
        

@app.route("/count")
def count_insp():
    logging.info("Counting Inspections")
    # TODO milestone 2
    db = DB(get_db_conn())
    count, httpResponseCode = db.count_inspection_records()
    return str(count), httpResponseCode


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


@app.route("/tweet", methods=["POST"])
def tweet():
    logging.info("Checking Tweet")
    # TODO milestone 2
    db = DB(get_db_conn())
    post_body = request.get_json() # parse the incoming JSON request data into dicts
    if not post_body:
        logging.error("No post body")
        return Response(status=400)
    
    tweet = {key:value for key, value in post_body.items() if key in KEY_TWEET}
    try:
        # add a record via the DB class
        tweet_id = db.add_tweet(tweet)
        return tweet_id, 201
    except BadRequest as e:
        raise InvalidUsage(e.message, status_code=e.error_code)
    except sqlite3.Error as e:
        logging.error(e)
        raise InvalidUsage(str(e))


@app.route("/tweets/<int:restaurant_id>", methods=["GET"])
def find_restaurant_tweets(restaurant_id):
    """
    Returns a restaurant's associated tweets (tkey and match).
    """
    db = DB(get_db_conn())

    # TODO milestone 2
    try:
        tweet, httpResponseCode = db.find_restaurant_tweet_by_restaurant_id(restaurant_id)
        return jsonify(tweet), httpResponseCode
    except KeyNotFound as e:
        logging.error(e)
        raise InvalidUsage(e.message, status_code=404)
    except sqlite3.Error as e:
        logging.error(e)
        raise InvalidUsage(str(e))


@app.route("/clean")
def clean():
    logging.info("Cleaning Restaurants")
    # TODO milestone 3
    db = DB(get_db_conn())
    if app.config['scaling'] == True:
        db.match_restaurant_blocking()
    else:
        db.match_restaurant()
    return Response(status=200)

# -----------------
# Web APIs
# These simply wrap requests from the website/browser and
# invoke the underlying REST / JSON API.
# -------------------

@app.route('/web/query', methods=["GET", "POST"])
def query():
    """
    runs pasted/entered query
    """
    data = None
    if request.method == "POST":
        qry = request.form.get("query")
        # Ensure query was submitted

        # get DB class with new connection
        db = DB(get_db_conn())

        # note DO NOT EVER DO THIS NORMALLY (run SQL from a client/web directly)
        # https://xkcd.com/327/
        try:
            res = db.run_query(str(qry))
        except sqlite3.Error as e:
            logging.error(e)
            return render_template("error.html", errmsg=str(e), errcode=400)

        data = res
    return render_template("query.html", data=data)


@app.route('/web/post_data', methods=["GET", "POST"])
def post_song_web():
    """
    runs simple post request
    """
    data = None
    if request.method == "POST":
        parameter = request.form.get("path")
        if parameter is None or parameter.strip() == "":
            flash("Must set key")
            return render_template("post_data.html", data=data)

        get_url = "%s/%s" % (app.config['addr'], parameter)
        logging.debug("Making request to %s" % get_url)
        # grab the response

        j = json.loads(request.form.get("json_data").strip())
        logging.debug("Json from form: %s" % j)
        r = requests.post(get_url, json=j)
        if r.status_code >= 400:
            logging.error("Error.  %s  Body: %s" % (r, r.content))
            return render_template("error.html", errmsg=r.json(), errcode=r.status_code)

        else:
            flash("Ran post command")
        return render_template("post_data.html", data=None)
    return render_template("post_data.html", data=None)


@app.route('/web/create', methods=["GET"])
def create_web():
    get_url = "%s/create" % app.config['addr']
    logging.debug("Making request to %s" % get_url)
    # grab the response
    try:
        r = requests.get(get_url)
        if r.status_code >= 400:
            logging.error("Error.  %s  Body: %s" % (r, r.content))
            return render_template("error.html", errmsg=r.json(), errcode=r.status_code)
        else:
            flash("Ran create command")
            data = r.json()
    except Exception as e:
        logging.error("%s\n$%s %s" % (e, r, r.content))
        return render_template("error.html", errmsg=e, errcode=400)

    return render_template("home.html", data=data)


@app.route('/web/restaurants', methods=["GET", "POST"])
def rest_landing():
    data = None
    if request.method == "POST":
        path = request.form.get("path")
        # Ensure path was submitted

        parameter = request.form.get("parameter")
        if parameter is None or parameter.strip() == "":
            flash("Must set key")
            return render_template("albums.html", data=data)

        get_url = ("%s/restaurants/" % app.config['addr']) + path + parameter
        # grab the response
        logging.debug("Making call to %s" % get_url)
        r = requests.get(get_url)
        if r.status_code >= 400:
            logging.error("Error.  %s  Body: %s" % (r, r.content))
            return render_template("error.html", errmsg=r.json(), errcode=r.status_code)
        else:
            try:
                data = r.json()
                logging.debug("Web Rest got : %s" % data)
            except Exception as e:
                logging.error("%s\n$%s %s" % (e, r, r.content))
    return render_template("restaurants.html", data=data)


# -----------------
# Utilities / Errors
# -------------------

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(KeyNotFound)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = 404
    return response


@app.errorhandler(BadRequest)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = 404
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="Server hostname (default 127.0.0.1)",
        default="127.0.0.1"
    )
    parser.add_argument(
        "-p", "--port",
        help="Server port (default 30235)",
        default=30235,
        type=int
    )
    parser.add_argument(
        "-s", "--scaling",
        help="Enable large scale cleaning (MS4)",
        default=False,
        action="store_true"
    )
    parser.add_argument(
        "-l", "--log",
        help="Set the log level (debug,info,warning,error)",
        default="warning",
        choices=['debug', 'info', 'warning', 'error']
    )

    # The format for our logger
    log_fmt = '%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s'
    
    # Create the parser argument object
    args = parser.parse_args()
    if args.log == 'debug':
        logging.basicConfig(
            format=log_fmt, level=logging.DEBUG)
        logging.debug("Logging level set to debug")
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.DEBUG)
    elif args.log == 'info':
        logging.basicConfig(
            format=log_fmt, level=logging.INFO)
        logging.info("Logging level set to info")
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.INFO)
    elif args.log == 'warning':
        logging.basicConfig(
            format=log_fmt, level=logging.WARNING)
        logging.warning("Logging level set to warning")
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
    elif args.log == 'error':
        logging.basicConfig(
            format=log_fmt, level=logging.ERROR)
        logging.error("Logging level set to error")
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    # Store the address for the web app
    app.config['addr'] = "http://%s:%s" % (args.host, args.port)

    # set scale
    if args.scaling:
        app.config['scaling'] = True
    else:
        app.config['scaling'] = False
    logging.info("Scaling set to %s" % app.config['scaling'])
    logging.info("Starting Inspection Service")
    app.run(host=args.host, port=args.port, threaded=False)
