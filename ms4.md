# Milestone 4 - Scaling Data Cleaning

In this milestone you are extending your cleaning from MS3 to handle larger datasets. In particular, you will:
 - Enable blocking of the restaurant data to limit the candidate set of potential pairs.
 - Within a block/umbrella set, you will use at least one index to accelerate look ups for at least one attribute.

**For testing, server.py has a flag -s that will set `app.config['scaling']`. In your cleaning function/endpoint. Check if this -s flag is set (`if app.config['scaling'] == True`, and if so use the new cleaning approach for this MS. Otherwise, use your cleaning approach from MS3. This will allow you to test your code's results. `python3 server.py -s`**


## Step 0 - Get Updated Datasets and dependencies

There is a larger dataset (1k) that you will need to download and unzip. Run the get.sh script in the data/ms4 directory. 
You can run the new test script with

```
python3 client/client.py -f data/ms4/ms4.json
```


You will also need to modify your sever.py to set an application variable to determine when to use scaling. The lines before `logging.info("Starting Inspection Service")` are new and need to added by you.

```python
    # set scale
    if args.scaling:
        app.config['scaling'] = True
    else:
        app.config['scaling'] = False
    logging.info("Scaling set to %s" % app.config['scaling'])
    logging.info("Starting Inspection Service")
    app.run(host=args.host, port=args.port, threaded=False)
```

## Step 1 - Enable Blocking

You should modify your cleaning process to now use blocking. Here, when your process begins, you should create a grouping of your records into mutually exclusive "blocks", based on one or more of these attributes: name, address, city, state, and zip. After creating a block of records, when carrying out matching, you will only consider records that match within the same block. For example, I take 100 records and create 3 blocks: AA BB and CC. A record in BB will only be checked against other records in BB. I strongly encourage you to use temporary tables to create these blocks. See https://database.guide/create-temporary-table-sqlite/ Remember that clean may be called multiple times, so your code for creating temp tables must be able to work in this case.

Your process should determine what temporary tables need to be created, and copy records into these temp tables (ideally these temp records have fewer data/attributes than the records in the full ri_inspections table). Your cleaning process should then iterate through each of these blocks, and perform your matching within the blocks. The output of the cleaning process is the same as MS3. Please document in MS4.txt how you created your blocks.


## Step 2 - Indexing within Blocks

For this step you will create an index within each of your blocks. This index should be used when looking for candidate records to match with this block. There are several indexes you could create, but you only need one. It should be simple and it is ok if this reduces the candidate set of records you compare with. Please document in MS4.txt how you created your indexes.

## Step 3 - Evaluate Performance

For this step you should measure and compare the time it takes to run your cleaning process for both MS3 and MS4 (you would control this using the -s flag).  You should average at least 3 runs/processes for each size (ms3/100 and ms4/1k) and type (MS3 vs MS4). Write up a short description of these results in MS4.txt. I suggest using the time command https://linuxize.com/post/linux-time-command/ to measure the run time for your loading and cleaning process. Alternatively you could instrument your clean function to record the time taken and log or print this time. 

## Step 4 - Write Up
Please add a write up m32.txt. Include about what functionality is not complete (if any). Please indicate how much time you spent on the project and if you got stuck on any particular part.  If you worked with a partner you must specify how you divided the work. You should also describe how you are blocking your data (e.g. describe the approach and motivation) and write up your performance analysis.