
# HARPIA Beam tracking package
This script is a software for tracking probe beam drift on the HARPIA delay line.

## Requirements
 - Installed Light Conversion Launcher application. It is used to run this script.
 - Installed and running HARPIA Service App. Connection with the spectrograph must be successful.
 - Installed and running Camera App. Connection with the camera must be successful. Activated beam profiling function.

## Configuration
 - Start the Launcher application
 - In 'Packages' tab, choose 'Add New Package' and select 'main.py' file of this package
 - The 'HARPIA REST' should be indicated as connected at '127.0.0.1' under the 'Required connections'. If not, check HARPIA Service App and choose 'Refresh' in 'Connections' tab


## Operation
 - Run the HARPIA Beam Tracking script using the Launcher application by clicking 'Start'
 - Install the camera on the probe rail and connect to the Harpia PC.
 - Run the Camera App and enable beam profiling function
 - In HARPIA Service App enable oscillate function of delay line by clicking three dots in ‘Probe Delay’ control field.
Open probe shutter in HARPIA Service App