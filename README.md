# Repulsive Grizzly
Application Layer DoS Testing Framework

<img src="http://i.imgur.com/ELSsnaw.jpg" width="300">

## What is Repulsive Grizzly?
Repulsive Grizzly is an application layer load testing framework specifically designed to support high throughput and sophisticated request types.  Repulsive Grizzly can help you confirm application layer Denial of Service (DoS) by running your test at a higher concurrency with other features such as session round robining to help you bypass certain rate limiters or web application firewalls.  

## Why is Repulsive Grizzly Different?
The main difference between Repulsive Grizzly and other load testing tools is we're specifically focused on providing a framework that makes Application Denial of Service testing easier.  Some features that are useful in Repulsive Grizzly include:
* Optional support to run tests within [Cloudy Kraken](https://github.com/netflix-skunkworks/cloudy-kraken) a red team orchestration framework that can help you scale up your test across multiple datacenters or regions
* Logging messages to centralized Amazon SNS queue for aggregation during larger exercises such as running a multiple agent test with [Cloudy Kraken](https://github.com/netflix-skunkworks/cloudy-kraken)
* Ability to round robin authentication objects using placeholders in headers, cookies, and/or POST:GET:PUT:DELETE data
* Ability to round robin target URLs or fix one URL per attack agent
* Sanity check logic to confirm your environment is stable enough to begin the test 
* Leverages [Eventlet](http://eventlet.net/) for high concurrency, allowing you to scale up to > 300 threads per repulsive grizzly agent
* Provides TTL as well as start time so multiple agent scans conducted with [Cloudy Kraken](https://github.com/netflix-skunkworks/cloudy-kraken) start and stop at the same time
* HTTP Proxy support for troubleshooting
* Grizzly Dashboard to aggregate and graph http status codes while you run multi agent tests

## How Does Repulsive Grizzly Perform Tests?
![Grizzly Flowchat](https://i.imgur.com/DxBdLXU.png)

The typical execution of Repulsive Grizzly is as follows:

1. Validate the commands.json file for good settings
2. Sleep until start time is triggered
3. Validate that the sanity check URL returns a HTTP 200
4. Build Eventlet Pool of request objects based on the commands file
5. Begin execution of the test
6. Log messages to console and Amazon SNS messaging queue (if configured)
7. Each iteration check TTL and one triggered, exit the test

## Getting Started
[Wiki](https://github.com/netflix-skunkworks/repulsive-grizzly/wiki)

## What is Skunkworks?
Skunkworks projects are not fully supported unlike other projects we open source.  We are leveraging the Skunkworks project to demonstrate one way engineers can approach application layer load testing.  We'd be happy to accept Pull Requests for bug fixes or features.  

## Release History ##
**Version 1.0** - *July 29, 2017*

Initial Release
