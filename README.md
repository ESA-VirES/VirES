# VirES for Swarm
VirES for Swarm - installer and utilities

This repository contains the installation and configuration scripts of the
VirES for Swarm system.

The repository contains following directories:

-  `scripts/` - installation and utility scripts
-  `contrib/` - location of the installed SW packages
-  `vagrant/` - vagrant VirES server development machine

NOTE: The repository does not cover the autonomous Cloud-free Coverage
Assembly.

### VirES for Swarm installation

This section describes the VirES installation

#### Prerequisites

The installation should be performed on a *clean* (virtual or physical)
CentOS 7 machine. Although not tested, it is assumed that the installation
will also work on the RHEL 7 and its other clones.

The installation requires access to the Internet.

The installation scripts may search for some the SW installation packages
in the `contrib/` directory or they try to download the SW
packages form the predefined location. As not all SW packages are available
on-line some of the SW packages might need to be copied manually
and put in the `contrib/` directory beforehand.

(Currently, the built web client needs to be copied manually. More details TBD.)


#### Step 1 - Get the Installation Scripts

The installer (i.e., content of this repository) can be obtained
either as on of the [tagged
releases](https://github.com/ESA-VirES/VirES/releases)
or by cloning of the repository:

```bash
git clone https://github.com/ESA-VirES/VirES.git
```

#### Step 2 - Prepare the installed SW packages

Put the SW packages which cannot be downloaded automatically
to the `VirES/contrib/` directory.

#### Step 3 - Run the Installation

Execute the installation script with the root's permission:

```bash
sudo VirES/scripts/install.sh
```

The output of the `install.sh` command is automatically saved to a log file
which can be inspected in case of failure.

```bash
less -rS  install.log
```

The `install.sh` command executes the individual installation scripts
located in the `scripts/install.d/` directory:

```bash
ls VirES/scripts/install.d/
00_selinux.sh    20_apache.sh         30_eoxs_rpm.sh
05_limits.sh     20_django.sh         30_vires_rpm.sh
10_rpm_repos.sh  20_gdal.sh           31_eoxs_wsgi.sh
15_curl.sh       20_mapserver.sh      45_client_install.sh
15_jq.sh         20_postgresql.sh     50_eoxs_instance.sh
15_unzip.sh      25_spacepy.sh        55_client_config.sh
15_wget.sh       30_eoxmagmod_rpm.sh  70_eoxs_load_fixtures.sh
```

By default, all these installation scripts are executed in order given by the
numerical prefix. However, the `install.sh` command allows execution of
the explicitly selected scripts as, e.g., in following command
(re-)installing and (re-)configuring the EOxServer instance:

```bash
sudo VirES/scripts/install.sh
VirES/scripts/scripts.d/{50_eoxs_instance.sh,70_eoxs_load_fixtures.sh}
```

This allows installation and/or update of selected SW packages only.



### VirES-Server Development Environment

The repository provides a vagrant machine to quickly set up a development
instance of the VirES server.

#### Step 1 - Clone the Required Repositories

```bash
git clone git@github.com:ESA-VirES/VirES.git
git clone git@github.com:ESA-VirES/VirES-Server.git
git clone git@github.com:EOxServer/eoxserver.git
```

Currently, the optional built web client can be copied manually to the `contrib`
directory:

```bash
cp WebClient-Framework.tar.gz VirES/contrib/
```

#### Step 2 - Customisation

The custom configuration option to be applied to your Vagrant instance can
be put in the optional `VirES/scripts/user.conf` file. The environment
variables defined in this file will override the installation defaults.

Example `user.conf`:
```
CONFIGURE_ALLAUTH=YES
TEMPLATES_DIR_SRC="/usr/local/vires-dempo_ops/templates"
FIXTURES_DIR_SRC="/usr/local/vires-dempo_ops/fixtures"
```

#### Step 3 - Start the Vagrant Machine

```bash
cd VirES/vagrant
vagrant up
```

#### Quick Start

After the installation the web server should be up and running and
if can be access on following at following URLs:

```
http://localhost:8300
http://localhost:8300/eoxs
http://localhost:8300/ows
```

To enter the vagrant machine use following command
```
vagrant ssh
```

To control the VirES installation change to the `scripts/` folder
```
cd VirES/scripts/
```

To restart the web server (including the asynchronous processing daemon)
use following script located in the `script` folder
```
./restart_server.sh
```

To call the EOxServer's `manage.py` with the activated `virtualenv` environment
use the following convenience command in the `scripts/` folder
```
./venv_vires_manage.sh [<options>]
```

To call Python with the activated `virtualenv` environment
use the following convenience command in the `scripts/` folder
```
./venv_vires_python.sh [<options>]
```

To call an arbitrary command with activated `virtualenv` environment
use the following convenience command in the `scripts/` folder
```
./venv_vires_execute.sh <command> [<options>]
```
