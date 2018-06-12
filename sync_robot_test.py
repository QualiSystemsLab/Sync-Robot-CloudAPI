import requests
import os
import json
import argparse
import re
import shutil
import codecs as codecs
import pyodbc
import paramiko
from quali_api_wrapper import QualiApi


def convert_to_ascii(text):
    return " ".join(str(ord(char)) for char in text)


def read_config_file(file_path):
    """
    Read config file into a dictionary.
    :param str file_path: the config.csv file path
    :return: dict
    """
    data_dict = dict()
    config_data = open(file_path, "r")
    for line in config_data:
        split_line = line.split(',', 1)
        key = split_line[0]
        value = split_line[1].strip()
        data_dict[key] = value
    return data_dict


def read_config_dict(config_data_dict):
    """
        Read config dictionary and set global variables accordingly
        :param dict config_data_dict: the config dictionary
        :return: None
    """
    global template_test_file
    global test_interface_template_file
    global test_variable_template_file
    global report_expression_template_file
    global variable_name_in_template
    global variable_original_name_in_template
    global variable_default_value_in_template
    global test_path

    global api_url
    global api_1_0_url
    global bitbucket_repository_url
    global default_domain

    global sql_server
    global db_name

    global exec_server_address
    global exec_server_username
    global exec_server_password
    global exec_server_working_directory
    global robot_tests_directory
    global archive_output_directory
    global local_working_directory

    global cloudshell_server_address
    global cloudshell_server_port
    global cloudshell_server_username
    global cloudshell_server_password
    global cloudshell_server_domain
    global cloudshell_shared_robots_folder

    if 'template_test_file' in config_data_dict:
        template_test_file = config_data_dict['template_test_file']
    if 'test_interface_template' in config_data_dict:
        test_interface_template_file = config_data_dict['test_interface_template']
    if 'test_variable_template' in config_data_dict:
        test_variable_template_file = config_data_dict['test_variable_template']
    if 'report_expression_template' in config_data_dict:
        report_expression_template_file = config_data_dict['report_expression_template']
    if 'variable_name_in_template' in config_data_dict:
        variable_name_in_template = config_data_dict['variable_name_in_template']
        variable_original_name_in_template = variable_name_in_template + '_Original'
    if 'variable_default_value_in_template' in config_data_dict:
        variable_default_value_in_template = config_data_dict['variable_default_value_in_template']
    if 'test_path' in config_data_dict:
        test_path = config_data_dict['test_path']
        if not test_path.endswith('\\'):
            test_path += '\\'

    if 'api_url' in config_data_dict:
        api_url = config_data_dict['api_url']
    if 'api_1_0_url' in config_data_dict:
        api_1_0_url = config_data_dict['api_1_0_url']
    if 'bitbucket_repository_url' in config_data_dict:
        bitbucket_repository_url = config_data_dict['bitbucket_repository_url']
    if 'default_domain' in config_data_dict:
        default_domain = config_data_dict['default_domain']

    if 'sql_server' in config_data_dict:
        sql_server = config_data_dict['sql_server']
    if 'db_name' in config_data_dict:
        db_name = config_data_dict['db_name']

    if 'exec_server_address' in config_data_dict:
        exec_server_address = config_data_dict['exec_server_address']
    if 'exec_server_username' in config_data_dict:
        exec_server_username = config_data_dict['exec_server_username']
    if 'exec_server_password' in config_data_dict:
        exec_server_password = config_data_dict['exec_server_password']
    if 'exec_server_working_directory' in config_data_dict:
        exec_server_working_directory = config_data_dict['exec_server_working_directory']
    if 'robot_tests_directory' in config_data_dict:
        robot_tests_directory = config_data_dict['robot_tests_directory']
    if 'archive_output_directory' in config_data_dict:
        archive_output_directory = config_data_dict['archive_output_directory']
    if 'local_working_directory' in config_data_dict:
        local_working_directory = config_data_dict['local_working_directory']

    if 'cloudshell_server_address' in config_data_dict:
        cloudshell_server_address = config_data_dict['cloudshell_server_address']
    if 'cloudshell_server_port' in config_data_dict:
        cloudshell_server_port = config_data_dict['cloudshell_server_port']
    if 'cloudshell_server_username' in config_data_dict:
        cloudshell_server_username = config_data_dict['cloudshell_server_username']
    if 'cloudshell_server_password' in config_data_dict:
        cloudshell_server_password = config_data_dict['cloudshell_server_password']
    if 'cloudshell_server_domain' in config_data_dict:
        cloudshell_server_domain = config_data_dict['cloudshell_server_domain']
    if 'cloudshell_shared_robots_folder' in config_data_dict:
        cloudshell_shared_robots_folder = config_data_dict['cloudshell_shared_robots_folder']


def clone_repository():
    """
        Clone Bitbucket repository onto Unix execution server machine, under specified working directory
        :return: None
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=exec_server_address, username=exec_server_username, password=exec_server_password)
        command = 'cd ' + exec_server_working_directory + '; rm -rf ' + robot_tests_directory
        ssh.exec_command(command=command, timeout=180)
        command = 'cd ' + exec_server_working_directory + '; git clone ' + bitbucket_repository_url
        ssh.exec_command(command=command, timeout=1800)
        ssh.close()
    except Exception as error:
        print("Failed to connect to execution server " + exec_server_address)


def read_db(sql_server, db_name):
    """
        Read from database the stored last update UTC timestamp of Bitbucket repository for the previous sync
        :param str sql_server: SQL Server engine instance name (assuming Windows Authentication)
        :param str db_name: database name (note the table and column names are hard coded)
        :return: str last update UTC timestamp in unicode
    """
    last_update_utc = '2000-01-01 12:00:00+00:00'
    con = pyodbc.connect('Trusted_Connectio=yes', driver='{SQL Server}', server=sql_server,
                         database=db_name)
    cur = con.cursor()
    querystring = "select LastUpdateUTC from Quali.dbo.BitBucketInfo"
    cur.execute(querystring)
    rows = cur.fetchall()
    for row in rows:
        last_update_utc = row.LastUpdateUTC
        break
    return last_update_utc


def write_db(sql_server, db_name, last_update_utc):
    """
        Store in database the last update UTC timestamp of Bitbucket repository for the current sync
        :param str sql_server: SQL Server engine instance name (assuming Windows Authentication)
        :param str db_name: database name (note the table and column names are hard coded)
        :param str last_update_utc: last update UTC timestamp in unicode
        :return: None
    """
    con = pyodbc.connect('Trusted_Connectio=yes', driver='{SQL Server}', server=sql_server,
                         database=db_name)
    cur = con.cursor()
    querystring = "update Quali.dbo.BitBucketInfo set LastUpdateUTC = '" + last_update_utc + "'"
    cur.execute(querystring)
    con.commit()


def delete_all(path, delete_root_dir=False):
    """
    Delete all files/folders under given path
    :param str path: the folder to delete
    :param bool delete_root_dir: whether to delete the root folder as well
    :return: None
    """
    if not os.path.isdir(path):
        return
    files=os.listdir(path)
    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            os.remove(fullpath)
        elif os.path.isdir(fullpath):
            delete_all(fullpath, True)
    if delete_root_dir:
        os.rmdir(path)


def read_template(file_name):
    """
        Read a template file which is a XML
        :param str file_name: file path
        :return: str file content
    """
    infile = open(file_name, 'r')
    return infile.read()


def fill_template(template, replacements):
    """
        Fill in a template using a dictionary to replace each given label by corresponding content
        :param str template: entire template text
        :param dict replacements: pairs of label and filled in content
        :return: str modified/filled content from the template
    """
    content = template
    for src, target in replacements.iteritems():
        content = content.replace(src, target)
    return content


def substitute_string_in_tstest_file(file_name, replacements):
    """
    Substitute old string to new string in given file
    :param str file_name: name of the file
    :param dict replacements: dictionary of old/new string pairings
    :return: None
    """
    lines = []
    infile = codecs.open(file_name, 'r', encoding='utf-16')
    for line in infile:
        for src, target in replacements.iteritems():
            line = line.replace(src, target)
        lines.append(line)
    infile.close()

    outfile = codecs.open(file_name, 'w', encoding='utf-16')
    outfile.writelines(lines)
    outfile.close()


def retrieve_variables(content):
    """
        Retrieve variables from Variables section of Robot test yaml file content
        :param str content: Robot test yaml file content
        :return: list of variables
    """
    variables = []
    in_var_section = False
    for line in content.splitlines():
        #print line
        if in_var_section:
            var_def = re.split('  +', line)
            if len(var_def) > 1:
                #print var_def[0], ':', var_def[1]
                var_name = var_def[0]
                def_value = var_def[1]
                if not def_value.startswith('%'): #not environment variable which would be directly passed to robot
                    variables.append([var_name.strip('${').strip('}'), def_value])
        if '*** Variables ***' in line:
            in_var_section = True
        elif in_var_section and '*** ' in line:
            #end of Variables section
            break
    return variables


def get_repository_last_update_timestamp(api_1_0_url):
    """
        Get last update UTC timestamp of a Bitbucket repository using Bitbucket Cloud REST API 1.0 URL
        :param str api_1_0_url: Bitbucket Cloud REST API 1.0 URL of the repository
        :return: str last update UTC timestamp in unicode, e.g. 2000-01-01 12:00:00+00:00
    """
    repository_last_update_timestamp = ''
    try:
        r = requests.get(api_1_0_url)
        json_string = r.content
        data = json.loads(json_string)
        try:
            repository_last_update_timestamp = data['utc_last_updated']
        except Exception as error:
            print("Caught error: " + repr(error))
    except Exception as error:
        print("Failed to connect to bitbucket: " + repr(error))
        exit(1)
    return repository_last_update_timestamp


def get_resource_last_update_timestamp(api_1_0_url, resource):
    """
        Get last update UTC timestamp of a Bitbucket resource (e.g. Robot test) using Bitbucket Cloud REST API 1.0 URL
        :param str api_1_0_url: Bitbucket Cloud REST API 1.0 URL of the resource
        :return: str last update UTC timestamp in unicode, e.g. 2000-01-01 12:00:00+00:00
    """
    try:
        r = requests.get(api_1_0_url)
        json_string = r.content
        data = json.loads(json_string)
        try:
            files = data['files']
            for entry in files:
                if entry['path'] == resource:
                    entry_last_update_timestamp = entry['utctimestamp']
                    return entry_last_update_timestamp
        except Exception as error:
            print("Caught error: " + repr(error))
    except Exception as error:
        print("Failed to connect to bitbucket: " + repr(error))
        exit(1)
    return None


def delete_obsolete_shared_tests(quali_api, expected_tests, shared_test_folder):
    """
        Delete obsolete Shared tests and test folders from CloudShell database based on latest Bitbucket repository
        :param QualiAPI quali_api: QualiAPI object
        :param list expected_tests: expected tests and test folders accordingly to Robot tests/folders in repository
        :param str shared_test_folder: top folder in Shared tests where generated tests are located
        :return: None
    """
    try:
        r = quali_api.get_tests_from_shared(shared_test_folder)
        data = json.loads(r)
        if 'Children' in data:
            num_entries = len(data['Children'])
            for i in range(num_entries):
                entry_type = data['Children'][i]['Type']
                entry_name = data['Children'][i]['Name']
                entry_name = entry_name.replace(' ', '%20')
                full_path = shared_test_folder + '/' + entry_name
                if entry_type == 'Folder':
                    if full_path not in expected_tests:
                        print('Delete obsolete Shared test folder that is no longer on repository: ' + full_path)
                        quali_api.delete_test_from_shared(full_path)
                    else:
                        delete_obsolete_shared_tests(quali_api, expected_tests, full_path)
                elif entry_type == 'Test' and full_path not in expected_tests:
                    print('Delete obsolete Shared test that is no longer on repository: ' + full_path)
                    quali_api.delete_test_from_shared(full_path)
    except Exception as error:
        print("Caught error: " + repr(error))


def add_expected_folders(directory_domains):
    """
        Iterate through directory to domains mappings, expand the target Shared folder by
         inserting domain folder at the top, and add it to expected Shared folders
        :param dict directory_domains: directory to domains mappings
        :return: None
    """
    global expected_folders_tests
    for directory, domain_directories in directory_domains.iteritems():
        for domain_directory in domain_directories:
            if not domain_directory == '':
                domain_directory = re.sub('[^0-9a-zA-Z_ ]', '_', domain_directory)
                domain_directory = '/' + domain_directory.replace(' ', '%20')
            target_shared_directory = cloudshell_shared_robots_folder + domain_directory
            #add domain level folder
            if target_shared_directory not in expected_folders_tests:
                expected_folders_tests.append(target_shared_directory)
            #add domain folder + directory sub folder
            if not directory == '':
                target_shared_directory = cloudshell_shared_robots_folder + domain_directory + '/' + directory.replace(' ', '%20')
            # target_shared_directory = 'Robots/' + entry.replace('.', '_').replace(' ', '%20')
            if target_shared_directory not in expected_folders_tests:
                expected_folders_tests.append(target_shared_directory)


def create_test_file(test_path, robot_test_name, entry_url, full_path):
    """
        Generate a Local test file
        :param str test_path: file path where the test file is to be created
        :param str robot_test_name: Robot test name, e.g. test1 (original name test1.robot)
        :param str entry_url: Bitbucket Cloud REST API 2.0 URL of the Robot, e.g.
         https://api.bitbucket.org/2.0/repositories/ericrqs/robot-tests/src/a30380928ea5fde267c36f3dba830ed4c21e6151/test1.robot
        :param str full_path: full path of the Robot, e.g. My Folder 1/test1.robot
        :return: None
    """
    new_test_file = test_path + '\\' + robot_test_name + '.tstest'
    shutil.copyfile(template_test_file, new_test_file) #note shutil.copyfile() overwrites target file if it exists
    r = requests.get(entry_url)
    # print r.content
    # fill in TestPrototypeParameter interface XML element and replace hard coded Param1 by variable name
    # fill in SingleVariable interface XML element and replace hard coded default_val by default value
    robot_arguments = ''
    replacements = dict()
    if VAR:
        interface_section = ''
        variable_section = ''
        report_expression_section = ''

        # by default, no need to rename robot variable in test unless there is space in the name
        variable_renames = dict()
        for variable in retrieve_variables(r.content):
            variable_name = variable[0]
            variable_renames[variable_name] = variable_name
            # print variable_name

        # if variable name has single spaces in it, e.g. 'Example Input 1', replace by '_', e.g. 'Example_Input_1'
        # however if there is also robot variable 'Example_Input_1', then keep appending '_' for the corresponding
        # TestShell test variable until it is unique
        for variable_name, rename in variable_renames.iteritems():
            if ' ' in variable_name:
                # rename = variable_name.replace(' ', '_') #replace space in the name by underscore
                rename = re.sub('[^0-9a-zA-Z_]', '_', variable_name)  # replace each unsupported char by underscore
                while rename in variable_renames:
                    rename += '_'
                variable_renames[variable_name] = rename

        for variable in retrieve_variables(r.content):
            variable_name = variable[0]
            default_value = variable[1]
            replacements[variable_name_in_template] = variable_renames[variable_name]
            replacements[variable_original_name_in_template] = variable_name
            replacements[variable_default_value_in_template] = default_value
            interface_section += fill_template(test_interface_template, replacements)
            variable_section += fill_template(test_variable_template, replacements)
            report_expression_section += fill_template(report_expression_template, replacements)
            robot_arguments += " --variable \'" + variable_name + "\':\'{" + variable_renames[variable_name] + "}\'"

    replacements = {"test1.robot": robot_arguments + " \'" + full_path + "\'"}  # reset dictionary
    if VAR:
        replacements[test_interface_template_fill_tag] = interface_section
        replacements[test_variable_template_fill_tag] = variable_section
        replacements[report_expression_template_fill_tag] = report_expression_section
    # the following initial values of required variables are hard coded in test template
    replacements['CLOUDSHELL_SERVER_ADDRESS_VALUE'] = cloudshell_server_address
    replacements['CLOUDSHELL_SERVER_PORT_VALUE'] = cloudshell_server_port
    replacements['CLOUDSHELL_USERNAME_VALUE'] = cloudshell_server_username
    replacements['CLOUDSHELL_PASSWORD_VALUE'] = cloudshell_server_password
    replacements['CLOUDSHELL_DOMAIN_VALUE'] = cloudshell_server_domain
    replacements['EXEC_SERVER_ADDRESS_VALUE'] = exec_server_address
    replacements['EXEC_USERNAME_VALUE'] = exec_server_username
    replacements['EXEC_PASSWORD_VALUE'] = exec_server_password
    replacements['BITBUCKET_REPOSITORY_URL'] = bitbucket_repository_url
    replacements['EXEC_SERVER_WORKING_DIR'] = exec_server_working_directory
    replacements['ROBOT_TESTS_DIR'] = robot_tests_directory
    replacements['ARCHIVE_OUTPUT_DIR'] = archive_output_directory
    replacements['LOCAL_WORKING_DIR'] = local_working_directory
    # print replacements
    substitute_string_in_tstest_file(new_test_file, replacements)
    new_test_file_ascii_name = new_test_file.encode('ascii', 'ignore')  # otherwise UnicodeDecodeError
    return new_test_file_ascii_name


def process_robot_tests(url, test_path, build_directory_domains=False):
    """
        Copy Robot test into a CloudShell Shared test
        :param str url: Bitbucket Cloud REST API 2.0 URL of a repository folder
        :param str test_path: file path where Local test file is to be created
        :param bool build_directory_domains: whether to only build directory to domains mapping in this process
        :return: None
    """
    global quali_api
    global expected_folders_tests
    global directory_domains
    try:
        r = requests.get(url)
        try:
            json_string = r.content
            #print url
            #print json_string
            data = json.loads(json_string)
            #print data

            num_entries = 0
            if 'values' in data:
                num_entries = len(data['values'])
            for i in range(num_entries):
                try:
                    entry = data['values'][i]['path']
                    entry_type = data['values'][i]['type']
                    entry_url = data['values'][i]['links']['self']['href']
                    #convert unsupported characters for Sharedt folder/test to '_' but leave ' ', '/' and '.'
                    entry = re.sub('[^0-9a-zA-Z_ /.]', '_', entry)
                    #print entry, entry_type
                except Exception as error:
                    print("Caught error: " + repr(error))
                    continue

                #print test_path
                #print entry
                # skip special folders like .idea, such named folder will corrupt Shared tests listing on portal
                if 'directory' in entry_type and not entry.startswith('.'):
                    directory = entry
                    directory = directory.replace('.', '_')
                    if directory not in directory_domains:
                        directory_domains[directory] = ['']
                    if '/' in entry: #sub folder, e.g. 'My Folder 1/Sub Folder 1.1'
                        entry = '\\' + entry.split('/')[-1] #take the last level folder as upper levels already in test_path
                        entry = entry.replace('.', '_')
                    if not os.path.exists(test_path + entry):
                        os.mkdir(test_path + entry)
                    process_robot_tests(entry_url, test_path + entry, build_directory_domains)
                elif 'file' in entry_type and entry.endswith('/.atf_project') and build_directory_domains:
                    r = requests.get(entry_url)
                    domain_data = json.loads(r.content)
                    if 'domains' in domain_data:
                        domains = domain_data['domains']
                        directory = entry.rsplit('/', 1)[0]
                        directory = directory.replace('.', '_')
                        directory = directory.encode('ascii', 'ignore')
                        if len(domains) == 0:
                            domains = [default_domain]
                        #print entry, directory, domains
                        directory_domains[directory] = domains
                        if DEBUG:
                            print(directory_domains)
                elif 'file' in entry_type and entry.endswith('.robot') and not build_directory_domains:
                    full_path = entry
                    message = full_path
                    directory = ''
                    if '/' in entry:
                        directory = entry.rsplit('/', 1)[0]
                        directory = directory.replace('.', '_')
                    #print directory
                    entry = entry.split('/')[-1]
                    robot_test_name = entry[:-6] #e.g. test1.robot name is test1
                    parent_dir_api_1_0_url = entry_url.replace('2.0', '1.0').rsplit('/', 1)[0] + '/'
                    last_update_timestamp = get_resource_last_update_timestamp(parent_dir_api_1_0_url, full_path)
                    if directory not in directory_domains:
                        directory_domains[directory] = ['']
                    domain_directories = directory_domains[directory]
                    for domain_directory in domain_directories:
                        test_domain_path = test_path
                        if not domain_directory == '':
                            test_domain_path = test_path.replace(test_path_root, test_path_root + domain_directory + '\\', 1)
                            domain_directory = re.sub('[^0-9a-zA-Z_ ]', '_', domain_directory)
                            domain_directory = '/' + domain_directory.replace(' ', '%20')
                        target_shared_directory = cloudshell_shared_robots_folder + domain_directory
                        if not directory == '':
                            target_shared_directory = cloudshell_shared_robots_folder + domain_directory + '/' + directory.replace(' ', '%20')
                        expected_folders_tests.append(target_shared_directory + '/' + robot_test_name)
                        if CLEAN or last_update_timestamp > last_sync_timestamp:
                            new_test_file_ascii_name = create_test_file(test_path, robot_test_name, entry_url, full_path)
                            # update corresponding Shared test
                            quali_api.upload_test_to_shared(new_test_file_ascii_name, target_shared_directory)
                            message = full_path + ' --updated'
                    if DEBUG:
                        message += ', last update in repository ' + last_update_timestamp
                    print(message)

            if 'next' in data:
                next_page = data['next']
                process_robot_tests(next_page, test_path, build_directory_domains)
        except Exception as error:
            print("Caught error: " + repr(error))
    except Exception as error:
        print("Failed to connect to bitbucket: " + repr(error))
        exit(1)


parser = argparse.ArgumentParser()
parser.add_argument('-config', action='store', dest='config_file', help='config file')
parser.add_argument('-clean', action='store_true', default=False, help='clean and resync all TestShell Robot tests')
parser.add_argument('-domain', action='store_true', default=False, help='sync TestShell tests per domain structure defined in Robot repository structure')
parser.add_argument('-debug', action='store_true', default=False, help='print Debug info')
parser.add_argument('-f', action='store_true', default=False, help='force to sync all Robot tests')
parser.add_argument('-v', action='store_true', default=False, help='sync Robot variables onto TestShell input paramaters')
args = parser.parse_args()
config_file = args.config_file
CLEAN = args.clean
DOMAINS = args.domain
DEBUG = args.debug
FORCE = args.f
VAR = args.v

"""
DOMAINS: whether to create Shared tests under Bitbucket domain top folders,
e.g. Robot test is under a folder which is associated to two domains A and B, then for this Robot test, two
Shared tests will be created, one per each domain, under top folder A and top folder B respectively
"""

config_data_dict = dict()
if config_file is not None:
    config_data_dict = read_config_file(config_file)
    if DEBUG:
        print(config_data_dict)

api_url = 'https://api.bitbucket.org/2.0/repositories/ericrqs/robot-tests/src'
api_1_0_url = 'https://api.bitbucket.org/1.0/repositories/ericrqs/robot-tests/'
bitbucket_repository_url = 'https://bitbucket.org/ericrqs/robot-tests.git'
default_domain = 'ATF-Admins'

template_test_file = 'RobotTemplate.tstest'
test_interface_template_file = 'TestPrototypeParameter.txt'
test_interface_template_fill_tag = '<TestPrototypeParameter></TestPrototypeParameter>'  #hard coded
test_variable_template_file = 'SingleVariable.txt'
test_variable_template_fill_tag = '<SingleVariable></SingleVariable>' #hard coded
report_expression_template_file = 'ExpressionTemplate.txt'
report_expression_template_fill_tag = '<ConstantExpression></ExpressionDecorator>' #hard coded
variable_name_in_template = 'Param1'
variable_original_name_in_template = 'Param1_Original'
variable_default_value_in_template = 'default_val'
test_path = 'tests\\'

sql_server = 'localhost\\SQLEXPRESS'
db_name = 'Quali'

exec_server_address = '192.168.41.88'
exec_server_username = 'root'
exec_server_password = 'qs1234'
exec_server_working_directory = '/usr/local/robot'
robot_tests_directory = 'robot'
archive_output_directory = '/usr/local/archive'
local_working_directory = 'C:\\bin'

cloudshell_server_address = 'localhost'
cloudshell_server_port = '9000'
cloudshell_server_username = 'admin'
cloudshell_server_password = 'admin'
cloudshell_server_domain = 'Global'
cloudshell_shared_robots_folder = 'Robot'

read_config_dict(config_data_dict)

if VAR:
    test_interface_template = read_template(test_interface_template_file)
    test_variable_template = read_template(test_variable_template_file)
    report_expression_template = read_template(report_expression_template_file)
test_path_root = test_path

directory_domains = dict()
expected_folders_tests = []

quali_api = QualiApi(cloudshell_server_address,
                     cloudshell_server_port,
                     cloudshell_server_username,
                     cloudshell_server_password,
                     cloudshell_server_domain)

repository_last_update_timestamp = get_repository_last_update_timestamp(api_1_0_url)
print('Last repository update time: ' + repository_last_update_timestamp)

last_sync_timestamp = ''
if not FORCE:
    last_sync_timestamp = read_db(sql_server, db_name)
print('Last sync repository update time: ' + last_sync_timestamp)

if last_sync_timestamp == repository_last_update_timestamp and not CLEAN:
    print('Shared tests are up to date.')
    exit(0)

if CLEAN:
    try:
        print('Cleaning existing Shared tests...')
        delete_all(test_path)
        quali_api.delete_test_from_shared(cloudshell_shared_robots_folder)
    except Exception as error:
        print('No test to clean, proceed...')

if DOMAINS:
    print('Checking Robot test directory to domain mappings...')
    process_robot_tests(api_url, test_path, True)
print('Synchronizing Robot tests from repository to Shared tests...')
process_robot_tests(api_url, test_path)

if DEBUG:
    print(directory_domains)

if not CLEAN:
    print('Checking Shared tests to remove obsolete tests...')
    add_expected_folders(directory_domains)
    if DEBUG:
        print(expected_folders_tests)
    delete_obsolete_shared_tests(quali_api, expected_folders_tests, cloudshell_shared_robots_folder)

write_db(sql_server, db_name, repository_last_update_timestamp)

print("Synchronizing Robot repository to execution server...")
clone_repository()




