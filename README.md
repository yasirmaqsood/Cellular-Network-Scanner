# Cellular Network Scanner
The aim of this tool is to extract significant network parameters of cellular networks. This utilizes the Service Mode of Mobile device to extract network parameters of 2G/3G/4G active in a operating vicinity.
For the moment, the tool has only been tested and developed for the following devices:

- Samsung Galaxy S5

- Samsung Galaxy S7

Note: All the mobile devices used to fetch the data need to be Rooted and unlocked.

# Requirements
Here are the following requirements:

- Ubuntu

- Python 3;

- A compatible mobile phone (rooted) - Samsung S5/S7

- A valid and active SIM card

- USB Debugging On

- Mobile Phone on MTP transfer

# How to Use
The tool can be operated easily by running the scanner script
```
sudo python3 scanner.py
```
# Saving Results

The results of one scan will be saved in a folder with a name of "scanneroutput.txt"

```
Data written to scanneroutput.txt
```

The result of a scan is:
```
----------------- 2G/GSM ------------------------------
PLMN=410-6
Type=2G
LAC=338
CID=268435455
,
----------------- 4G/LTE ------------------------------
Serving_PLMN=410-4
Type=4G
LAC=5035
ARFCN=0
PCI=120
,

Serving_PLMN=410-1
Type=4G
LAC=11001
ARFCN=0
PCI=467
,
Serving_PLMN=410-6
Type=4G
LAC=11128
ARFCN=0
PCI=153
,
----------------- 3G/UMTS ------------------------------
PLMN=410-4
Type=3G
LAC=31302
CID=53320054
,
PLMN=410-6
Type=3G
LAC=1127
CID=13447473

```
#### NOTE: The 2G/3G/4G heading is just for demonstration purposes in readme

# Customization

Currently work is done to make it work in every environment by using "AT+COPS?" command to search active mobile operators and their MCC/MNCs in the operating environment and automatically search for available network parameters of thos networks.

Note that retrieving results from AT+COPS command could take a lot of time and sometime would need to restart the tool.


