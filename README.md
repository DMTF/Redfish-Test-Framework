Copyright 2017-2019 DMTF. All rights reserved.

# Redfish-Test-Framework

        Language: Python 3.x

## Prerequisites

Install `jsonschema` and `html-testRunner`:

```
pip install jsonschema
pip install html-testRunner
```

## About

The Redfish Test Framework is a tool and a model for organizing and running a set of Redfish interoperability tests against a target system. At this time, there are three tiers (or suites) of testing envisioned for the framework:

1. Base schema validation (validate against DMTF and service schemas)
2. Interoperability profiles (e.g. OCP, OpenStack, VMWare, Azure)
3. Use case checkers (e.g. power control, account management, one-time-boot, etc.)

But the framework is designed to be flexible to allow for running fewer or greater suites of tests. The set of tests to be run are determined by the set of files in a test directory hierarchy. The directory hierarchy organizes the tests into a set of suites. And each suite is further organized into a set of specific tests. Within this hierarchy are config files that specify the details of how to invoke the tests as well as the test programs themselves (e.g. python scripts).

## Usage

```
usage: test_framework.py [-h] [-v] [-d DIRECTORY] [-r RHOST] [-u USER]
                         [-p PASSWORD] [-i INTERPRETER] [-t TOKEN] [-s SECURE]

Run a collection of Redfish validation tests

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase verbosity of output
  -d DIRECTORY, --directory DIRECTORY
                        directory containing hierarchy of tests to run
  -r RHOST, --rhost RHOST
                        target hostname or IP address with optional :port
  -u USER, --user USER  username for authentication to the target host
  -p PASSWORD, --password PASSWORD
                        password for authentication to the target host
  -i INTERPRETER, --interpreter INTERPRETER
                        name of python interpreter to use to run the tests
  -t TOKEN, --token TOKEN
                        security token for authentication to the target host
  -s SECURE, --secure SECURE
                        https security option: Always, Never,
                        IfSendingCredentials or IfLoginOrAuthenticatedApi
```

## Quick Start (install and run)

To get the Redfish Test Framework installed and ready to run, follow these steps.

* Download the framework zip file from: https://github.com/DMTF/Redfish-Test-Framework/archive/master.zip
* Unzip the file to the location of your choice.
* Change directory into the top level directory of the unziped file:

```
cd Redfish-Test-Framework-master
```

* Run the `build_test_tree.py` script:

```
python3 build_test_tree.py
```

At this point you will have a test tree of tests to run. In the current directory there is a top-level config file called `framework_conf.json`. It will look something like this:

```
{
  "target_system": "127.0.0.1:8000",
  "https": "Always",
  "username": "someuser",
  "password": "xxxxxxxx",
  "interpreter": "python3",
  "custom_variables": {
    "system_id": "sys1",
    "metadata_url": "https://127.0.0.1:8000/redfish/v1/$metadata",
    "nochkcert": "--nochkcert",
    "secure": "-S"
  }
}
```

* Using you favorite text editor, edit the following entries in the file:
    * `target_system` - edit the value to be the IP address or hostname of your target system with optional :port
    * `username` - edit the value to specify the user name to use for authentication to the target system
    * `password` - specify the password for the user name to use for authentication
    * `interpreter` - specify the name of the python 3 interpreter to use to run the tests
    * `system_id` - specify the identifier of a system in the Systems collection of the target (this is used to perform a reset operation on the specified system in the Redfish-Usecase-Checkers power_control test)
    * `metadata_url` - edit the `127.0.0.1:8000` portion of the url to match the target_system value specified above (this url is used by the Redfish-Reference-Checker test)

* You can now run the tests via the test framework tool:

```
python3 test_framework.py
```

For more information on customizing the variables in the config files, adding new tests to the framework and reviewing the test output, see the sections below.



## Test Setup

In order to run  a set of tests, some setup work is needed to organize the tests into the directory structure expected by the framework. Choose a top-level directory in which to setup the tests. In this top-level directory will be 2 files, the test framework script itself (`test_framework.py`), and the top-level config file (`framework_conf.json`). Then create a subdirectory for each suite of tests to be run. Example suite-level subdirectories would be `Redfish-Service-Validator` and `Redfish-Usecase-Checkers`. The names of these subdirectories are not important (the test framework discovers tests within this described directory hierarchy). But using descriptive names like the examples given will make using the framework and reading the output reports easier.

Within each suite-level subdirectory can be an optional suite-level config file (`suite_conf.json`). Then create a test case subdirectory under the suite-level subdirectory for each test to be run. Example test case subdirectories would be `account_management`, `power_control`, `one_time_boot`, and `root_schema_validation`.

Finally, within each test case subdirectory will be a test config file (`test_conf.json`). The presence of a `test_conf.json` file in a test case subdirectory is what the framework uses to determine if this is a test to be run. Other subdirectories can be present (python packages, report output directories, etc.), but they will not be treated as test case directories without a `test_conf.json` file. The test case subdirectory may also contain the actual test programs/scripts. Or the test programs may reside elsewhere as long as they can be found via the system PATH, PYTHONPATH, etc. 

At this point an example directory tree should be helpful.

```
├── Redfish-Service-Validator
│   ├── root_schema_validation
│   │   ├── RedfishServiceValidator.py
│   │   ├── test_conf.json
│   │   └── traverseService.py
│   └── suite_conf.json
├── Redfish-Usecase-Checkers
│   ├── account_management
│   │   ├── account_management.py
│   │   ├── test_conf.json
│   │   └── toolspath.py
│   ├── one_time_boot
│   │   ├── one_time_boot.py
│   │   └── test_conf.json
│   ├── power_control
│   │   ├── power_control.py
│   │   ├── test_conf.json
│   │   └── toolspath.py
│   ├── suite_conf.json
│   └── usecase
│       ├── __init__.py
│       ├── results.py
│       └── validation.py
├── framework_conf.json
└── test_framework.py
```



## Configuration Files

### framework_conf.json

The framework config file (`framework_conf.json`) contains information about the target system to test. This includes the hostname or IP address of the target system with optional port number, whether to use the http or https protocol, security credentials, etc. There are a set of predefined variable names that can be configured as well as a `custom_variables` entry where other variables can be defined as needed by the underlying tests.

Example:

```
{
  "target_system": "127.0.0.1:8001",
  "https": "Never",
  "username": "root",
  "password": "c7tidsvbjw4",
  "interpreter": "python3",
  "custom_variables": {
    "verbosity": "-v",
    "ssl": "--nossl"
  }
}
```

The predefined variables are:

* `target_system` - the hostname or IP address of the target system with optional port number (example: "127.0.0.1:8001")
* `username` - the username for basic authentication to the target system
* `password` - the password for basic authentication to the target system
* `interpreter` - the name of the python interpreter to use to run the tests
* `token` - a security token for authentication to the target system
* `https` - when to use the https protocol vs. http (example: "Never", "Always", "IfSendingCredentials", or "IfLoginOrAuthenticatedApi")

There is also one special predefined variable that is provided by the framework. The name of this variable is `output_subdir`. But you cannot specify it in the `framework_conf.json` file. The value of this variable is generated by the framework based on the time and date of the test run. And it is used to collect the various test program outputs into a consistent set of output directories. 

Custom variables:

If your test cases need other variables defined beyond the predefined ones, they can be specified in the `custom_variables` entry. For example, different test programs specify the use of http/https differently. One program may expect `-S Never` to specify the use of the http protocol while another may expect `--nossl` for the same scenario. The example above shows how to use the predefined variable `https` as well as the custom variable `ssl` to achieve this. 

Note in the **Usage** section above that there are command-line options to the `test_framework.py` script that mirror the predefined variables in the `framework_conf.json` file. You can specify these values either on the the command line or in the config file. If any are specified in both places, the command-line args take precedence. 


### suite_conf.json

In most cases there is no need to specify anything in the `suite_conf.json` files. There are no predefined variables here. But there is a `custom_variables` entry just like in the `framework_conf.json` file.  Specify custom variables in this file to define variables that are only applicable to this suite of tests or that need to be overridden for this suite.

Example:

```
{
  "custom_variables": {
    "verbosity": "-vv",
    "mode": "remote"
  }
}
```

### test_conf.json

The test case config file `test_conf.json` is very simple. It has a `test` element that contains a required `command` entry and an optional `wait_seconds_after` entry. The `command` specifies the command-line needed to execute the test. In this command string, use the predefined and custom variables defined in the higher level config files to specify test case parameters that can vary between runs (like the target system, username or password). Prefix the variable name with a dollar sign (e.g. `$target_system`) in order for the framework to perform the variable substitution. The `wait_seconds_after` entry specifies the number of seconds to delay after running the command. This is helpful in a scenario where a command initiates a long running operation that the test program is unable to determine has completed.


Example 1:

```
{
  "test": {
    "command": "$interpreter power_control.py -r $target_system -S $https -d $output_subdir $verbosity -I System.Embedded.1 GracefulRestart",
    "wait_seconds_after": 120
  }
}
```

Example 2:

```
{
  "test": {
    "command": "$interpreter RedfishServiceValidator.py --ip $target_system $ssl --logdir $output_subdir"
  }
}
```

## Outputs

* The output of each test will be written under its own test subdirectory.
* In order to prevent overwriting of results from previous runs, an output subdirectory named with a date and time stamp of the test run will be created under each test directory and the results for that test run will be written into that output subdirectory.
* The test framework will take care of redirecting the STDOUT and STDERR of the test programs to output files in the proper output subdirectory.
* The test framework will take care of providing a config substitution variable (`$output_subdir`) for this output subdirectory that can be passed via an argument to the test programs. This will allow the test programs to write any additional output files (*.html, *.json, debug files, etc.) to the proper output subdirectory. 
* The test framework generates a summary HTML report showing the passing and failing tests colored green or red respectively.
* The test framework also generates a pair of summary reports in JSON format showing the passing and failing tests (`results_pass.json` and `results_fail.json`). These summaries are generated by combining the results.json payloads from the individual tests.
* The summary report of passing tests (`results_pass.json`) is envisioned to be sent to DMTF for publication of successful vendor implementation testing results.

After running the test framework for a set of tests, the directory tree will look something like the example shown below. Notice that all the test output for individual tests appears in subdirectories of the individual tests. And summary reports for the overall framework run appear in a `reports` subdirectory at the top of the directory hierarchy. And finally note that the output subdirectory names includes a date and time stamp. This prevents subsequent test runs from overwriting previous results.

Example directory tree after test run:

```
├── Redfish-Service-Validator
│   ├── root_schema_validation
│   │   ├── RedfishServiceValidator.py
│   │   ├── output-2017-06-29T173926Z
│   │   │   ├── ConformanceHtmlLog_06_29_2017_123941.html
│   │   │   ├── ConformanceLog_06_29_2017_123941.txt
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── test_conf.json
│   │   └── traverseService.py
│   └── suite_conf.json
├── Redfish-Usecase-Checkers
│   ├── account_management
│   │   ├── account_management.py
│   │   ├── output-2017-06-29T173926Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── test_conf.json
│   │   └── toolspath.py
│   ├── one_time_boot
│   │   ├── one_time_boot.py
│   │   ├── output-2017-06-29T173926Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   └── test_conf.json
│   ├── power_control
│   │   ├── output-2017-06-29T173926Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── power_control.py
│   │   ├── test_conf.json
│   │   └── toolspath.py
│   ├── suite_conf.json
│   └── usecase
│       ├── __init__.py
│       ├── results.py
│       └── validation.py
├── framework_conf.json
├── reports
│   └── output-2017-06-29T173926Z
│       ├── Test_RedfishTestCase_2017-06-29_12-39.html
│       ├── results_fail.json
│       └── results_pass.json
└── test_framework.py
```



