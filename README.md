# Portfolio Manager
PortfolioManager is a tool to provide objective insights into your portfolio
## Server
Contains the server infrastructure. We have several executables:
feeder: Feeder is the main program. It takes a list of exchanges and a configuration file
controlFeedConfig: utility to generate the configuration of the controlFeed
### config
Contains all configurations files for the backend to run

# Architecture
3 servers are involved:
. The session manager which runs a react webapp managing user sessions and able to start/stop/run the infrastructure.
. The compute server which runs the jupiter notebooks and the database update process.
. The SQL Server database server, keeping track of the database update processes.

## Session Manager
It runs:
. A REST API to start/stop the underlying infrastructure
. A REACT "startapp" which provides the user interface in front of the API
### REST API
This in happening in frontend/api. Read the README there.
### Startapp
This is happening in fronend/startapp. Read the README there.

## Compute server
It runs jupyter server.
This is happening in frontend/lab.



# TODOs:
## Must do
- Deploy jupiter lab on the smarcsoft.com web server
    - Automate the proxy configuration when the compute sever starts

## Should do
- Setup the daily update process with a report being emailed daily 
- Purge old exchange load IDs (with ticker loads) from the database and setup automated cleanup job

## Possible improvements
- Avoid API calls if we are trying to update data which is already loaded in the database
- Check the integrity of the price data
