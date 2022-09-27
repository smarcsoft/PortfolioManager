# AWSW Linux one time preparation
## To install python 3.10:
sudo yum install sqlite-devel.x86_64 #Required by jupyter-lab
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

## To install pip:
sudo yum install python-pip

## To install the SQL Server ODBC drivers:
sudo su
curl https://packages.microsoft.com/config/rhel/6/prod.repo > /etc/yum.repos.d/mssql-release.repo
curl https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo
curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
exit
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel #to avoid conflicts
sudo ACCEPT_EULA=Y yum install -y msodbcsql17
### optional: for bcp and sqlcmd
sudo ACCEPT_EULA=Y yum install -y mssql-tools
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc
#### optional: for unixODBC development headers
sudo yum install -y unixODBC-devel


# Using linux and python to run the stuff
run the linuxsetup.sh script. This will setup the python environment and install the required python packages and switch to the correct python virtual environment.

# Key scripts for Windows
## connect
connect.ps1 connects through ssh to the underlying server infrastructure
Example:
connect.ps1: connects to the main backend server using the default user name (smarcsoft)
connect.ps1 -server scheduler connects to the scheduling server using the default user name
connect.ps1 -username ec2-user -keyfile PortfolioManager.pem -server backend connects to the main compute server using the ec2-user

# Key scripts for Unix
## run
run_remotely.sh: Connects to a compute server to run the update process. This is the script executed by the daily crontab
run.sh: runs the python update process.

## run.sh
Main run script able to run the update process locally.
Examples: 
run.sh -c or run.sh --controller to run the controller.
run.sh --controller --configfile=config/controller_us.json will run the controller for the US market

## un_remotely.sh
Spawns the update process on the AWS compute server
Examples:
run_remotely.sh will:
    . Start the AWS infrastructure
    . run the controller on the compute server
    . Stop the AWS infrastructure
run_remote --no-infra will not spin up and down the infrastructure
run_remote --no-infra --config config/controller_us.json will run the controller remotely on the compute server for the US stock exchnages.

## infrastructure management
start_infra.sh: starts the AWS infrastructure (all of it)
start_compute.sh: starts the main compute server
start_db.sh: starts the database infrastructure
stop_infra.sh: stops the entire AWS infrastructure
stop_compute:sh stops the main compute server
stop_db.sh: stops the database infrastructure