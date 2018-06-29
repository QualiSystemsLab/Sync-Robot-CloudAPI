# README #

This README would normally document whatever steps are necessary to get your application up and running.

### Set up a Linux server to execute Robot tests ###

* 1, Reserve CentOS 7.0 VM on Do
* 2, ssh to VM, root/qs1234
* 3, yum install python-pip
* 4, pip install robotframework
* 5, yum install git-all
* 6, mkdir /usr/local/robot


### Set up local working directory on CloudShell execution server (Windows) ###

* Make sure test_path defined in config file exists on local machine
* Make sure the local_working_directory defined in config file, e.g. C:\TestShell\Robot, contains pscp.exe and zip.exe (in /bin of this repository)



### Set up Robot sync process ###

* 1, Install 8.1 or higher
* 2, Add a new table to Quali DB:
	use [Quali]
	create table dbo.BitBucketInfo 
	( LastUpdateUTC nvarchar(255)
	)
	insert into dbo.BitBucketInfo (LastUpdateUTC)
	values ('2000-01-01 12:00:00+00:00')
* 3, Edit config file. Examples included: config.csv, config-v.vsx
* 4, Run sync_robot_tests.py -config config.csv
* 5, Run SyncRobots.bat to test
* 6, Schedule task to run SyncRobots.bat every 5 minutes
Note: Step 2 can be skipped to simpplify the setup without DB. In this case, to run the sync script, do: sync_robot_tests.py -config config.csv -f


### Prepare TestShell test template ###

* Two templates are provided: RobotTemplate.tstest, RobotTemplate_v.tstest. 
* RobotTemplate.tstest is in 8.3 and can be directly opened by TestShell Studio 8.3 for any further modification needed.
* RobotTemplate_v.tstest cannot be directly opened in TestShell Studio. It is for creating wrapper test that captures all Robot variables
as input parameters of the test, so that when user runs such TestShell test, user can pass in Robot variable values (instead of default values
set within Robot test) from CloudShell user interface. To run script using this template, do: sync_robot_tests.py -config config-v.csv -v.
Note option -v is only for this type of template.
