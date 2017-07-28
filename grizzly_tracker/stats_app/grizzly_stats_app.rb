#this is a sinatra based quick UI to show what's going on with a Repulsive Grizzly DoS test
require 'sinatra'
require 'mysql2'
require 'json'
require 'yaml'

configs = YAML.load(File.read("./config.yml"))

#start up a few clients since calls happen asynchronously at different times so they need their own clients

client = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])

client2 = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])

client3 = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])

#initial page load
get '/' do
  div_str = "No Agents Reported Yet"
  erb :index, locals: {divs: div_str}
end

#gets the data for the graphs
get '/data.json' do
  results = client.query("SELECT status_code, UNIX_TIMESTAMP(statuses_counted_at) DIV 5 as counted_at_group, SUM(status_code_count) AS counted_total 
FROM status_codes 
WHERE UNIX_TIMESTAMP(statuses_counted_at) DIV 5 = 
(SELECT UNIX_TIMESTAMP(sc.statuses_counted_at) DIV 5 as sub_counted_at_group FROM status_codes AS sc WHERE sc.statuses_counted_at < (now() - INTERVAL 30 SECOND) ORDER BY UNIX_TIMESTAMP(sc.statuses_counted_at) DIV 5 DESC LIMIT 1) AND statuses_counted_at > (now() - INTERVAL 5 MINUTE)
GROUP BY UNIX_TIMESTAMP(statuses_counted_at) DIV 5, status_code ORDER BY status_code")


  graph_res = []
  results.each do |row|
    temp_hash = {"key" => row["status_code"], "value" => row["counted_total"]}
    graph_res.push temp_hash
  end

  i = 0
  while graph_res.size < 15
    temp_hash = {"key" => "empty_" + i.to_s, "value" => 0}
    graph_res.push temp_hash
    i += 1
  end

  graph_res.to_json
end

#gets the agent status for the boxes that show status
get '/agent_status' do
  results = client2.query("SELECT DISTINCT agent_id,  
(SELECT ex2.exception_recorded_at FROM exceptions AS ex2 WHERE ex1.agent_id = ex2.agent_id 
AND (ex2.exception = '200' OR ex2.exception = '400') ORDER BY 
ex2.exception_recorded_at DESC LIMIT 1) AS last_exception_at,
(SELECT ex3.exception FROM exceptions AS ex3 
WHERE ex1.agent_id = ex3.agent_id AND (ex3.exception = '200' OR ex3.exception = '400') ORDER BY 
ex3.exception_recorded_at DESC LIMIT 1) AS last_exception FROM exceptions AS ex1 WHERE ex1.exception_recorded_at > (now() - INTERVAL 120 SECOND)")

  res_hash = {}
  results.each do |row|
    res_hash[row["agent_id"]] = {last_status_at: row["last_exception_at"], last_status: row["last_exception"]}
  end

  all_agents = client2.query("SELECT DISTINCT agent_id FROM exceptions WHERE exception_recorded_at > (now() - INTERVAL 2 HOUR) AND message_subject LIKE 'Grizzly Sanity Check %' ORDER BY agent_id")

  div_str = "<div id=\"row\">"
  i = 1
  all_agents.each do |row|
    if res_hash[row["agent_id"]].nil?
      div_str += "<div class=\"agent_no_status\" id=\"agent_status_#{row["agent_id"]}\">#{row["agent_id"]}</div>"
    elsif res_hash[row["agent_id"]][:last_status].to_i == 200
      div_str += "<div class=\"agent_success\" id=\"agent_status_#{row["agent_id"]}\">#{row["agent_id"]}</div>"
    else
      div_str += "<div class=\"agent_fail\" id=\"agent_status_#{row["agent_id"]}\">#{row["agent_id"]}</div>"
    end

    if i%20 == 0
      div_str += "</div><div id=\"row\">"
    end
    i += 1
  end
  div_str += "</div>"
  div_str
end

#gets the text of exceptions
get '/exceptions' do
  results = client3.query("SELECT elb, exception_recorded_at, exception, agent_id, message_subject FROM exceptions WHERE message_subject NOT LIKE 'Grizzly Sanity Check %' ORDER BY exception_recorded_at DESC LIMIT 3")
  ret_str = ""
  results.each do |row|
    ret_str += "<div>#{row["agent_id"]} | #{row["exception_recorded_at"]} | #{row["message_subject"]} | #{row["exception"]} | #{row["elb"]}</div>"
  end
  ret_str
end
