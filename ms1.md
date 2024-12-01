# Milestone 1 - Basic Loading / Reading Endpoint

In this milestone you are setting up the basic end points of your web service that will receive POST requests to store data and GET requests to read data.

See the documentation on the endpoints at http://people.cs.uchicago.edu/~aelmore/class/30235/RestInsp.html to see what functionality you will need to implement.

The code in server/ has many instances of `#TODO MS1` that represent various pieces of functionality that you need to implement to complete the milestone. If the TODO is followed by a return or raise, you will need to replace the following line with the appropriate return value. These can be found in server.py (the main web/app service) and db.py (the data access object/layer that will interface with the DBMS). You can add new classes/files to help with abstracting functionality if you want. Remember to check these in!

Please see the documentation on the API and schema at http://people.cs.uchicago.edu/~aelmore/class/30235/RestInsp.html


## Running the server
You will need to start the webserver in a tab and leave it running while you test. If you are testing the server with a command line tool, such as curl or out client, you will need to run those tools in another window/tab.

To run the server, from the project root
```
cd server
python3 server.py
```

You should see some output like
```
WARNING  [server.py:448] Logging level set to warning
 * Serving Flask app 'server' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
```

If you want to run in [debug mode](https://flask.palletsprojects.com/en/2.1.x/debugging/)
`FLASK_DEBUG=1 python3 server.py`

Note that many file changes will require you to restart the server for them to be picked up.

## Logging
Your code should not use print for debug statements. Instead we use a logging library to control what messages are shown. You can read more about Python's [simple logging library](https://docs.python.org/3/howto/logging.html#). With logging libraries you give a message and a level (debug, info,warn, error, and critical). The logger is then configured with properties such as where should the log go (e.g. a file, the screen), the message format, and the level that controls what messages should be shown (e.g. setting the log level to error, will shower error or critical messages and supress debug, info, and warn level messages). This is a good practice as it allows the amount of output to be controlled, and excessive messages (either to a screen or file) can hinder a program's performance.

Using a log let's you run a program with a controllable verbosity and we expect that your code will be relatively 'quiet' when running in error mode, unless there is an error. **Using print statements or putting debug messages that show up in the default mode (`error`) will result in a 10 point penalty!**

You set the logging level with an argument `-l` or `--log`. For example `python3 server.py -l info` will run the server with a logging level info.

You log a message by calling the level on logging.
```
logging.debug("A debug message")
logging.info("An info message")
logging.warning("A warning message")
logging.error("An error message")
```

## Step 1 Configure DB
We will be using SQLite3 for this project, which requires minimal configuration to use.  The code will assume you have a sqlite3 file called insp.db in the server/ directory. To open the database simply type `sqlite3 insp.db` in server (if you have sqlite3 installed. this should be the case by default for OSX and for Ubuntu/WSL run `sudo apt-get install sqlite3`)

You should read about using python3 and sqlite3 at https://docs.python.org/3/library/sqlite3.html and in particular: https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor 


You will then need to run the drop and create scripts against your DB. We have provided a simple end point that will run the create script for you. Visit `http://127.0.0.1:30235/create` in your browser or use `curl http://127.0.0.1:30235/create`. 

**Note** this endpoint/function can be used to reset your database if create.sql contains the ability to drop all tables before creating them (which it should).

There is also a script that will 'seed' the database with two sample records. Visit `http://127.0.0.1:30235/seed` in your browser or use `curl http://127.0.0.1 :30235/seed`. You should be able to stop the web server (ctrl+c), and then connect to the database via the sqlite3 application and query the records.  Alternatively you can use this seed function to immediately start on Step 3 (but you will still need to complete Step 2 for this milestone eventually).



## Step 2: Save Inspections
Implement the function
```
@app.post("/inspections")
def load_inspection():
```
This function will take a JSON as input (`request.json`) which you will need to parse / convert into a Python object. 

See the API specs (link above) to see what are the requirements for return (response) codes, data to be included in the return, and how the input data is formatted.

Hint, to control the response type/code you can use something like the following code that sets the response type to 201 when returning an object (this is from the sample server)
```
resp = db.add_test(post_body)
return resp, 201
```

### Test 2.1
You should be able to test this with from the data dir (assuming default host and port): 
```
curl -H "Content-Type: application/json" --data @testInsp1.json http://127.0.0.1:30235/inspections
```
or use the web interface to post data and copy the contents from testInsp1.json into the form.


Your output should include `{"restaurant_id": 1}`. Your ID may be different if you have records or have previously loaded restaurant records, but for a fresh database instance, this should be the id.

### Test 2.2
After running the step in Test 2.1, run from the data dir (assuming default host and port): 
```
curl -H "Content-Type: application/json" --data @testInsp2.json http://127.0.0.1:30235/inspections
```
or use the web interface to post data and copy the contents from testInsp3.json into the form.


Your output should include `{"restaurant_id": 1}`. Your ID may be different if you have records or have previously loaded restaurant records.

### Test 2.3
In a new terminal, while the server is running, run from the root directory 
`python3 client/client.py -f data/10/test-2-3.json`

This will invoke a series of commands based on the test file (`test-2-3.json`). These tests are in the form of a list of requests and expected request codes and/or request content/body. Take a look at the files in `data/10` to get a sense of what is in there. More tests will come soon! 


## Step 3: Read Restaurant by ID
Implement the function
```
@app.get("/restaurants/<restaurant_id:int>")
def find_restaurant(restaurant_id):
```
### Test 3.1
After running Test 2.1 or 2.2 test with
```
curl http://127.0.0.1:30235/restaurants/1
```
or go to http://127.0.0.1:30235/restaurants/1 in your favorite browser.


If you had a fresh (empty) DB before running 2.1 you should an output like (2.2 would look slightly different)
```
{
  "id": 1,
  "name": "TORTOISE CLUB",
  "facility_type": "Restaurant",
  "address": "350 N STATE ST ",
  "city": "CHICAGO",
  "state": "IL",
  "zip": "60654",
  "clean": 0,
  "latitude": 41.888895927694364,
  "longitude": -87.62820008276263,
  "inspections": [
    {
      "id": "2359211",
      "risk": "Risk 1 (High)",
      "inspection_date": "2020-01-23 00:00:00",
      "inspection_type": "Canvass",
      "results": "Pass",
      "violations": ""
    }
  ]
}
```

Then run the test file. In a new terminal, while the server is running, run from the root directory 
`python3 client/client.py -f data/10/test-3-1.json`


## Step 4: Read by Inspection
Implement the function
```
@app.get("/restaurants/by-inspection/<inspection_id>")
def find_restaurant_by_inspection_id(inspection_id):
```

### Test 4.1
After running Test 2.1 and 2.2 test with
```
curl http://127.0.0.1:30235/restaurants/by-inspection/2356959
```
or go to http://127.0.0.1:30235/restaurants/by-inspection/2356959 in your favorite browser.

If you had a fresh (empty) DB before running 2.1 you should an output like
```
{
  "id": 1,
  "name": "TORTOISE CLUB",
  "facility_type": "Restaurant",
  "address": "350 N STATE ST ",
  "city": "CHICAGO",
  "state": "IL",
  "zip": "60654",
  "clean": 0,
  "latitude": 41.888895927694364,
  "longitude": -87.62820008276263
}
```

### Test 4.2
After 4.1 test
```
curl -i http://127.0.0.1:30235/restaurants/by-inspection/111
```

and verify that your output is :

```
HTTP/1.0 404 Not Found
Date: Mon, 11 May 2020 22:57:19 GMT
Server: WSGIServer/0.2 CPython/3.8.2
Content-Length: 0
Content-Type: text/html; charset=UTF-8
```

Finally test via
`python3 client/client.py -f data/10/test-4-1.json`

## Additional Tests
We will provide some additional tests this week, which will evaluate the same endpoints but with more data.

## Fin and Write Up
Please add a write up ms1.txt about what functionality is not complete. Please indicate how much time you spent on the project and if you got stuck on any particular part.  If you worked with a partner you must specify how you divided the work. With this your MS1 should be good to go! Feel free to do additional testing. More client evaluation components will come in a future MS.