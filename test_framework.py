# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Test-Framework/LICENSE.md

import argparse
import datetime
import HtmlTestRunner
import json
import jsonschema
import logging
import os
import re
import subprocess
import sys
import time
import unittest

# for NOTICE logging level (25 is between INFO and WARNING)
NOTICE = 25


class TestFramework(object):
    """
    Class TestFramework is a top-level class that represents a set of tests to be run within the Redfish
    interoperability test framework.
    """

    # config filename for TestFramework
    config_filename = "framework_conf.json"

    # sensitive config args like password that should not be logged or printed
    sensitive_args = ["password", "token"]

    # schema for TestFramework config file (framework_conf.json)
    config_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {},
        "id": "http://dmtf.org/redfish/test_framework_conf.json",
        "properties": {
            "custom_variables": {
                "id": "/properties/custom_variables",
                "patternProperties": {
                    "^[_a-z][_a-z0-9]*$": {
                        "id": "/properties/custom_variables/properties/variable",
                        "type": "string"
                    }
                },
                "additionalProperties": False,
                "type": "object"
            },
            "https": {
                "id": "/properties/https",
                "type": "string"
            },
            "interpreter": {
                "id": "/properties/interpreter",
                "type": "string"
            },
            "password": {
                "id": "/properties/password",
                "type": "string"
            },
            "target_system": {
                "id": "/properties/target_system",
                "type": "string"
            },
            "token": {
                "id": "/properties/token",
                "type": "string"
            },
            "username": {
                "id": "/properties/username",
                "type": "string"
            }
        },
        "additionalProperties": False,
        "type": "object"
    }

    def __init__(self, path):
        """
        :param path: the full path of the top-level directory defining the set of tests to be run
        """
        self.path = path
        self.config_file = None
        self.config_dict = None
        self.suite_list = list()
        self.suite_dict = dict()
        self.config_vars = dict()
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.output_subdir = "output-{:%Y-%m-%dT%H%M%SZ}".format(self.timestamp)

    def get_path(self):
        """
        :return: the full path of the top-level directory defining the set of tests to be run
        """
        return self.path

    def get_timestamp(self):
        """
        :return: the timestamp from when this class instance was created
        """
        return self.timestamp

    def set_config_file(self, config_file):
        """
        :param config_file: filename of the top-level config file (not including the path)
        """
        self.config_file = config_file

    def get_config_file(self):
        """
        :return: filename of the top-level config file (not including the path)
        """
        return self.config_file

    def set_config_data(self, config_dict):
        """
        :param config_dict: dictionary of the config data read from the top-level config file
        """
        self.config_dict = config_dict
        self.config_vars["output_subdir"] = self.output_subdir
        for var in "target_system", "username", "password", "token", "https", "interpreter":
            if var in self.config_dict:
                self.config_vars[var] = self.config_dict[var]
        if "custom_variables" in self.config_dict:
            variables = self.config_dict["custom_variables"]
            for var in variables:
                self.config_vars[var] = variables[var]
        # do not log config_vars by default (even in debug mode) - may contain sensitive vars like password
        # logging.debug("set_config_data: config_vars = {}".format(self.config_vars))

    def override_config_data(self, args):
        """
        :param args: Namespace of command-line args (from argparse)
        """
        if args.rhost is not None:
            self.config_vars["target_system"] = args.rhost
        if args.user is not None:
            self.config_vars["username"] = args.user
        if args.password is not None:
            self.config_vars["password"] = args.password
        if args.token is not None:
            self.config_vars["token"] = args.token
        if args.secure is not None:
            self.config_vars["https"] = args.secure
        if args.directory is not None:
            self.config_vars["output_subdir"] = args.directory
        if args.interpreter is not None:
            self.config_vars["interpreter"] = args.interpreter
        # do not log config_vars by default (even in debug mode) - may contain sensitive vars like password
        # logging.debug("override_config_data: config_vars = {}".format(self.config_vars))

    def substitute_config_variables(self, command_args, command_args_printable):
        """
        Perform variable substitution on the test-case-level command-line args
        using variables defined in the top-level configuration
        
        :param command_args: test-case command-line args
        :param command_args_printable: test-case command-line args with sensitive args like password obscured
        """
        if command_args is not None:
            for index, arg in enumerate(command_args):
                if arg.startswith("$"):
                    var = arg[1:]
                    if var in self.config_vars:
                        command_args[index] = self.config_vars[var]
                    else:
                        logging.warning("No variable for arg {} found".format(arg))
        if command_args_printable is not None:
            for index, arg in enumerate(command_args_printable):
                if arg.startswith("$"):
                    var = arg[1:]
                    if var in self.config_vars:
                        # mask sensitive args like password
                        if var not in TestFramework.sensitive_args:
                            command_args_printable[index] = self.config_vars[var]
                        else:
                            command_args_printable[index] = "********"
                    else:
                        logging.warning("No variable for arg {} found".format(arg))
            logging.debug("printable command args after top-level substitution: {}".format(command_args_printable))

    def get_config_data(self):
        """
        :return: the top-level config dictionary
        """
        return self.config_dict

    def add_suite(self, test_suite):
        """
        Add a TestSuite instance to the list of test suites to be run
        
        :param test_suite: a TestSuite instance
        """
        self.suite_list.append(test_suite)
        name = test_suite.get_name()
        self.suite_dict[name] = test_suite

    def get_suite(self, name):
        """
        :param name: the name of a test suite to retrieve (the name of the suite subdirectory)
        :return: the TestSuite instance matching the test suite name provided
        """
        if name in self.suite_dict:
            return self.suite_dict[name]
        else:
            return None

    def get_suites(self):
        """
        :return: the list of test suites to be run
        """
        return self.suite_list

    def get_output_subdir(self):
        """
        :return: the subdirectory name to be used for test output
        """
        return self.output_subdir


class TestSuite(object):
    """
    Class TestSuite represents a suite of tests to run within the Redfish interoperability test framework. The suite is
    defined by a subdirectory under the top-level directory for the test framework. For example, one suite can be for
    schema validation tests, another for use-case checker tests and another for interoperability profile tests.
    """

    # config filename for TestSuite
    config_filename = "suite_conf.json"

    config_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {},
        "id": "http://dmtf.org/redfish/test_suite_conf.json",
        "properties": {
            "custom_variables": {
                "id": "/properties/custom_variables",
                "patternProperties": {
                    "^[_a-z][_a-z0-9]*$": {
                        "id": "/properties/custom_variables/properties/variable",
                        "type": "string"
                    }
                },
                "additionalProperties": False,
                "type": "object"
            }
        },
        "additionalProperties": False,
        "type": "object"
    }

    def __init__(self, path, subdir):
        """
        :param path: the full path of the top-level directory defining the set of tests to be run
        :param subdir: the subdirectory for this suite of tests (not including the path)
        """
        self.path = os.path.join(path, subdir)
        self.name = subdir
        self.config_file = None
        self.config_dict = None
        self.test_list = list()
        self.test_dict = dict()
        self.custom_vars = dict()

    def get_path(self):
        """
        :return: the full path of the subdirectory for this test suite
        """
        return self.path

    def set_config_file(self, config_file):
        """
        :param config_file: filename of the config file for this suite (not including the path)
        """
        self.config_file = config_file

    def get_config_file(self):
        """
        :return: filename of the config file for this suite (not including the path)
        """
        return self.config_file

    def set_config_data(self, config_dict):
        """
        :param config_dict: dictionary of the config data read from the config file for this suite 
        """
        self.config_dict = config_dict
        if "custom_variables" in self.config_dict:
            variables = self.config_dict["custom_variables"]
            for var in variables:
                self.custom_vars[var] = variables[var]
        # do not log config_vars by default (even in debug mode) - may contain sensitive vars like password
        # logging.debug("set_config_data: custom_vars = {}".format(self.custom_vars))

    def substitute_config_variables(self, command_args, command_args_printable):
        """
        Perform variable substitution on the test-case command line args
        using variables defined in the suite-level configuration

        :param command_args: test-case command args
        :param command_args_printable: test-case command-line args with sensitive args like password obscured
        """
        if command_args is not None:
            for index, arg in enumerate(command_args):
                if arg.startswith("$"):
                    var = arg[1:]
                    if var in self.custom_vars:
                        command_args[index] = self.custom_vars[var]
                    else:
                        logging.debug("No custom variable for arg {} found".format(arg))
        if command_args_printable is not None:
            for index, arg in enumerate(command_args_printable):
                if arg.startswith("$"):
                    var = arg[1:]
                    if var in self.custom_vars:
                        # mask sensitive args like password
                        if var not in TestFramework.sensitive_args:
                            command_args_printable[index] = self.custom_vars[var]
                        else:
                            command_args_printable[index] = "********"
                    else:
                        logging.debug("No custom variable for arg {} found".format(arg))
            logging.debug("printable command args after suite-level substitution: {}".format(command_args_printable))

    def get_config_data(self):
        """
        :return: the config dictionary for this suite
        """
        return self.config_dict

    def get_name(self):
        """
        :return: the name of this test suite (the name of the suite subdirectory)
        """
        return self.name

    def add_test_case(self, test_case):
        """
        :param test_case: the test case instance to add the the lists of tests for this suite 
        """
        self.test_list.append(test_case)
        name = test_case.get_name()
        self.test_dict[name] = test_case

    def get_test_case(self, name):
        """
        :param name: the name of a test case to retrieve (the name of the test case subdirectory)
        :return: the TestCase instance matching the test case name provided
        """
        if name in self.test_dict:
            return self.test_dict[name]
        else:
            return None

    def get_test_cases(self):
        """
        :return: the list of test cases to be run for this suite
        """
        return self.test_list


class TestCase(object):
    """
    Class TestCase represents a test to run within a suite of tests in the Redfish interoperability test framework.
    The test case is defined by a subdirectory under a test suite subdirectory in the framework. For example, one
    test case in the use-case checker suite can be for a power control checker test and another for an account
    management checker test.
    
    Each TestCase can invoke one command. If a particular test program needs to be run multiple times, create a
    separate test case subdirectory for each invocation. For example, if multiple account management checker tests
    need to be run, put each one in a separate subdirectory under the appropriate test suite directory.
    """

    # config filename for TestCase
    config_filename = "test_conf.json"

    config_schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {},
        "id": "http://dmtf.org/redfish/test_case_conf.json",
        "properties": {
            "test": {
                "id": "/properties/test",
                "properties": {
                    "command": {
                        "id": "/properties/test/properties/command",
                        "type": "string"
                    },
                    "wait_seconds_after": {
                        "id": "/properties/test/properties/wait_seconds_after",
                        "minimum": 0,
                        "type": "integer"
                    }
                },
                "required": ["command"],
                "additionalProperties": False,
                "type": "object"
            }
        },
        "required": ["test"],
        "additionalProperties": False,
        "type": "object"
    }

    def __init__(self, path, subdir, output_subdir):
        """
        :param path: the full path of the suite-level directory under which this test case resides
        :param subdir: the subdirectory for this test case (not including the path)
        :param output_subdir: the subdirectory for test output (not including the path)
        """
        self.path = os.path.join(path, subdir)
        self.name = subdir
        self.output_dir = os.path.join(self.path, output_subdir)
        self.config_file = None
        self.config_dict = None
        self.command_args = None
        self.command_args_printable = None
        self.return_code = 1  # set to non-zero initially
        self.results_filename = "results.json"
        self.results = None
        self.timestamp = None
        self.wait_seconds_after = 0

    def get_path(self):
        """
        :return: the full path of the subdirectory for this test case
        """
        return self.path

    def set_config_file(self, config_file):
        """
        :param config_file: filename of the config file for this test case (not including the path)
        """
        self.config_file = config_file

    def get_config_file(self):
        """
        :return: filename of the config file for this test case (not including the path)
        """
        return self.config_file

    def set_config_data(self, config_dict):
        """
        :param config_dict: dictionary of the config data read from the config file for this test case
        """
        self.config_dict = config_dict
        test_case = self.config_dict["test"]
        if "command" in test_case:
            self.command_args = test_case["command"].split()
            self.command_args_printable = test_case["command"].split()
        if "wait_seconds_after" in test_case:
            self.wait_seconds_after = test_case["wait_seconds_after"]

    def get_command_args(self):
        """
        :return: the command line args for this test case
        """
        return self.command_args

    def get_command_args_printable(self):
        """
        :return: the command line args for this test case, with sensitive args like password obscured
        """
        return self.command_args_printable

    def get_name(self):
        """
        :return: the name of this test case (the name of the test case subdirectory)
        """
        return self.name

    def get_return_code(self):
        """
        :return: the return code from the test case execution
        """
        return self.return_code

    def get_results(self):
        """
        :return: the successful test results as a python dict()
        """
        return self.results

    def get_timestamp(self):
        """
        :return: the timestamp when this test was run
        """
        return self.timestamp

    def run(self):
        """
        Runs this test case
        """
        # Change to the directory containing the test case
        try:
            os.chdir(self.path)
        except OSError as e:
            logging.error("Unable to change directory to {}, error: {}".format(self.path, e))
            return
        # Create output directory (should NOT already exist)
        try:
            os.mkdir(self.output_dir)
        except OSError as e:
            logging.error("Unable to create output directory {}, error: {}".format(self.output_dir, e))
            return
        # Open output files for STDOUT and STDERR
        try:
            std_out_path = os.path.join(self.output_dir, "stdout.log")
            std_out_fd = open(std_out_path, "w")
            std_err_path = os.path.join(self.output_dir, "stderr.log")
            std_err_fd = open(std_err_path, "w")
        except OSError as e:
            logging.error("Unable to create output file in directory {}, error: {}".format(self.output_dir, e))
            return
        # Run test
        if self.config_dict is not None and "test" in self.config_dict:
            test_case = self.config_dict["test"]
            if self.command_args is not None:
                try:
                    logging.info("Running test in {}".format(self.name))
                    self.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    self.return_code = subprocess.call(self.command_args, stdout=std_out_fd, stderr=std_err_fd)
                    msg = "Return code {} from running test in {}".format(self.return_code, self.path)
                    if self.return_code == 0:
                        logging.info(msg)
                    else:
                        logging.error(msg)
                except OSError as e:
                    logging.error("OSError while trying to execute test in {}, error: {}".format(self.path, e))
                except ValueError as e:
                    logging.error("ValueError while trying to execute test in {}, error: {}".format(self.path, e))
                except subprocess.TimeoutExpired as e:
                    logging.error("TimeoutExpired while trying to execute test in {}, error: {}".format(self.path, e))
                else:
                    pass
                # Read the results.json file if available
                try:
                    with open(os.path.join(self.output_dir, self.results_filename)) as results_file:
                        self.results = json.load(results_file)
                except OSError as e:
                    logging.warning("OSError opening JSON results from file {} in directory {}, error: {}"
                                    .format(self.results_filename, self.output_dir, e))
                except ValueError as e:
                    logging.error("ValueError loading JSON results from file {} in directory {}, error: {}"
                                  .format(self.results_filename, self.output_dir, e))
                else:
                    pass
            else:
                logging.warning("Skipping test in {}: element 'command' missing from 'test' element {}"
                                .format(self.name, test_case))
        else:
            logging.warning("Skipping {}: test config data empty or 'test' element missing. Test config data: {}"
                            .format(self.name, self.config_dict))
        # Close output files
        std_out_fd.close()
        std_err_fd.close()
        # sleep if wait_seconds_after param provided
        if self.wait_seconds_after > 0:
            msg = "Sleeping for {} seconds after running test".format(self.wait_seconds_after)
            logging.log(NOTICE, msg)
            time.sleep(self.wait_seconds_after)


class RedfishTestCase(unittest.TestCase):
    """
    A unittest TestCase class to drive running the Redfish tests through the Python unittest framework.
    Note that there are no "test*" methods defined in this class. They are added dynamically via the
    add_test_as_unittest() function as the tests to be run are discovered and set up.

    Each of the dynamically created "test*" methods can be viewed as a stub that calls the run_test()
    method below to actually run the test, collect the results and assert that it passed.
    """

    def run_test(self, framework, suite, case, results):
        case.run()
        rc = case.get_return_code()
        if case.get_return_code() == 0:
            # add results object to summary passing results object
            if case.get_results() is not None:
                results.add_test_results_pass(case.get_results())
            else:
                test_results = create_test_results(suite.get_name(), case.get_name(),
                                                   case.get_timestamp(), case.get_command_args_printable(),
                                                   case.get_return_code())
                results.add_test_results_pass(test_results)
        else:
            # add results object to summary failing results object
            if case.get_results() is not None:
                results.add_test_results_fail(case.get_results())
            else:
                test_results = create_test_results(suite.get_name(), case.get_name(),
                                                   case.get_timestamp(), case.get_command_args_printable(),
                                                   case.get_return_code())
                results.add_test_results_fail(test_results)
        # change directory back to top-level
        try:
            os.chdir(framework.get_path())
        except OSError as e:
            logging.error("Unable to change directory to {}, error: {}".format(framework.get_path(), e))
        self.assertEqual(rc, 0, msg="Non-zero return code from test case")


class Results(object):

    def __init__(self, output_dir, timestamp):
        self.output_dir = os.path.abspath(output_dir)
        self.results_pass_filename = "results_pass.json"
        self.results_fail_filename = "results_fail.json"
        self.return_code = 0
        self.results_pass = {
            "Redfish Test Framework Passing Results": {
                "Timestamp": {
                    "DateTime": "{:%Y-%m-%dT%H:%M:%SZ}".format(timestamp)
                }
            },
            "TestCases": []
        }
        self.results_fail = {
            "Redfish Test Framework Failing Results": {
                "Timestamp": {
                    "DateTime": "{:%Y-%m-%dT%H:%M:%SZ}".format(timestamp)
                }
            },
            "TestCases": []
        }

    def add_test_results_pass(self, results_dict):
        self.results_pass["TestCases"].append(results_dict)

    def add_test_results_fail(self, results_dict):
        self.results_fail["TestCases"].append(results_dict)

    def write_results(self):
        # Create output dir if it doesn't exist
        try:
            if not os.path.isdir(self.output_dir):
                os.mkdir(self.output_dir)
        except OSError as e:
            logging.error("Error creating output directory {}, error: {}".format(self.output_dir, e))
            logging.error("Will write results file to current working directory instead.")
            self.output_dir = os.getcwd()
        # Write the passing results file
        path = os.path.join(self.output_dir, self.results_pass_filename)
        try:
            with open(path, 'w') as outfile:
                json.dump(self.results_pass, outfile)
        except OSError as e:
            logging.error("Error writing results file to {}, error: {}".format(path, e))
            logging.error("Printing results to STDOUT instead.")
            print(json.dumps(self.results_pass))
        # Write the failing results file
        path = os.path.join(self.output_dir, self.results_fail_filename)
        try:
            with open(path, 'w') as outfile:
                json.dump(self.results_fail, outfile)
        except OSError as e:
            logging.error("Error writing results file to {}, error: {}".format(path, e))
            logging.error("Printing results to STDOUT instead.")
            print(json.dumps(self.results_fail))


def walk_depth(directory, max_depth=1):
    """
    Directory tree walk like os.walk(), but with a max_depth limit 
    :param directory: the directory to start the walk from
    :param max_depth: the maximum depth to walk
    :return: the tuple (depth, path, dirs, files)
    """
    directory = directory.rstrip(os.path.sep)
    assert os.path.isdir(directory)
    base_sep = directory.count(os.path.sep)
    for path, dirs, files in os.walk(directory):
        cur_sep = path.count(os.path.sep)
        depth = cur_sep - base_sep
        yield depth, path, dirs, files
        if depth >= max_depth:
            del dirs[:]


def display_entry(depth, path, dirs, files):
    """
    For debugging: Displays the depth, path, dirs and files in a nice format
    
    :param depth: the depth of this directory within the test framework directory tree 
    :param path: the path to the directory
    :param dirs: a list of the names of directories in path
    :param files: a list of the names of files in path
    """
    logging.debug("depth {}, directory path: {}".format(depth, path))
    logging.debug("files in this directory:")
    for file in files:
        logging.debug("    {}".format(file))
    logging.debug("subdirectories in this directory:")
    for subdir in dirs:
        logging.debug("    {}".format(subdir))


def create_test_results(suite_name, test_name, timestamp, command_args_printable, rc):
    """
    Create a minimal test results object for test cases that did not produce their own

    :param suite_name: the name of the subdirectory for the suite this test was run in
    :param test_name: the name of the subdirectory for this test case
    :param timestamp: the timestamp when the test case was run
    :param command_args_printable: the command line args with sensitive args like password obscured
    :param rc: the return of the test (zero for success, non-zero for fail)
    :return: the results object that can be converted to JSON
    """
    failed, passed = 0, 0
    if rc == 0:
        passed = 1
    else:
        failed = 1
    results = {
        "ToolName": "Suite: {}, Test case: {}".format(suite_name, test_name),
        "Timestamp": {
            "DateTime": "{:%Y-%m-%dT%H:%M:%SZ}".format(timestamp)
        },
        "CommandLineArgs": command_args_printable,
        "TestResults": {
            test_name: {
                "fail": failed,
                "pass": passed
            }
        },
        "ServiceRoot": {}
    }
    return results


def get_config_schema(json_file):
    """
    Get and return the schema associated with the given config filename

    :param json_file: the name of the configuration file
    :return: the schema
    """
    if json_file == TestFramework.config_filename:
        return TestFramework.config_schema
    elif json_file == TestSuite.config_filename:
        return TestSuite.config_schema
    elif json_file == TestCase.config_filename:
        return TestCase.config_schema
    else:
        logging.error("Unexpected config filename '{}'".format(json_file))
        return None


def read_config_file(path, json_file):
    """
    Read the specified configuration file (in JSON format) and load it into a dictionary
    
    :param path: the full path of the directory where the configuration file resides
    :param json_file: the configuration file name (not including the path)
    :return: the dictionary representing the JSON config file
    """
    try:
        # open JSON config file
        with open(os.path.join(path, json_file)) as json_data:
            json_dict = json.load(json_data)
            # get the schema for the config file and validate it
            schema = get_config_schema(json_file)
            jsonschema.validate(json_dict, schema)
    except OSError as e:
        logging.error("OSError opening file {} in directory {}, error: {}"
                      .format(json_file, path, e))
        sys.exit(1)
    except ValueError as e:
        logging.error("ValueError loading JSON from file {} in directory {}, error: {}"
                      .format(json_file, path, e))
        sys.exit(1)
    except jsonschema.ValidationError as e:
        logging.error("JSON validation error from file {} in directory {}, error: {}"
                      .format(json_file, path, e.message))
        sys.exit(1)
    except jsonschema.SchemaError as e:
        logging.error("JSON schema error from file {} in directory {}, error: {}"
                      .format(json_file, path, e.message))
        sys.exit(1)
    else:
        logging.info("Successfully read and validated config file {} in directory {}".format(json_file, path))
        return json_dict


def get_config_file(depth, files):
    """
    Look for the configuration file expected at this depth
    
    :param depth: the directory depth
    :param files: a list of the names of files in a directory
    :return: the file name of the expected configuration file if present, otherwise None
    """
    config_files = [TestFramework.config_filename, TestSuite.config_filename, TestCase.config_filename]
    if config_files[depth] in files:
        return config_files[depth]
    return None


def add_test_as_unittest(framework, suite, case, results):
    """
    Creates a "test*" method in the RedfishTestCase unittest class for the test case defined by the
    given framework, suite and case instances.

    :param framework: the TestFramework instance
    :param suite: the TestSuite instance
    :param case: the TestCase instance
    :param results: the Results instance
    """
    def test_func(self):
        self.run_test(framework, suite, case, results)
    test_func_name = 'test_' + suite.get_name() + '_' + case.get_name()
    # ensure test_func_name is a valid python identifier (convert non-valid chars to '_')
    test_func_name = re.sub('\W|^(?=\d)', '_', test_func_name)
    setattr(RedfishTestCase, test_func_name, test_func)
    test_func.__name__ = test_func_name
    logging.debug("Added test {} with name {}".format(test_func, test_func_name))


def add_details_to_test_case(framework, depth, path, dirs, files):
    """
    Add the configuration data to the TestCase instance associated with this path
    
    :param framework: the TestFramework instance
    :param depth: the current directory depth within the test framework
    :param path: the full path of this test case subdirectory
    :param dirs: a list of the names of directories in path
    :param files: a list of the names of files in path
    """
    _, suite_name, test_name = path.rsplit(os.sep, 2)
    suite = framework.get_suite(suite_name)
    test_case = suite.get_test_case(test_name)
    config_file = get_config_file(depth, files)
    if config_file is not None:
        config_dict = read_config_file(path, config_file)
        test_case.set_config_file(config_file)
        test_case.set_config_data(config_dict)


def add_test_cases_to_suite(framework, depth, path, dirs, files):
    """
    Read the suite config file (if present) and create TestCase instances for each subdirectory in path
    and add them to the list of test cases for this suite
    
    :param framework: the TestFramework instance
    :param depth: the current directory depth within the test framework
    :param path: the full path of this test suite subdirectory
    :param dirs: a list of the names of directories in path
    :param files: a list of the names of files in path
    """
    _, suite_name = path.rsplit(os.sep, 1)
    suite = framework.get_suite(suite_name)
    config_file = get_config_file(depth, files)
    if config_file is not None:
        config_dict = read_config_file(path, config_file)
        suite.set_config_file(config_file)
        suite.set_config_data(config_dict)
    for subdir in dirs:
        test_case = TestCase(path, subdir, framework.get_output_subdir())
        suite.add_test_case(test_case)


def add_test_suites(framework, depth, path, dirs, files):
    """
    Read the top-level config file (if present) and create TestSuite instances for each subdirectory in path
    and add them to the list of test suites
    
    :param framework: the TestFramework instance
    :param depth: the current directory depth within the test framework
    :param path: the full path of the test framework (top-level) directory
    :param dirs: a list of the names of directories in path
    :param files: a list of the names of files in path
    """
    config_file = get_config_file(depth, files)
    if config_file is not None:
        config_dict = read_config_file(path, config_file)
        framework.set_config_file(config_file)
        framework.set_config_data(config_dict)
    for subdir in dirs:
        suite = TestSuite(path, subdir)
        framework.add_suite(suite)


def main():
    """
    main
    """

    # Parse command-line args
    parser = argparse.ArgumentParser(description="Run a collection of Redfish validation tests")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity of output")
    parser.add_argument("-d", "--directory", help="directory containing hierarchy of tests to run")
    parser.add_argument("-r", "--rhost", help="target hostname or IP address with optional :port")
    parser.add_argument("-u", "--user", help="username for authentication to the target host")
    parser.add_argument("-p", "--password", help="password for authentication to the target host")
    parser.add_argument("-i", "--interpreter", help="name of python interpreter to use to run the tests")
    parser.add_argument("-t", "--token", help="security token for authentication to the target host")
    parser.add_argument("-s", "--secure",
                        help="https security option: Always, Never, IfSendingCredentials or IfLoginOrAuthenticatedApi")
    cmd_args = parser.parse_args()

    # Set up logging
    logging.addLevelName(NOTICE, "NOTICE")

    def notice(self, message, *args, **kwargs):
        if self.isEnabledFor(NOTICE):
            self._log(NOTICE, message, args, **kwargs)

    logging.Logger.notice = notice
    log_level = NOTICE
    if cmd_args.verbose == 1:
        log_level = logging.INFO
    elif cmd_args.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(stream=sys.stderr, level=log_level)

    # Get directory from command-line args or default to current working directory
    framework_dir = os.getcwd()
    if cmd_args.directory is not None:
        framework_dir = os.path.abspath(cmd_args.directory)
    logging.debug("framework_dir = {}".format(framework_dir))

    # Walk the test framework directory tree to a max depth of 2 subdirectories,
    # building up the hierarchy of TestFramework, TestSuite(s), and TestCase(s)
    framework = None
    for depth, path, dirs, files in walk_depth(framework_dir, 2):
        display_entry(depth, path, dirs, files)
        if depth == 0:
            framework = TestFramework(path)
            add_test_suites(framework, depth, path, dirs, files)
        elif depth == 1:
            add_test_cases_to_suite(framework, depth, path, dirs, files)
        elif depth == 2:
            add_details_to_test_case(framework, depth, path, dirs, files)
        else:
            logging.error("Invalid depth {}".format(depth))
            exit(1)

    # Override params from top-level config file with command-line args
    framework.override_config_data(cmd_args)

    # Create a Results object
    results = Results(os.path.join(framework.get_path(), "reports", framework.get_output_subdir()),
                      framework.get_timestamp())

    # Traverse the TestFramework hierarchy and execute the specified tests
    logging.info("Test Framework: config_file = {}, path = {}"
                 .format(framework.get_config_file(), framework.get_path()))
    if framework.get_config_file() is None:
        logging.error("Top-level config file (framework_conf.json) not found")
    suites = framework.get_suites()
    for suite in suites:
        cases = suite.get_test_cases()
        if len(cases) > 0:
            logging.info("Suite: name = {}, config_file = {}, path = {}"
                         .format(suite.get_name(), suite.get_config_file(), suite.get_path()))
        for case in cases:
            if case.get_config_file() is not None:
                logging.info("Test case: name = {}, config_file = {}, path = {}"
                             .format(case.get_name(), case.get_config_file(), case.get_path()))
                suite.substitute_config_variables(case.get_command_args(), case.get_command_args_printable())
                framework.substitute_config_variables(case.get_command_args(), case.get_command_args_printable())
                print("Adding test {}/{} to test runner".format(suite.get_name(), case.get_name()))
                add_test_as_unittest(framework, suite, case, results)
            else:
                logging.info("Test case: name = {} skipped, config file (test_conf.json) not found, path = {}"
                             .format(case.get_name(), case.get_path()))

    # Run the tests via HTMLTestRunner
    runner = HtmlTestRunner.HTMLTestRunner(output=framework.get_output_subdir())
    runner.run(unittest.makeSuite(RedfishTestCase))

    # Change the directory back to the root of this test framework run
    try:
        os.chdir(framework.get_path())
    except OSError as e:
        logging.error("Unable to change directory to {}, error: {}".format(framework.get_path(), e))

    # Write results summary
    results.write_results()

    print()
    print("See HTML and JSON summary results in {}/{}/".format("reports", framework.get_output_subdir()))
    print()


if __name__ == "__main__":
    main()
