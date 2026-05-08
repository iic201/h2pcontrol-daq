# h2pcontrol-daq starter

A minimal producer-side DAQ package intended to be imported by device servers.

This local package is intentionally small:
- capture request/response events
- buffer locally
- serialize off the RPC hot path
- batch and write JSON locally
- keep all data on the producer side

What it does **not** do:
- connect to a central DAQ
- write HDF5 directly
- write InfluxDB directly
- host any UI
