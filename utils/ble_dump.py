from bluepy.btle import Scanner
scanner = Scanner()
devices = scanner.scan(2)
for dev in devices:
    print ("\n--------------------------------\n")
    print ("MAC - {}".format(dev.addr))
    print("RSSI - {}".format(dev.rssi))
    #ibeacon_data = dev.getScanData()[3][2][8:50]
    #uuid = ibeacon_data[0:32]
    #print("uuid - {}".format(uuid))
    for (adtype, desc, value) in dev.getScanData():
        print ("{}:{}".format(desc,value))
        if "Local Name" in desc:
            name = value
            print(name)
