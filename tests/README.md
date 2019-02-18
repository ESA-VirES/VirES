# TESTS

This directory contains various test scripts.

## Setting up the test environment

The tests are written in Python and require Python 2.7 or Python 3 installed.

### Installation

The get the scripts to your local computer clone the `VirES` repository
```
git clone https://github.com/ESA-VirES/VirES.git
```

Then change the directory to the location of the tests scripts

```
cd VirES/tests/
```

### Magnetic Model

The test of the magnetic model require installation of the
[`eoxmagmod`](https://github.com/ESA-VirES/MagneticModel/tree/staging/eoxmagmod)
Python package. To install this library and its dependencies follow
the installation instructions from the
[ESA-VirES/MagneticModel](https://github.com/ESA-VirES/MagneticModel/)
Git repository.

### ApexPy

Some of the tests require installation of the
[`apexpy`](https://github.com/aburrell/apexpy) Python package.
This package can be installed by the `pip` command:
```
pip install apexpy
```

### CDF Library

To read CDF files install [`spacepy`](https://github.com/spacepy/spacepy)
Python package with the
[NASA CDF](https://cdf.gsfc.nasa.gov/html/sw_and_docs.html) library.

Since the CDF library is a dependency of the magnetic model, its installation
is described in the
[ESA-VirES/MagneticModel](https://github.com/ESA-VirES/MagneticModel/)
Git repository.


## Testing Downloaded Datasets

Following test scripts can be used to test the files downloaded from
the VirES server, e.g., via the web GUI.

### Testing Magnetic Model - `eoxmagmod`

Downloaded modelled magnetic field and residuals can be tested by following script:
```
./test_file_eoxmagmod_magnetic_model.py <model_name> <tested file> [<model_file> ...]
```
This script compares the downloaded values with the locally calculated model values. 

The mode name (.e.g., `CHAOS-6-Combined`, `SIFM`, `IRGF12`, or `Custom`)
is required to identify the tested variable and pick the right model.

The model tests following variables:
`F_<model_name>`, `F_res_<model_name>`, `B_NEC_<model_name>`, `B_NEC_res_<model_name>`
(not all of them must be present in the tested dataset).

Optionally, the model file(s) can be provided to override the defaults.

The script accepts downloaded datasets in both the CDF and CSV format.

### Testing Downloaded VirES dataset against the original Swarm products

Two CDF files containing the same data but each obtained from a different source
can be compared by
```
./compare_cdf_files.py <CDF-file> <CDF-file>
```

The reference files can be filtered manually (emulating the server side filters)
by the following script
```
./filter_cdf_file.py <CDF-input> <CDF-output>
```

The script accepts downloaded datasets in the CDF format only.

### Testing Support Variables - `eoxmagmod`

The support variables (Sun ephemeris, magnetic coordinates or dipole axis
parameters) can be tested by the following script.
```
./test_file_eoxmagmod.py <tested_file>
```
This scripts compares the support variables with the same variables calculated
locally by the `eoxmagmod` package.

The model tests following variables:
`QDLat`, `QDLon`, `QDBasis`, `MLT`,
`NGPLongitude`, `NGPLatitude`, `DipoleTiltAngle`, `DipoleAxisVector`,
`SunDeclination`, `SunRightAscension`, `SunHourAngle`, `SunLongitude`,
`SunVector`, `SunAzimuthAngle`, `SunZenithAngle`
(not all of them must be present in the tested dataset).

The script accepts downloaded datasets in both the CDF and CSV format.

### Testing Support Variables - `apexpy`

The support variables (Sun ephemeris or magnetic coordinates)
can be tested by the following script.
```
./test_file_apexpy.py <tested_file>
```
This scripts compares the support variables with the same variables calculated
locally by the `apexpy` package.

The model tests following variables:
`QDLat`, `QDLon`, `QDBasis`, `MLT`, 
`SunDeclination`, `SunRightAscension`, `SunHourAngle`, `SunLongitude`,
`SunVector`, `SunAzimuthAngle`, `SunZenithAngle`,

The script accepts downloaded datasets in both the CDF and CSV format.

## Testing VirES Server

### Testing Models

The following test set tests the server WPS processes fetching data and,
specifically, the calculated model variables (note that the term model is used
for any calculated variable, including such as, e.g., Sun ephemeris or
magnetic coordinates, and not just magnetic field evaluated by the spherical
harmonic forward expansion).

The test set is executed by
```
 ./test_models.py [-v] [<test-class>[.<test-method>]]
```

#### Server Connection Configuration

By default, the test script expects the tested server running on the local
computer (`http://localhost:80/ows`).
This can be changed by creating simple `service.py` with the server URL and
optional authentication/authorization HTTP headers.

An example `service.py`:
```
SERVICE_URL = "https://tested.server/ows"
HEADERS = [
    ("Authorization", "Basic PHVzZXJuYW1lPjo8cGFzc3dvcmQ+OykK"),
 ]
```
