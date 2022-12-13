# Jupyter lab setup:
## One-time setup:
pip install jupyterlab
pip install notebook
pip install voila
pip install matplotlib

## Start-up:
### run_jupiter.sh
Runs the jupiter server.
jupyter notebook runs at http://localhost:9999/

### Manually:
In this directory:
jupyter-lab
jupyter notebook
voila 

Please prefer the run_jupiter.sh over the manual procedure.

### Configuration
The configuration is driven by the following environment variables overriding the default values.
In order to find the pm.conf configuration file, the environment variable PM_CONFIG_LOCATION can be used.
In order to find the logging.conf configuration file, the environment variable PM_LOGGING_LOCATION can be used. It will then override whatever is found in the pm.conf file.
In order to find the location of the database, the environment variable DB_LOCATION can be used. See run_jupiter.sh.

## To expose jupiter notebooks on the internet
## One-time on the compute server:
jupyter server --generate-config generates /home/smarcsoft/.jupyter/jupyter_server_config.py
jupyter server password

jupyter notebook --generate-config -> /home/smarcsoft/.jupyter/jupyter_notebook_config.py

### configuration file:
#### To allow the proxy to work with jupiter
jupyter_notebook_config.py and jupyter_server_config.py
c.ServerApp.allow_origin = '*'
c.ServerApp.allow_remote_access = True


jupyter notebook runs at http://localhost:8888/
jupyter server runs on port 9999.

# Node and REACT setup
## One time
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
