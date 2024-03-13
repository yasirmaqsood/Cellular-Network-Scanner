#IMPORT
import subprocess
import time
import xml.etree.ElementTree as ET
import serial
import os
import re # from extract.py

# Define regex patterns to extract required information for GSM
gsm_patterns = {
    'PLMN': r'Serving PLMN\((\d+-\d+)\)',
    'LAC': r'LAC:(\d+)',
    #'Band': r'GSM:(\d+)',
    'CID': r'CID: (\w+)',
    #'Rx_Power': r'Rx Pwr: (-?\d+)',
    #'ARFCN': r'BCCH: (\d+)',
    #'RxL_RxQ': r'RxL: (\d+), RxQ: (\d+)'
}

# Define regex patterns to extract required information for UMTS
umts_patterns = {
    'PLMN': r'Serving PLMN\((\d+-\d+)\)',
    'LAC': r'LAC:(\d+)',
    #'RAC': r'RAC:(\d+)',
    #'Band': r'Band:(\d+)',
    'CID': r'CID:(\w+)',
    #'Rx_Power': r'RI:(-?\d+)',
    #'UARFCN': r'RX:(\d+) RI',
    #'RSCP': r'RSCP:(-?\d+)',
    #'PSC': r'PSC:(\d+)'
}

# Define regex patterns to extract required information for LTE
lte_patterns = {
    'Serving_PLMN': r'Serving PLMN\((\d+-\d+)\) - LTE',
    'Selected_PLMN': r'Selected PLMN\((\d+-\d+)\) - GSM',
    'TAC': r'TAC\((\d+)\)',
   # 'Band_BW': r'BAND:(\d+) BW: (\d+)',
    'Earfcn_PCI': r'Earfcn: (\d+), PCI: (\d+)',
   # 'RSRP': r'RSRP:(-?\d+)',
    #'RSRQ': r'RSRQ:(-?\d+)',
    #'SNR': r'SNR:(-?\d+\.\d+)',
}


# Serial number of the device connected i.e. S7
device_serial = '44372415'
nw_type=14
duplicate_list=[]
duplicate_items=""

# ATCommands class to run AT commands in the mobile device using adb shell
class ATCommands:
    def __init__(self, tty_path):
        self.tty_int = serial.Serial(tty_path, 115200)

    def _parseCOPS(self, string):
        # Parse AT+COPS=? information
        dict_ = {}
        rstr = string.replace(b'+COPS: ', b'')
        for x in rstr.split(b'),'):
            ysp = x.split(b',')
            if len(ysp) >= 5:
                mccmnc = ysp[3].decode("utf-8").replace('"', '')
                netname = ysp[1].decode("utf-8").replace('"', '')
                if mccmnc not in dict_:
                    dict_[mccmnc] = netname
        return dict_

    def getCOPS(self):
        self.tty_int.write(b'AT+COPS=?\r\n')
        self.tty_int.readline()  # command sent
        result = self.tty_int.readline()
        return self._parseCOPS(result)


    #Function to change the PLMN as well as network tehnology
    def changePLMN(self, MCCMNC,types ,automode=False):

        """# Airplane mode ON
        self.tty_int.write(b"AT+CFUN=4\r\n")
        time.sleep(5)

        #Airplane mode OFF
        self.tty_int.write(b"AT+CFUN=1\r\n")
        """
        global nw_type


        if nw_type!=types:
            print(nw_type)
            print(types)
            nw_type=types
            print(nw_type)
            print(types)
            try:
                # Use the provided network type in the AT^SYSCONFIG command
                self.tty_int.write(
                    b"AT^SYSCONFIG=%i,1,1,2\r\n" % types)  # type= '13' for 2G, '14' for 3G and '2' for 4G
                response = self.tty_int.read_all()
                time.sleep(7)

            except Exception as e:
                print(f"Error changing network type: {e}")
        else:
            nothing=0


        mode = 1
        if automode:
            mode = 0

        self.tty_int.write(b"AT+COPS=%i,2,\"%s\"\r\n" % (mode, MCCMNC.encode('utf-8')))  # For auto mode for 4G
        """if types==4:
            self.tty_int.write(b"AT+COPS=%i,2,\"%s\"\r\n" % (mode, MCCMNC.encode('utf-8')))  # For auto mode for 4G
        else:
            self.tty_int.write(b"AT+COPS=%i,2,\"%s\",%s\r\n" % (mode, MCCMNC.encode('utf-8'), str(types).encode(
                'utf-8')))  # For 2G/3G i.e. 'types=0 for GSM and types = 2 for UMTS'"""
        """if types==4:
            self.tty_int.write(b"AT+COPS=%i,2,\"%s\",%s\r\n" % (mode, MCCMNC.encode('utf-8'), str(types).encode(
                'utf-8')))  # For 2G/3G i.e. 'types=0 for GSM and types = 2 for UMTS'"""


    # Add a delay to allow the network selection to take effect

    def unregister(self):
        self.tty_int.write(b"AT+COPS=2\r\n")

    def airplane(self):
        #Airplane mode ON
        self.tty_int.write(b"AT+CFUN=4\r\n")
        time.sleep(5)

        #Airplane mode OFF
        self.tty_int.write(b"AT+CFUN=1\r\n")
        time.sleep(2)


    def changeNetworkType(self, type_):
        try:
            # Use the provided network type in the AT^SYSCONFIG command
            self.tty_int.write(b"AT^SYSCONFIG=%i,1,1,2\r\n" % type_)
            response = self.tty_int.read_all()
            print(f"Response from modem: {response.decode('utf-8')}")
            time.sleep(10)

        except Exception as e:
            print(f"Error changing network type: {e}")








def send_at_command(at_command):
    subprocess.run(
        f"adb shell am broadcast -a android.provider.Telephony.SECRET_CODE -d android_secret_code://{at_command}",
        shell=True)

# Function to check if new data set is already present in the existing file content
def is_duplicate_data(new_data_set, existing_data):
    return new_data_set + ',' in existing_data

# This function reads the .xml file. extracts only node->text data from the file. then saves the output in a favourable format to the output file i.e scanneroutput.txt
def extract_and_dump():
    desired_path = "/home/mscanner/Documents/Scanner/window_dump.xml"
    # Capture the data on the new screen using uiautomator
    uiautomator_command = f"adb -s {device_serial} shell uiautomator dump -o /sdcard/window_dump.xml"
    subprocess.run(uiautomator_command, shell=True)

    # Pull the uiautomator dump file from the device to your PC
    uiautomator_dump_command = f"adb -s {device_serial} pull /sdcard/window_dump.xml {desired_path}"
    subprocess.run(uiautomator_dump_command, shell=True)

    # Specify the path to your XML file
    xml_file_path = '/home/mscanner/Documents/Scanner/window_dump.xml'

    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Open a new file for writing
    with open("/home/mscanner/Documents/Scanner/scanneroutput.txt", "a") as output_file:
        con_type = ""
        arfcn = ""
        band=""
        psc=""
        cid=""
        plmn=""
        lac=""
        extract_func=extract_info_lte
        # Iterate through the nodes and write the 'text' attribute to the file
        for node in root.iter('node'):
            text_value = node.get('text')

            if text_value:
                if text_value.strip().__contains__("Serving"):
                    plmn = text_value.strip()
                    if (plmn.__contains__("GSM")):
                        con_type = "2G"
                    elif (plmn.__contains__("WCDMA")):
                        con_type = "3G"
                    elif (plmn.__contains__("LTE")):
                        con_type = "4G"
                    print(plmn)
                    print(con_type)
                if text_value.strip().__contains__("LAC"):
                    lac = text_value.strip()
                    print(lac)
                if text_value.strip().__contains__("TAC"):
                    if con_type=="4G":
                        lac = text_value.strip()
                            print(lac)
                          

                    else:
                        lac = text_value.strip()
                        print(lac)
                if text_value.strip().__contains__("ARFCN"):
                    arfcn = text_value.strip()
                    print(arfcn)
                if text_value.strip().__contains__("BCCH"):
                    arfcn = text_value.strip()
                    print(arfcn)
                if text_value.strip().__contains__("Rx"):
                    arfcn = text_value.strip()
                    print(arfcn)
                if text_value.strip().__contains__("Earfcn"):
                    arfcn = text_value.strip()
                    print(arfcn)
                if text_value.strip().__contains__("Band"):
                    band = text_value.strip()
                    print(band)
                if text_value.strip().__contains__("BAND"):
                    band = text_value.strip()
                    print(band)
                if text_value.strip().__contains__("IDLE"):
                    match = re.search(r'GSM(\d+)', text_value.strip())
                    if match:
                        band = "GSM"+":" + match.group(1)
                        print(band)
                if text_value.strip().__contains__("CID"):
                    cid = text_value.strip()
                    print(cid)
                if text_value.strip().__contains__("PSC"):
                    psc = text_value.strip()
                    print(psc)
        if con_type == "2G":
            extract_func = extract_info_gsm
        elif con_type == "3G":
            extract_func = extract_info_umts
        elif con_type == "4G":
            extract_func = extract_info_lte
        else:
            xy=0#raise ValueError("File type not supported")


        # ----------- ORIGINAL --------------------------
        lines = [plmn, lac, arfcn, band, cid, psc]
        global duplicate_list
        global duplicate_items

        extracted_info = {}
        for line in lines:
            info = extract_func(line)
            if info:
                extracted_info.update(info)

        duplicate_items = ""  # Reset duplicate_items for each iteration
        for key, value in extracted_info.items():
            duplicate_items += str(value)

        if duplicate_items not in duplicate_list:
            if len(duplicate_items) > 1:
                duplicate_list.append(duplicate_items)
                print(duplicate_list)
                for key, value in extracted_info.items():
                    output_file.write(f'{key}={value}\n')  # Each parameter on a new line
                output_file.write(',\n')  # Add a comma at the end of the last value
                print("Data written to output.txt")
                output_file.close()

        """if band.strip().__contains__(":2"):
            f=1
        else:
            extracted_info = {}
            for line in lines:
                info = extract_func(line)
                if info:
                    extracted_info.update(info)
            for key, value in extracted_info.items():
                output_file.write(f'{key}={value}\n')  # Each parameter on a new line
            output_file.write(',\n')  # Add a comma at the end of the last value
            print("Data written to scanneroutput.txt")
            output_file.close()"""



        # ----------- ORIGNAL END--------------------------

#----------- Code for multiple rounds for 2G/3G and 4G--------------
def run_mutiple_times(times,lte):

    # Initialize ATCommands
    at_commands = ATCommands('/dev/ttyACM0')

    # Example usage of ATCommands
    # ---print(at_commands.getCOPS())

    print("Switching to GSM")
    at_commands.changeNetworkType(13)

    for i in range(times):
        # --------------------------- 2G - GSM --------------------------

        at_commands.changePLMN('41001', 13)  # Change PLMN to 41001
        time.sleep(5)
        at_commands.changePLMN('41001', 13)  # Change PLMN to 41001
        time.sleep(5)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41003', 13)  # Change PLMN to 41003
        time.sleep(5)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41004', 13)  # Change PLMN to 41004
        time.sleep(5)
        at_commands.changePLMN('41004', 13)  # Change PLMN to 41004
        time.sleep(2)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41006', 13)  # Change PLMN to 41006
        time.sleep(3)
        at_commands.changePLMN('41006', 13)  # Change PLMN to 41006
        time.sleep(2)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

    print("Switching to lTE")
    at_commands.changeNetworkType(2)
    at_commands.changeNetworkType(2)

    for i in range(times):
        # ------  4G - LTE -----------
        time.sleep(2)
        at_commands.changePLMN('41004', 2)  # Change PLMN to 41001
        time.sleep(5)
        at_commands.changePLMN('41004', 2)  # Change PLMN to 41001
        time.sleep(3)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)
        

        at_commands.changePLMN('41001', 2)  # Change PLMN to 41004
        time.sleep(5)
        at_commands.changePLMN('41001', 2)  # Change PLMN to 41004
        time.sleep(3)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41003', 2)  # Change PLMN to 41003
        time.sleep(5)
        at_commands.changePLMN('41003', 2)  # Change PLMN to 41003
        time.sleep(3)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41001', 2)  # Change PLMN to 41004
        time.sleep(5)
        at_commands.changePLMN('41001', 2)  # Change PLMN to 41004
        time.sleep(3)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41006', 2)  # Change PLMN to 41006
        time.sleep(4)
        at_commands.changePLMN('41006', 2)  # Change PLMN to 41006
        time.sleep(4)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41051', 2)  # Change PLMN to 41006
        time.sleep(5)
        at_commands.changePLMN('41051', 2)  # Change PLMN to 41006
        time.sleep(3)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

    print("Switching to UMTS")
    at_commands.changeNetworkType(14)
    at_commands.changeNetworkType(14)
    time.sleep(2)

    for i in range(times):
        # ------  3G - UMTS -----------

        at_commands.changePLMN('41003', 14)  # Change PLMN to 41003
        time.sleep(5)
        at_commands.changePLMN('41003', 14)  # Change PLMN to 41003
        time.sleep(5)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41004', 14)  # Change PLMN to 41004
        time.sleep(5)
        at_commands.changePLMN('41004', 14)  # Change PLMN to 41004
        time.sleep(5)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41006', 14)  # Change PLMN to 41006
        time.sleep(3)
        at_commands.changePLMN('41006', 14)  # Change PLMN to 41006
        time.sleep(2)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)

        at_commands.changePLMN('41001', 14)  # Change PLMN to 41001
        time.sleep(5)
        at_commands.changePLMN('41001', 14)  # Change PLMN to 41001
        time.sleep(5)
        extract_and_dump()  # function call to extract data from .xml file and save to output file only he required parameters
        time.sleep(5)






        


# Function to run the ussd code on the mobile in order to access service menu
def dial_ussd_code(ussd_code):

    # Construct the ADB command to open the dialer app
    open_dialer_command = f"adb -s {device_serial} shell am start -a android.intent.action.DIAL"

    # Construct the ADB command to input the USSD code
    input_ussd_code_command = f"adb -s {device_serial} shell input text '{ussd_code}'"

    # Execute the ADB command to open the dialer
    subprocess.run(open_dialer_command, shell=True)
    time.sleep(2)  # Add a delay to allow the dialer to open

    # Execute the ADB command to input the USSD code
    subprocess.run(input_ussd_code_command, shell=True)
    time.sleep(2)  # Add a delay to allow the USSD code to be entered




    """# Read the content of the uiautomator dump file
    with open("window_dump.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()"""

#----------------------------------------------------------------------------------------------------------------------------------------


# Function to extract the data from GSM captured parameters
def extract_info_gsm(line):
    info = {}
    for key, pattern in gsm_patterns.items():
        match = re.search(pattern, line)
        if match:
            if key == 'CID':
                info[key] = int(match.group(1), 16)
            else:
                info[key] = match.group(1)
    info['Type'] = '2G'
    return info

# Function to extract the data from UMTS captured parameters
def extract_info_umts(line):
    info = {}
    for key, pattern in umts_patterns.items():
        match = re.search(pattern, line)
        if match:
            if key == 'CID':
                info[key] = int(match.group(1), 16)
            elif key == 'UARFCN':
                info['ARFCN'] = match.group(1)
            else:
                info[key] = match.group(1)
    info['Type'] = '3G'
    return info

# Function to extract the data from LTE captured parameters
def extract_info_lte(line):
    info = {}
    for key, pattern in lte_patterns.items():
        match = re.search(pattern, line)
        if match:
            if key == 'Serving_PLMN' or key == 'Selected_PLMN':
                info[key] = match.group(1)
            elif key == 'TAC':
                info['LAC'] = match.group(1)
            elif key == 'Band_BW':
                info['Band'] = match.group(1)
                info['BW'] = match.group(2)
            elif key == 'Earfcn_PCI':
                info['ARFCN'] = match.group(1)
                info['PCI'] = match.group(2)
            else:
                info[key] = match.group(1)
    info['Type'] = '4G'
    return info




at_commands = ATCommands('/dev/ttyACM0')
"""at_commands.changeNetworkType()
time.sleep(5)"""


"""at_commands.changePLMN('41001', 2)  # Change PLMN to 41001
time.sleep(10)"""

# USSD code to opening preferred network type
#dial_ussd_code('*#*#4636#*#*',1)
#time.sleep(6)

at_commands.airplane()

# USSD code to open service menu
dial_ussd_code('*#0011#')

#Function call to run the scanning process multiple times
run_mutiple_times(2,1)


