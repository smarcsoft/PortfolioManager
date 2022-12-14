# AWS Linux one time preparation
## To install python 3.10 on the compute servers:
sudo yum install sqlite-devel.x86_64 #Required by jupyter-lab
sudo yum install bzip2-devel  #Required for pandas 
sudo yum -y groupinstall "Development Tools"
sudo yum -y install gcc devel libffi-devel openssl11 openssl11-devel
wget https://www.python.org/ftp/python/3.10.2/Python-3.10.2.tgz
tar zxvf Python-3.10.2.tgz
cd Python-3.10.2/
./configure
make
sudo make altinstall

Check the installed version:
python3.10 --version

### To install pip:
sudo yum install python-pip

### To install the SQL Server ODBC drivers:
sudo su
curl https://packages.microsoft.com/config/rhel/6/prod.repo > /etc/yum.repos.d/mssql-release.repo
curl https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo
curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
exit
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel #to avoid conflicts
sudo ACCEPT_EULA=Y yum install -y msodbcsql17
#### optional: for bcp and sqlcmd
sudo ACCEPT_EULA=Y yum install -y mssql-tools
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
##### optional: for unixODBC development headers
sudo yum install -y unixODBC-devel

## To install python 3.10 on the scheduling server:
sudo apt update && sudo apt upgrade
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz
tar -xf Python-3.10.*.tgz
cd Python-3.10.*/
./configure --enable-optimizations
make -j 4
sudo make altinstall
Check result with python3.10 --version
cd ..;sudo rm -rf Python-3.10.0 Python-3.10.0.tgz



# Using linux and python to run the stuff
run the linuxsetup.sh script. This will setup the python environment and install the required python packages and switch to the correct python virtual environment.

# Key scripts for Windows
## connect
connect.ps1 connects through ssh to the underlying server infrastructure
Example:
**connect.ps1**: connects to compute server using the default user name (smarcsoft)
**connect.ps1 -username ec2-user -keyfile PortfolioManager.pem -server backend** connects to the main compute server using the ec2-user
**connect.ps1 -server session** connects to the session manager
**connect.ps1 -server scheduler** connects to the scheduling server using the default user name (will be deprecated)


# Key scripts for Unix
start_instance.sh: This is the master scripts. It starts the compute server if needed, run jupiter on it, and configure the web proxy to access it through pm.smarcsoft.com
run_update.sh: Connects to a compute server to run the update process. This is the script executed by the daily crontab
run_jupiter.sh: Connects to a compute server to run the jupiter server.
run.sh: runs the python update process.
run_fx_update.sh: runs the fx feeder remotely
run_fx.sh: runs the fx feeder locally. Called by run_fx_update.sh
restart_proxy.sh: Restarts the reverse proxy

## run.sh
Main run script able to run the update process locally. Prefer run_update.sh over run.sh.
Examples: 
run.sh -c or run.sh --controller to run the controller.
./run.sh --controller --config config/controller_us.json --batch Batch_01 : Will run the first batch for the US
./run.sh --type fundamental_data --config config/pm.conf --exchange US : Will get fundamental data for the US
./run.sh --config config/pm.conf --exchange LSE : will run the update process for the london stock exchange

## run_update.sh
Spawns the update process on the AWS compute server

run_update.sh will:
    . Start the AWS infrastructure
    . run the controller on the compute server
    . Stop the AWS infrastructure
### Examples:
run_update.sh --no-infra will not spin up and down the infrastructure
run_update.sh --no-infra --config config/controller_us.json will run the price loader controller remotely on the compute server for the US stock exchanges.
run_update.sh --type fundamental_data --config config/controller_us.json will run the fundamental data loader controller remotely on the compute server for the US stock exchanges.
run_update.sh --type fundamental_data --config config/controller_us.json --batch Batch_01

## run_jupiter.sh
Runs the jupiter server on the AWS compute server. Will start the server if not running.
Examples:
run_jupiter.sh --no-infra will not spin up the infrastructure
run_jupiter.sh will spin up the infrastructure if needed and will run the jupiter server on it.

## infrastructure management
start_infra.sh: starts the AWS infrastructure (all of it)
start_compute.sh: starts the main compute server
start_db.sh: starts the database infrastructure
stop_infra.sh: stops the entire AWS infrastructure
stop_compute:sh stops the main compute server
stop_db.sh: stops the database infrastructure

### start_compute.sh [--check]
starts the main compute server. If --check is provided, checks if the infrastructure is already started and prints the public (first) and private IP (second) addresses of the server like "x.x.x.x,y.y.y.u" if the compute server is started or "not started" otherwise

### indexer.sh
Runs the indexation process to speed up symbol searches. 
Example:
indexer.sh --no-infra will run the indexer on the remote compute server without starting/stopping the compute server
indexer.sh --config config/pm.conf will run the indexation process on the compute server