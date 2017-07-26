#This script is used to send test messages to the SNS topic to test if the system is working"

require 'aws-sdk'
require 'yaml'

configs = YAML.load(File.read("./config.yml"))

#region
sns = Aws::SNS::Client.new(region: configs["sns_region"])

exceptions = [{subject: "something went wrong", message: "Bad UTF8 Char line 54"}, {subject: "there was an error", message: "This is the end"}, {subject: "strange things are happening", message: "unhandled exception on line 53 of /var/log/stuff that is causing everything to fall apart"}]

while true
  timestamp = Time.now().strftime("%Y-%m-%d %H:%M:%S.%6N")



#{"elb": "padme-staging-frontend-1409373721.us-west-2.elb.amazonaws.com", "timestamp": "2016-06-07 17:26:33.481010", "agent": "1", "status_codes": {"200": 36}}
  50.times do |i|
    resp = sns.publish(topic_arn: configs["sns_topic"], message: "{\"elb\": \"padme-staging-frontend-1409373721.us-west-2.elb.amazonaws.com\", \"timestamp\": \"#{timestamp}\", \"agent\": \"#{i}\", \"status_codes\": {\"200\": #{rand(200)}, \"504\": #{rand(200)}, \"502\": #{rand(200)}, \"503\": #{rand(200)}}}")
  end
  puts "sent status updates"

  error_or_not = [200, 400]

  100.times do |i|
    e_or_n = error_or_not[rand(2)]
    subject = "Grizzly Sanity Check Passed"
    if e_or_n == 400
      subject = "Grizzly Sanity Check Failed"
    end
    resp = sns.publish(topic_arn: configs["sns_topic"], message: "{\"elb\": \"padme-staging-frontend-1409373721.us-west-2.elb.amazonaws.com\", \"timestamp\": \"#{timestamp}\", \"agent\": \"#{i}\", \"exception\": \"#{e_or_n}\"}", subject: subject)
  end

  puts "sent client status checks"

  error_message = exceptions.sample

  resp = sns.publish(topic_arn: configs["sns_topic"], message: "{\"elb\": \"padme-staging-frontend-1409373721.us-west-2.elb.amazonaws.com\", \"timestamp\": \"#{timestamp}\", \"agent\": \"15\", \"exception\": \"#{error_message[:message]}\"}", subject: error_message[:subject])
  puts "sent exception"
  sleep 2
end
