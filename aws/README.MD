# AWSW Linux one time preparation
## To install python 3.10:
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
