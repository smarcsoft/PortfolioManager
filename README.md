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


# Roadmap:
+ Notebook to demonstrate tags and selections
+ Support my portfolio
+ Save and Load portfolio and portfolio groups
- Support dated transactions
- Create the API documentation and publish it
- Alert capabilities on relative/absolute profit and losses
- Daily report (value, breakdowns, p&ls)
- Create an environment per user
- User registration capability
- Feedback/Request for improvement section in UI
- Post pilot on french finance forum



# TODOs:

## Should do
- Setup the daily update process with a report being emailed daily 

## Possible improvements
- Avoid API calls if we are trying to update data which is already loaded in the database
- Check the integrity of the price data
