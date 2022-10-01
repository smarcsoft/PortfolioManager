# Jupyter lab setup:
## One-time setup:
pip install jupyterlab
pip install notebook
pip install voila
pip install matplotlib

## Start-up:
In this directory:
jupyter-lab
jupyter notebook
voila 

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

## Operations on the proxy:
/etc/init.d/bitnami start/stop
The correct proxy configuration is the following (after 2 days of research/work)
<VirtualHost 172.26.1.230>
  ProxyPreserveHost On
  ProxyRequests Off
  ProxyPass / http://[computeIP]:9999/
  ProxyPassReverse / http://[computeIP]:9999/
  RequestHeader set Origin "http://[computeIP]:9999"
  RequestHeader set Host "[computePrivateIP]"
  ServerName pm.smarcsoft.com

  <Location "/api/kernels"> 
   ProxyPass ws://[computeIP]:9999/api/kernels
   ProxyPassReverse ws://[computeIP]:9999/api/kernels
  </Location>
</VirtualHost>
