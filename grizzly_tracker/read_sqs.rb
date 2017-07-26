#this script reads from the SQS queue and inputs data in a database to be used for graphing
require 'aws-sdk'
require 'mysql2'
require 'json'
require 'date'
require 'yaml'

configs = YAML.load(File.read("./config.yml"))

sqs = Aws::SQS::Client.new(region: configs["sqs_region"])

threads = []

#starts 200 threads to read more
#still we usually start 3 or 4 processes to keep up
200.times do |i|
  threads << Thread.new {
    client = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])
    while true
      resp = sqs.receive_message({queue_url: configs["sqs_queue"]})
      resp.messages.each do |message|
        begin
          parsed = JSON.parse(message.body)
          if parsed["Subject"].to_s.strip != "control"
            resp = JSON.parse(parsed["Message"])
        
            puts resp.inspect
            if !resp["status_codes"].nil?
              resp["status_codes"].each do |key, value|
                puts "inserting into db #{key} #{value}"
                prestm = client.prepare("INSERT INTO status_codes (statuses_counted_at, status_code, status_code_count, agent_id, elb) VALUES (?, ?, ?, ?, ?)")
                prestm.execute(parsed["Timestamp"], key, value, resp["agent"], resp["elb"])  
              end
            elsif !resp["exception"].nil?
              prestm = client.prepare("INSERT INTO exceptions (elb, exception_recorded_at, exception, agent_id, message_subject) VALUES (?, ?, ?, ?, ?)")
              prestm.execute(resp["elb"], parsed["Timestamp"], resp["exception"], resp["agent"], parsed["Subject"]) 
            end    
            resp = sqs.delete_message({queue_url: "https://sqs.us-west-2.amazonaws.com/179727101194/grizzly_stats", receipt_handle: message.receipt_handle})
          else
            resp = sqs.delete_message({queue_url: "https://sqs.us-west-2.amazonaws.com/179727101194/grizzly_stats", receipt_handle: message.receipt_handle})
          end
        rescue JSON::ParserError
          prestm = client.prepare("INSERT INTO other_messages (message) VALUES (?)")
          if !parsed["Message"].nil?
            puts "JSON error #{parsed["Message"]}"
            prestm.execute(parsed["Message"])
           else
             puts message
             prestm.execute(message)
           end
           resp = sqs.delete_message({queue_url: "https://sqs.us-west-2.amazonaws.com/179727101194/grizzly_stats", receipt_handle: message.receipt_handle}) 
        rescue Aws::SQS::Errors::ReceiptHandleIsInvalid
          puts "Invalid delete handle"
        end
      end
    end
  }
end

threads.map(&:join)
