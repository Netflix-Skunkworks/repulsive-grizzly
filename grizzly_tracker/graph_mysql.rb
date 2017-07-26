#alternative to using the web UI to see what messages are coming back
require 'mysql2'
require 'ascii_charts'
require 'yaml'

configs = YAML.load(File.read("./config.yml"))

client = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])

while true
  results = client.query("SELECT status_code, UNIX_TIMESTAMP(statuses_counted_at) DIV 5 as counted_at_group, SUM(status_code_count) AS counted_total 
FROM status_codes 
WHERE UNIX_TIMESTAMP(statuses_counted_at) DIV 5 = 
(SELECT UNIX_TIMESTAMP(sc.statuses_counted_at) DIV 5 as sub_counted_at_group FROM status_codes AS sc WHERE sc.statuses_counted_at < (now() - INTERVAL 6 SECOND) ORDER BY UNIX_TIMESTAMP(sc.statuses_counted_at) DIV 5 DESC LIMIT 1)
GROUP BY UNIX_TIMESTAMP(statuses_counted_at) DIV 5, status_code ORDER BY status_code") 


  graph_res = []
  results.each do |row|
    graph_res.push [row["status_code"], row["counted_total"]]
  end
  puts ascii_str = AsciiCharts::Cartesian.new(graph_res, bar: true).draw
  sleep 6  
end


