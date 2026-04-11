# h2pcontrol-daq

This is the daq (data acquisition) component of the h2pcontrol system. It is responsible for acquiring data from various sensors and devices,
and sending it to the h2pcontrol-daq server for processing, storage and UI.

There are two parts of this project, the first one is the h2pcontrol-daq server [`h2pcontrol-daq/server`], which is responsible for receiving data from the device servers and processing it,
and the second one is the h2pcontrol-daq package [`h2pcontrol-daq/lib`], which is responsible for giving an easy interface to the device servers to send data to the h2pcontrol-daq server.

## Installation for the package

For the installation of the python package (the `h2pcontrol-daq/lib`), you just have to do the following:

```bash
pip install h1pcontrol-daq
```

The installation is available like this because the package is published on PyPI, which is the Python Package Index.
This allows users to easily install the package using pip, which is the standard package manager for Python.
You can also see the github workflow used to make the release of the package in the `.github/workflows/release.yml` file.
