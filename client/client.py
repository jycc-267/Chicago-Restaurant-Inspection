import json
import argparse
import sys
import requests
from requests.exceptions import ConnectionError, ConnectTimeout
from collections import defaultdict
from os import path


class LoaderError(Exception):
    def __init__(self, message=None):
        Exception.__init__(self)
        if message:
            self.message = message
        else:
            self.message = "Loader Error"

def round_ll(p1,p2):
    if isinstance(p1,str):
        p1 = float(p1)
    if isinstance(p2,str):
        p2 = float(p2)
    return round(p1,4),round(p2,4)

# Validate the script file
def validate_script(script_file):
    with open(script_file, 'r') as file_in:
        script_dir = path.dirname(script_file)
        json_script = json.load(file_in)
        if not isinstance(json_script, list):
            raise LoaderError("Main/root JSON object in the file %s is not a list" % script_file)
        for script_obj in json_script:
            if not isinstance(script_obj, object):
                raise LoaderError("Expected object in list file")
            if "url" in script_obj and "response" in script_obj:
                pass
            elif "file" in script_obj:
                if not path.exists(path.join(script_dir, script_obj["file"])):
                    raise LoaderError("File given but does not exist %s" % script_obj["file"])
                with open(path.join(script_dir, script_obj["file"]), 'r') as test_file:
                    test_file_json = json.load(test_file)
                    if "response" not in test_file_json:
                        raise LoaderError("Test script file %s missing response %s"
                                          % (test_file, test_file_json.keys()))
                    if "post_path" and "values" in test_file_json:
                        pass
                    elif "get_path" and "tests" in test_file_json:
                        pass
                    else:
                        raise LoaderError("Test script file %s should have post_path & values, or get_path & tests %s"
                                          % (test_file, test_file_json.keys()))


# Run a single file which is made up of multiple requests to the same URL
def run_test_file(server, test_file_path, fail_on_wrong_response=True):        
    with open(test_file_path, 'r') as test_file:
        script = json.load(test_file)
        response = script["response"]
        if not isinstance(response, list):
            response = [response]
        if "post_path" in script:
            count = 0
            post_url = "%s%s" % (server, script["post_path"])
            for v in script["values"]:
                r = requests.post(post_url, json=v)
                if r.status_code not in response:
                    if fail_on_wrong_response:
                        body = r.content
                        try:
                            body = r.json()
                        except:
                            pass
                        raise LoaderError("Failure (%s) on post to %s with value: %s. Body: %s "
                                          % (r.status_code, post_url, v, body))
                else:
                    count += 1
        elif "get_path" in script:
            count = 0
            get_urlbase = "%s%s" % (server, script["get_path"])
            for v in script["tests"]:
                if "inputs" in v:
                    inputs = v["inputs"]
                    get_url = "%s/%s" % (get_urlbase, str(inputs))
                else:
                    get_url = get_urlbase
                # appending parameters into get_url
                expected = v["expected"]

                r = requests.get(get_url)
                if r.status_code not in response:
                    if fail_on_wrong_response:
                        raise LoaderError("Failure (%s) on get to %s  " % (r.status_code, get_url))
                else:
                    res = r.json()
                    if 'clean' in res and 'clean' in expected:
                        if expected['clean']==0 and res['clean'] == 'FALSE':
                            res['clean'] = 0
                        elif expected['clean']==1 and res['clean'] == 'TRUE':
                            res['clean'] = 1
                        elif expected['clean']=='TRUE' and res['clean'] == 1:
                            res['clean'] = 'TRUE'
                        elif expected['clean']=='FALSE' and res['clean'] == 0:
                            res['clean'] = 'FALSE'
                    if 'latitude' in res and 'latitude' in expected:
                        res['latitude'], expected['latitude'] = round_ll(res['latitude'],expected['latitude'])
                    if 'longitude' in res and 'longitude' in expected:
                        res['longitude'], expected['longitude'] = round_ll(res['longitude'],expected['longitude'])
                    if isinstance(expected, list) and not isinstance(res, list):
                        res = [res]
                    if expected != res:
                        if fail_on_wrong_response:
                            if config.indent:
                                expected_out = json.dumps(expected, indent=1)
                                res_out = json.dumps(res, indent=1)
                            else:
                                expected_out = expected
                                res_out = res
                            raise LoaderError("Wrong expected value on get to %s. \nExpect:%s\nGot   :%s  "
                                              % (get_url, expected_out, res_out))

                        print("===unexpected return at" + get_url + "===")
                        print("expected json: %s" % expected)
                        print("actual: %s" % r.json())
                        print("=======================")
                    else:
                        count += 1
    return count


# Run the script file that contains a list of URLS and file for testing
def run_script(script_file, cfg):
    print("Running script %s" % script_file)
    server = "http://%s:%s/" % (cfg.server, cfg.port)
    script_dir = path.dirname(script_file)
    failed = False
    with open(script_file, 'r') as file_in:
        if cfg.out:
            out_file = open(cfg.out,'w')
        json_script = json.load(file_in)
        for script in json_script:
            if "url" in script:
                get_url = "%s%s" %(server,script["url"])
                r = requests.get(get_url)
                if r.status_code != script["response"]:
                    if cfg.out:
                        out_file.write("get-%s FAILED\n"% get_url)                        
                    if cfg.nofailfast:
                        print("Failure on %s. Expected %s Got %s" % (get_url, script["response"], r.status_code))
                        failed = True
                    else:
                        if cfg.concat and not cfg.nofailfast:
                            with open(cfg.concat,"a") as of:
                                of.write("test %s FAILED\n" % cfg.name )
                        raise LoaderError("Failure on %s. Expected %s Got %s" % (get_url, script["response"], r.status_code))
                else:
                    print("Called %s" % get_url)
                    if "body" in script:
                        if r.text == script["body"]:
                            if cfg.out:
                                out_file.write("get-%s ok\n"% get_url)
                        else:                           
                            err_msg = "Failure on %s. Expected %s Got %s" % (get_url, script["body"], r.text)
                            if cfg.nofailfast:
                                print(err_msg)
                                failed = True
                            else:
                                if cfg.concat and not cfg.nofailfast:
                                    with open(cfg.concat,"a") as of:
                                        of.write("test %s FAILED\n" % cfg.name )
                                raise LoaderError(err_msg)                       
                    elif cfg.out:
                        out_file.write("get-%s ok\n"% get_url)
            else:
                try:
                    count = run_test_file(server, path.join(script_dir, script["file"]))
                    print("Ran file %s Successful %s" % (script["file"], count))
                    if cfg.out:
                        out_file.write("%s ok\n"% script["file"])                    
                except LoaderError as le:
                    if cfg.out:
                        out_file.write("%s FAILED\n"% script["file"])
                    if cfg.nofailfast:
                        print(le.message)
                        failed = True
                    else:
                        if cfg.concat and not cfg.nofailfast:
                            with open(cfg.concat,"a") as of:
                                of.write("test %s FAILED\n" % cfg.name )
                        raise le
    print("Done")
    if cfg.concat:
        with open(cfg.concat,"a") as of:
            if failed:
                of.write("test %s FAILED\n" % cfg.name )
            else:
                of.write("test %s ok\n" % cfg.name )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest="file", help="Input json script file", required=True)
    parser.add_argument("-s", "--server", help="Server hostname (default localhost)", default="127.0.0.1")
    parser.add_argument("-p", "--port", help="Server port (default 30235)", default=30235, type=int)
    parser.add_argument("-i", "--indent", help="indent compare output (default False)", default=False, action="store_true")
    parser.add_argument("-nff", "--nofailfast", help="No fail fast (stop test on first failure)", default=False, action="store_true")
    parser.add_argument("-o", "--out", help="Write out test results to file (staff only)", )
    parser.add_argument("-c", "--concat", help="Concat out final result to this file  (staff only)")
    parser.add_argument("-n", "--name", help="Concat out final result as this name. Default to file name (staff only)")

    config = parser.parse_args()
    if config.concat and not config.name:
        # Default to file name if no test name is given for this script test.
        config.name = config.file
    try:
        validate_script(config.file)
        run_script(config.file, config)
    except LoaderError as e:
        print("LoaderError: %s" % e.message)