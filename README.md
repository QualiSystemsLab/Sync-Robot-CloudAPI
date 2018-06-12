# README #

This README would normally document whatever steps are necessary to get your application up and running.

### Set up a server to execute Robot tests ###

* 1, Reserve CentOS 7.0 VM on Do
* 2, ssh to VM, root/qs1234
* 3, yum install python-pip
* 4, pip install robotframework
* 5, yum install git-all
* 6, mkdir /usr/local/robot

### Set up local working directory ###

* Make sure test_path defined in config file exists on local machine
* Make sure the local_working_directory defined in config file, e.g. C:\TestShell\Robot, contains pscp.exe and zip.exe



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
* 4, Run sync_robot_tests.py -config config.csv, or sync_robot_tests.py -config config-v.csv -v
* 5, Run SyncRobots.bat to test
* 6, Schedule task to run SyncRobots.bat every 5 minutes