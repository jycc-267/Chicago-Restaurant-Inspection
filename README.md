# RestInsp - Basic Web Service Endpoints

In this project you are setting up basic endpoints of web service for a music service "RestInsp", which will manage (altered) data for food inspections from the city of Chicago. Note we use the restaurant but many locations in the dataset are not actually restaurants, we will treat all locations as restaurants for simplicity.

These endpoints will receive http POST requests to store data and http GET requests to read data  ([more info on request types](https://www.w3schools.com/tags/ref_httpmethods.asp)). The data will be sent and received as [JSON](https://www.w3schools.com/js/js_json_intro.asp). JSON is a simple textual data format, that can store objects (e.g. dictionary or map), a list, or primitive values. Your web service will respond to http requests with a JSON response body and a [numeric http response code](https://www.restapitutorial.com/httpstatuscodes.html) that indicates a valid request (200), that something was created (201), an unknown error occurred (400), or that a lookup did not find the requested data (404).  See the link for a detailed list of response codes. This project is a "REST"-like set up, where operations like create and read data get mapped to a URL. At its core, REST is a simple http APIs to create, read, update, and delete data using stateless web requests.  If you are interested in learning more about REST see this [link](https://www.restapitutorial.com/).

For this project, we have given you a few components to work with:
 - `server/server.py` has the skeleton code for the web/http server. All requests made to the server get mapped to a function in this file (an endpoint). These functions get arguments (either from the [URL](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/What_is_a_URL) or from data that was sent as the "body" of a post request). Most endpoints will in turn make a call to the underlying database. 
 - `server/db.py` is the data access layer. This class will hold the connection to the database (sqlite3) and provide functions that insert and read data. Almost all of your work will be in this file to start. Note you are not obligated to use our "seed" functions we give you, and alter them/add new functions here. For later milestones you will definitely need to add new ones.
 - `server/errors.py` defines some common exceptions/errors used in our provided code.
 - `client/client.py` is the client/driver for testing your application. This program reads a workload file that specifies a list of files, that each give an endpoint, an expected http response code, an optional payload (data to send), and an option response body to verify against. You will not need to change this file at all, but it will be used heavily in testing and developing your code. You should not modify the client (or if you do, do NOT commit any changes).  
 - You are free to add additional Python classes/files to handle certain aspects of your application, such as a models for holding state based on the DB and/or data access objects that provide the functions to interact with the database. Most of your changes will be in the db.py file to start. Be sure to add/check-in any new files.

The code in app.py/db.py has instances of `#TODO milestone` that represent various pieces of functionality that you need to implement to complete the milestone. If the TODO is followed by a return or raise, you will need to replace the following line with the appropriate return value. These can be found in app.py (the main web/app service) and db.py (the data access object/layer that will interface with the DBMS). You can add new classes/files/functions to help with abstracting functionality if you want. Remember to check these files in!

## Technologies Used
This assignment uses a few popular and lightweight technologies in addition to the aforementioned concepts (e.g. JSON, http). 
- Python3. We will assume you are using python3 for this assignment. It is a very simple language. [Here](https://www.stavros.io/tutorials/python/) as a quick tutorial from someplace that I found on the web after a quick search and not much checking. Python3 is very easy to install and is readily available on most OSes. 
-  [Flask](https://flask.palletsprojects.com/en/2.3.x/quickstart/) is a lightweight and popular web framework written in Python. Depending on your OS you will need to figure out how to install flask. Flask provides an easy way to map http requests to a function and return http/html/json responses.
-  [SQLite](https://www.sqlite.org/index.html) is an embedded relational database.  It does not have the full set of features as something like PostgreSQL but is very easy to use and install. We will be using the [sqlite3 database driver](https://docs.python.org/3/library/sqlite3.html) to connect and interact with the DBMS via Python.  Note that sqlite will create a single file for the entire database on the first time you access/open it.  Only one process can interact with the database at a time (single threaded). It would be unlikely that you would use sqlite for such a project, but given the ease of use of sqlite and the ubiquity of it, we choose to use it for this project.

## Python packages/library
For this project we will specify exactly what python packages/library/module you are allowed to use. Any additional package that is not specified or approved will result in a **50% point penalty** the module is used on. Use your favorite installer (pip3)  To start we will use:
 - flask (2.3)
 - requests

The best way to set up these libraries is to use a [virtual environment](https://docs.python.org/3/library/venv.html).  This creates a place to control what libraries are used for a particular project. Using a virtual environment is a good idea as it allows you to have different versions of a library installed without issue. You can also easily remove libraries when no longer needed.

Assuming you are on linux, WSL or mac these instructions should (roughly) work. A common virtual environment set up is to create one called `venv` in the root of the project.  Here you run something like `python3 -m venv venv` in the root of the project folder. You should then be able to run `ls` in the directory and see a folder called `venv/` Afterwards you should be able to "activate" the virtual environment which will control how Python libraries are used. Active the environment via `source venv/bin/activate`. You should then see `(venv) ` at the start of every line. Then you should be able to install the libraries.

pip3 is one of the easiest tools to use to install python libraries. check that pip/pip3 is install via running `pip3 --version`. If that does not work try `pip --version`. If this works, be sure to use pip instead of pip3.  To install the necessary packages use `pip3 install -r  requirements.txt` *while in the virtual environment*. requirements.txt is a list of the libraries and the necessary versions to install. If you log out or close the terminal, you will need to re-active the virtual environment to have access to the libraries.

## Sample REST Service
We have provided a small reference solution for you to work from. Please see the [SampleServer.md](SampleServer.md) write up for details on how to walk through/test the sample server. **You should get this running and familiarize yourself with the code before moving on.** 

## Requirements
See the documentation on the endpoints at [http://people.cs.uchicago.edu/~aelmore/class/30235/RestInsp.html](http://people.cs.uchicago.edu/~aelmore/class/30235/RestInsp.html) to see what functionality you will need to implement. The descriptions of the end points are basic, but contains enough information for you to complete the required functionality. This includes what the input and output should be.   

## Web/html wrapper
We have provided you with a simple web (html) interface to some of the underlying JSON Rest endpoints. This is to allow you to test the end points in a browser, as opposed to sending JSON http requests via program like CURL or Python. After starting the server, visit http://localhost:30235/ and see the top menu links to the web wrappers. In app.py these are all prefixed with /web and as you can see in the code, most of these just take the input from the form and call the REST JSON endpoint and return the results. The exception to this is the query endpoint which will let you run an arbitrary SQL statement against the database. NEVER do run arbitrary SQL outside testing/class, it is a huge security risk.

## Suggested Steps
We have provided a set of suggested steps to complete this project. Please see the [ms1.md](ms1.md) write up for details on how to complete the first milestone.

## Partners
If you work with a partner the expectation is that you both work together and are able to explain each other's code. If the work is partitioned at all you must explain how. You should not partition work by milestone, but instead partition the tasks within a milestone. Questions about the project are fair game for an exam, so it is in your benefit to understand all parts of the solution.

A partner not completing tasks is not a reason for an extension. At any point partners may split up into individuals. If so any and all source that committed and push to the team repository is available to both partners. If you split from your partner you cannot form a new partnership. Choose your partner carefully.

## AI Tools
The use of AI assisted tools (such as copilot) is disallowed for this project.  Part of learning tools, frameworks, and concepts is struggling through examples, documentations, and tests.  Using AI aided tools will rob you of the experience and knowledge. Additionally, these tools can be wrong and it is hard to understand why until you have learned the foundations. In your professional life, you may have access to these tools but it is important to be aware of potential legal and ethical pitfalls of doing so.

## Fin and Write Up
For each milestone you should complete the required write up.