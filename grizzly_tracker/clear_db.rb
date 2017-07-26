require 'mysql2'
require 'yaml'

configs = YAML.load(File.read("./config.yml"))

client = Mysql2::Client.new(:database => configs["db_name"], :host => configs["db_host"], :username => configs["db_username"], :password => configs["db_password"])

client.query("DELETE FROM exceptions")

client.query("DELETE FROM status_codes")
