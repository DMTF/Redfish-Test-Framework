# Redfish Test Framework Design

## Overview

The Redfish Test Framework is a tool and a model for organizing and running a set of interoperability tests against a target system. At this time, there are three tiers (or suites) of testing envisioned for the framework:

1. Base schema validation (validate against DMTF and service schemas)
2. Interoperability Profiles (e.g. OCP, OpenStack, VMWare, Azure)
3. Use case Checkers (e.g. power control, account management, etc.)

But the framework is designed to be flexible to allow for running fewer or greater suites of tests. The set of tests to be run are determined by the set of files in a test directory hierarchy. The directory hierarchy organizes the tests into a set of suites. And each suite is further organized into a set of specific tests. Within this hierarchy are config files that specify the details of how to invoke the tests. And the test programs themselves (e.g. python scripts) will likely also reside.


### Configuration files

The configuration files are placed in the directory hierarchy matching the scope of configuration they represent. The three scopes and the type of configuration information they contain are:

* Framework level (top level) - applies to all tests run by framework:
    * Target hostname or IP address, port number
    * Security credentials (username/password or token)
    * Security settings (https, basic auth, etc.)
* Test suite level (mid level):
    * Config input that applies to all tests within one of the framework suites (e.g. InteropProfiles, UsecaseCheckers, SchemaValidation) 
* Individual test level (lowest level):
    * Command line args needed to invoke the specific tests, including:
        * Test-specific options like location of local schema files, options for individual checker tests, etc.
        * Specify directory/filenames for output
    
    
### Test programs

The top-level test framework tool (e.g. test_framework.py) will be placed at the top level of the directory hierarchy. This is the tool that will read the directory hierarchy and config files and orchestrate the running of all the tests defined within all the suites.
 
The test programs or scripts needed to perform the individual validations are to be placed within the directory hierarchy at the individual test level (lowest level). The test programs will be peers (siblings) of the config files that specify how they are to be invoked.


### Outputs

* Each individual test should produce these 4 types of output:
	* Return code (zero for success, non-zero for failure)
	* Log files (STDOUT, STDERR, debug logs) [audience: developer]
	* HTML reports (optional) [audience: user/customer]
	* DMTF results payload (summary of test results in a standard format that can be digitally signed and then sent to DMTF for publication of successful testing results)
* The top-level framework tool will produce a pair of summary reports in JSON format - one for the passing tests and one for the failing tests.

## Deeper dive 

### Configuration files

The input to control the running of the tests is provided via config files.

* The config files are in JSON format.
* The expected directory/file structure is described in the Overview section above.
* An example directory structure is shown below.
* The config files are named:
    * `framework_conf.json` (framework-level config)
    * `suite_conf.json` (suite-level config)
    * `test_conf.json` (test-case-level config)
* The format of the config files will be defined by a JSON schema. 

### Test programs

The test programs needed to run the tests will reside in the individual test (lowest level) subdirectories. The programs may be python scripts, shell scrips, Java programs, binary executables, etc.

### Example directory structure with config files and test programs

~~~
test_framework
├── interop_profiles_suite
│   ├── abc_profile_test
│   │   ├── interop_profile_validation.py
│   │   └── test_conf.json
│   ├── xyz_profile_test
│   │   ├── interop_profile_validation.py
│   │   └── test_conf.json
│   └── suite_conf.json
├── schema_validation_suite
│   ├── root_schema_validation
│   │   ├── schema_validator.py
│   │   └── test_conf.json
│   ├── service_schema_validation
│   │   ├── schema_validator.py
│   │   └── test_conf.json
│   └── suite_conf.json
├── usecase_checkers_suite
│   ├── usecase_1_checker
│   │   ├── test_conf.json
│   │   └── usecase_1_checker.py
│   ├── usecase_2_checker
│   │   ├── test_conf.json
│   │   └── usecase_2_checker.py
│   └── suite_conf.json
├── framework_conf.json
└── test_framework.py
~~~

### Configuration processing


#### Top-level (framework-level) config file (`framework_conf.json`)

The top-level config file specifies the following parameters:

* Target system hostname (or IP address) and (optionally) port (example: "127.0.0.1:8000")
* HTTPS usage info (example: "Never", "Always", "IfSendingCredentials", or "IfLoginOrAuthenticatedApi")
* Credentials (example: username and password, or token)
* These top-level parameters are used (inherited) by the individual test cases
* For any parameters that need to be communicated down to the individual test programs but are
not covered by the parameters described above, a `custom_variables` parameter is available to specify additional custom key/value pairs.
* Example `framework_conf.json`:

~~~json
{
  "target_system": "127.0.0.1:8000",
  "username": "admin",
  "password": "********",
  "https": "Always"
  "custom_variables": {
    "verbosity": "-vvv",
    "mode": "local"
  }
}
~~~

The predefined parameters that can be specified in the top-level config file (`framework_conf.json`) can also be specified by command-line args to the test framework tool (`test_framework.py`). The predefined parameters are `target_system`, `username`, `password`, `token`, and `https`. If any parameters are specified in both places, the command-line args take precedence. 

Custom variables can also be defined in the config file in the `custom_variables` element. Custom variables cannot be specified via the command-line.

Command-line usage:

~~~
usage: test_framework.py [-h] [-v] [-d DIRECTORY] [-r RHOST] [-u USER]
                         [-p PASSWORD] [-t TOKEN] [-s SECURE]

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
  -t TOKEN, --token TOKEN
                        security token for authentication to the target host
  -s SECURE, --secure SECURE
                        https security option: Always, Never,
                        IfSendingCredentials or IfLoginOrAuthenticatedApi
~~~


#### Mid-level (suite-level) config file (`suite_conf.json`)

The mid-level config file (`suite_conf.json`) allows custom variable to be defined. Specify custom variables in this file to define variables that are only applicable to this suite of tests or that need to be overridden for this suite.

Example `suite_conf.json`:

~~~json
{
  "custom_variables": {
    "verbosity": "-vv",
    "mode": "remote"
  }
}
~~~


#### Lowest-level (test-case-level) config file (`test_conf.json`)

This config file contains the detail of the test to invoke and how to invoke it (the command line args). It contains these parameters:

* A "test" element that specifies:
	* Command string to execute for this test
* Config values inherited from top-level can be specified with substitution variables (`$target_system`, `$username`, etc.)
* Example `test_conf.json`:

~~~json
{
  "test": {
    "command": "python usecase_1_checker.py $verbosity -r $target_system -u $username -p $password -S $https -d $output_subdir twiddle knob1"
  }
}
~~~

Given the example config files above (`framework_conf.json` and `test_conf.json`), after variable substitution by the framework, the resulting test case config would look like this:

~~~json
{
  "test": {
    "command": "python usecase_1_checker.py -vvv -r 127.0.0.1:8000 -u admin -p ******** -S Always -d output-2017-05-18T171529Z twiddle knob1"
  }
}
~~~


### Outputs

* The output of each test will be written under its own test subdirectory.
* In order to prevent overwriting of results from previous runs, an output subdirectory named with a date and time stamp of the test run will be created under each test directory and the results for that test run will be written into that output subdirectory.
* The test framework will take care of redirecting the STDOUT and STDERR of the test programs to output files in the proper output subdirectory.
* The test framework will take care of providing a config substitution variable for this output subdirectory that can be passed via an argument to the test programs. This will allow the test program to write any additional output files (*.html, debug files, etc.) to the proper output subdirectory. 
* Individual tests may make use of the python logging facility, but this is not mandated.
* The framework will *not* roll up the individual test outputs into a single file.
* But it should generate a pair of summary reports showing the passing and failing tests. These summaries are generated by combining the DMTF result payloads from the individual tests.
* The summary report of passing tests is envisioned to be sent to DMTF for publication of successful vendor implementation testing results.

After running the test framework for a set of tests, the directory tree will look something like the example shown below. Notice that all the test output appears in subdirectories of the individual tests. And also note that the subdirectory name includes a date and time stamp. This prevents subsequent test runs from overwriting previous results.

Example directory tree after test run:

~~~
test_framework
├── interop_profiles_suite
│   ├── abc_profile_test
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── interop_profile_validation.py
│   │   └── test_conf.json
│   ├── xyz_profile_test
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── interop_profile_validation.py
│   │   └── test_conf.json
│   └── suite_conf.json
├── schema_validation_suite
│   ├── root_schema_validation
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── ComplianceHtmlLog_05_18_2017_171529.html
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── schema_validator.py
│   │   └── test_conf.json
│   ├── service_schema_validation
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── ComplianceHtmlLog_05_18_2017_171529.html
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── schema_validator.py
│   │   └── test_conf.json
│   └── suite_conf.json
├── usecase_checkers_suite
│   ├── usecase_1_checker
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── test_conf.json
│   │   └── usecase_1_checker.py
│   ├── usecase_2_checker
│   │   ├── output-2017-05-18T171529Z
│   │   │   ├── results.json
│   │   │   ├── stderr.log
│   │   │   └── stdout.log
│   │   ├── test_conf.json
│   │   └── usecase_2_checker.py
│   └── suite_conf.json
├── framework_conf.json
├── test_framework.py
└── output-2017-05-18T171529Z
    ├── results_fail.json
    └── results_pass.json
~~~


#### DMTF results payload format

As mentioned in the Overview section, one of the test outputs that each test program is expected to produce is a DMTF results payload file (`results.conf`). Details on this output file:

* Payload is in JSON format
* Info to include in this results payload:
	* Timestamp
	* Environment:
		* Key info from ServiceRoot document
		* Target hostname/IP and port
		* Credentials (sensitive information masked)
	* Name of validation test/scenario performed
	* Pass/fail results (summary of which tests passed/failed)
	* Overall return code
* Digital signing info TBD. Consider:
	* Who will sign results?
	* Key management issues
	* Use JSON Web Signature standard?

In the `Redfish-Usecase-Checkers` project there is a `results.py` module that python test tools can use to facilitate the simple creation and updating of this DMTF results payload.

Example of a DMTF results file (`results.json`) for a usage scenario checker tool:

~~~json
{
  "ToolName": "Account Management Checker",
  "Timestamp": {
    "DateTime": "2017-04-25T22:05:24Z"
  },
  "CommandLineArgs": [
    "account_management.py",
    "-r",
    "127.0.0.1:8001",
    "-S",
    "Never",
    "-d",
    "output-2017-06-23T172750Z",
    "Accounts",
    "list"
  ],
  "ServiceRoot": {
    "Chassis": {
      "@odata.id": "/redfish/v1/Chassis"
    },
    "Registries": {
      "@odata.id": "/redfish/v1/Registries"
    },
    "Id": "RootService",
    "JsonSchemas": {
      "@odata.id": "/redfish/v1/JSONSchemas"
    },
    "@odata.id": "/redfish/v1",
    "Description": "Root Service",
    "Tasks": {
      "@odata.id": "/redfish/v1/TaskService"
    },
    "Links": {
      "Sessions": {
        "@odata.id": "/redfish/v1/Sessions"
      }
    },
    "@odata.context": "/redfish/v1/$metadata#ServiceRoot.ServiceRoot",
    "@odata.type": "#ServiceRoot.v1_0_2.ServiceRoot",
    "Name": "Root Service",
    "AccountService": {
      "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/AccountService"
    },
    "Systems": {
      "@odata.id": "/redfish/v1/Systems"
    },
    "SessionService": {
      "@odata.id": "/redfish/v1/SessionService"
    },
    "EventService": {
      "@odata.id": "/redfish/v1/EventService"
    },
    "Managers": {
      "@odata.id": "/redfish/v1/Managers"
    },
    "RedfishVersion": "1.0.2"
  },
  "TestResults": {
    "Accounts": {
      "fail": 0,
      "pass": 1
    },
    "ErrorMessages": []
  }
}
~~~

### Considerations for test programs

* When the framework runs an individual test, the current working directory will be the directory where the low-level configuration file (`test_conf.json`) resides. For example, in the directory tree shown above, the current working directory when running the `abc_profile_test` will be `.../test_framework/interop_profiles_suite/abc_profile_test/`
* Test programs can write output to STDOUT an STDERR as desired. The test framework will take care or redirecting that output to files in the output directory.
* For other files generated by a test program (`results.json`, html reports, etc.), the test program should write these files to the output subdirectory that is created by the test framework. In order to know the name of this subdirectory, the test program should use a command-line arg to receive it. And the `test_conf.json` file should specify this arg using the provided `$output_subdir` variable. See the example `test_conf.json` shown earlier in this document.
* The test program (or script) itself may reside in the test directory (the same directory containing the `test_conf.json` file) or it may reside where it will be found based on the appropriate search path (`PATH`, `PYTHONPATH`, etc). For python scripts, required python library packages can follow this same model (reside in the test directory or be available in the `PYTHONPATH`).
* The design of the test framework assumes that the configuration data can be passed to the individual tests via command-line args. A test program can still be run if it reads config data from some other configuration file. But that would mean specifying configuration data in multiple files, leading to potential mistakes and unexpected behavior. It is strongly encouraged that test programs accept configuration data via command-line args.
