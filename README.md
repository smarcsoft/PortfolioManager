# Portfolio Manager
PortfolioManager is a tool to provide objective insights into your portfolio
## Server
Contains the server infrastructure. We have several executables:
feeder: Feeder is the main program. It takes a list of exchanges and a configuration file
controlFeedConfig: utility to generate the configuration of the controlFeed
### config
Contains all configurations files for the backend to run


# TODOs:
Fix feeder log
Setup the daily update process with a report being emailed daily 
Avoid API calls if we are trying to update data which is already loaded in the database
Check the integrity of the price data
