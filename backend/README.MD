# Main backend directory
This is the directory from which you run the backend processes (feeder controller or feeder).

## Feeder controller


## Feeder
Runs a set of exchanges in a single threaded manner. Uselful if you want to focus on a set of small exchanges and do not need to split the exchanges using the controller.

Example:  python feeder/feeder.py --help

To run the feeder for the US stock exchange:
python feeder/feeder.py --exchange US

