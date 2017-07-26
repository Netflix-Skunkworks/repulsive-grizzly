Requirements:
* MySQL Database server
* Server with ruby installed and the bundler gem
* An SQS queue that's fed by an SNS topic which Repulsive Grizzly pushes messages to

To run the Grizzly tracker first set the correct DB, SQS and SNS values in config.yaml.  Next install the gems by running `bundle install` from the root directory. Then you need to start 3 or 4 instances of read_sqs.rb like this
`nohup bundle exec ruby read_sqs.rb &`

Then startup the UI by running:
`nohup bundle exec ruby stats_app/grizzly_stats_app.rb -e production &`

Now you can access the app on port 4567 (you can change the port using the -p option)

The backend database is MySQL, below are the create statements to create the database with the correct columns needed to run the code specified above

``CREATE TABLE `exceptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `elb` varchar(255) DEFAULT NULL,
  `exception_recorded_at` timestamp NULL DEFAULT NULL,
  `exception` varchar(255) DEFAULT NULL,
  `agent_id` int(11) DEFAULT NULL,
  `message_subject` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `speed_index` (`exception_recorded_at`,`exception`,`agent_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3145699 DEFAULT CHARSET=latin1;``


``CREATE TABLE `status_codes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `agent_id` int(11) DEFAULT NULL,
  `elb` varchar(255) DEFAULT NULL,
  `status_code` int(11) DEFAULT NULL,
  `status_code_count` int(11) DEFAULT NULL,
  `statuses_counted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `pkey_index` (`id`),
  KEY `date_and_such` (`agent_id`,`statuses_counted_at`)
) ENGINE=InnoDB AUTO_INCREMENT=7204506 DEFAULT CHARSET=latin1;``



