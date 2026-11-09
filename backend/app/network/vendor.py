"""
IEEE OUI Vendor Lookup Module
Expanded with common vendors for enterprise, consumer, and IoT network hardware.
"""
import re

OUI_DATABASE = {
    # Apple
    "00:03:93": "Apple, Inc.",
    "00:05:02": "Apple, Inc.",
    "00:0A:95": "Apple, Inc.",
    "00:10:FA": "Apple, Inc.",
    "00:14:51": "Apple, Inc.",
    "00:1B:63": "Apple, Inc.",
    "00:1C:B3": "Apple, Inc.",
    "00:1E:C2": "Apple, Inc.",
    "00:23:12": "Apple, Inc.",
    "00:25:00": "Apple, Inc.",
    "00:26:08": "Apple, Inc.",
    "00:26:BB": "Apple, Inc.",
    "3C:07:54": "Apple, Inc.",
    "40:6C:8F": "Apple, Inc.",
    "AC:BC:32": "Apple, Inc.",
    "F0:18:98": "Apple, Inc.",
    "F4:5C:89": "Apple, Inc.",
    "BC:D0:74": "Apple, Inc.",
    "E4:54:E8": "Apple, Inc.",
    "DC:A9:04": "Apple, Inc.",
    "60:F8:1D": "Apple, Inc.",

    # Intel
    "00:02:B3": "Intel Corporate",
    "00:03:47": "Intel Corporate",
    "00:04:23": "Intel Corporate",
    "00:0E:0C": "Intel Corporate",
    "00:13:02": "Intel Corporate",
    "00:13:E8": "Intel Corporate",
    "00:15:00": "Intel Corporate",
    "00:19:D1": "Intel Corporate",
    "00:1B:21": "Intel Corporate",
    "00:21:5C": "Intel Corporate",
    "00:24:D7": "Intel Corporate",
    "08:11:96": "Intel Corporate",
    "34:13:E8": "Intel Corporate",
    "68:05:CA": "Intel Corporate",
    "80:86:F2": "Intel Corporate",
    "A4:4C:C8": "Intel Corporate",
    "E0:E2:58": "Intel Corporate",

    # TP-Link
    "00:1D:0F": "TP-Link Corporation",
    "00:21:27": "TP-Link Corporation",
    "00:23:CD": "TP-Link Corporation",
    "00:27:19": "TP-Link Corporation",
    "14:CC:20": "TP-Link Corporation",
    "30:B5:C2": "TP-Link Corporation",
    "3C:84:6A": "TP-Link Corporation",
    "50:C7:BF": "TP-Link Corporation",
    "60:32:B1": "TP-Link Corporation",
    "70:4F:57": "TP-Link Corporation",
    "AC:84:C6": "TP-Link Corporation",
    "C0:06:C3": "TP-Link Corporation",
    "C4:6E:1F": "TP-Link Corporation",
    "E8:48:B8": "TP-Link Corporation",
    "F4:F2:6D": "TP-Link Corporation",
    "CC:ED:21": "TP-Link Corporation",

    # Netgear
    "00:09:5B": "Netgear Inc.",
    "00:0F:B5": "Netgear Inc.",
    "00:14:6C": "Netgear Inc.",
    "00:18:4D": "Netgear Inc.",
    "00:1E:2A": "Netgear Inc.",
    "00:24:B2": "Netgear Inc.",
    "04:A1:51": "Netgear Inc.",
    "20:E5:2A": "Netgear Inc.",
    "2C:30:33": "Netgear Inc.",
    "84:1B:5E": "Netgear Inc.",
    "9C:3D:CF": "Netgear Inc.",

    # Cisco
    "00:00:0C": "Cisco Systems",
    "00:01:42": "Cisco Systems",
    "00:01:43": "Cisco Systems",
    "00:02:16": "Cisco Systems",
    "00:06:52": "Cisco Systems",
    "00:07:0D": "Cisco Systems",
    "00:0C:85": "Cisco Systems",
    "00:11:20": "Cisco Systems",
    "00:17:59": "Cisco Systems",
    "00:26:0B": "Cisco Systems",
    "70:81:05": "Cisco Systems",

    # Google
    "00:1A:11": "Google, Inc.",
    "3C:5A:B4": "Google, Inc.",
    "54:60:09": "Google, Inc.",
    "74:E5:43": "Google, Inc.",
    "94:EB:CD": "Google, Inc.",
    "D8:6C:63": "Google, Inc.",
    "F8:8F:C2": "Google, Inc.",

    # Microsoft
    "00:03:FF": "Microsoft Corporation",
    "00:0D:3A": "Microsoft Corporation",
    "00:12:5A": "Microsoft Corporation",
    "00:15:5D": "Microsoft Corporation (Hyper-V)",
    "00:17:FA": "Microsoft Corporation",
    "00:22:48": "Microsoft Corporation",
    "00:50:F2": "Microsoft Corporation",
    "28:18:78": "Microsoft Corporation",
    "7C:1E:52": "Microsoft Corporation",

    # Raspberry Pi
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Trading",
    "E4:5F:01": "Raspberry Pi (Trading) Ltd",
    "28:CD:C1": "Raspberry Pi (Trading) Ltd",

    # Lenovo
    "00:1A:6B": "Lenovo Mobile",
    "00:21:CC": "Lenovo",
    "40:B0:34": "Lenovo",
    "54:EE:75": "Lenovo",
    "60:D8:19": "Lenovo",
    "70:72:0D": "Lenovo",
    "98:FA:9B": "Lenovo",
    "E8:6A:64": "Lenovo",

    # Dell
    "00:06:5B": "Dell Computer Corp.",
    "00:08:74": "Dell Computer Corp.",
    "00:0B:DB": "Dell Computer Corp.",
    "00:11:43": "Dell Inc.",
    "00:14:22": "Dell Inc.",
    "00:18:8B": "Dell Inc.",
    "00:19:B9": "Dell Inc.",
    "18:03:73": "Dell Inc.",
    "74:86:7A": "Dell Inc.",
    "B8:2A:72": "Dell Inc.",

    # HP
    "00:01:E6": "Hewlett-Packard Company",
    "00:08:02": "Hewlett-Packard Company",
    "00:0E:7F": "Hewlett-Packard Company",
    "00:11:0A": "Hewlett-Packard Company",
    "00:15:60": "Hewlett-Packard Company",
    "00:17:A4": "Hewlett-Packard Company",
    "10:1F:74": "Hewlett Packard Enterprise",
    "2C:44:FD": "Hewlett-Packard Company",

    # Realtek
    "00:07:0E": "Realtek Semiconductor",
    "00:0A:CD": "Realtek Semiconductor",
    "00:E0:4C": "Realtek Semiconductor",
    "38:A7:46": "Realtek Semiconductor",
    "52:54:00": "QEMU Virtual NIC / Realtek",

    # Samsung
    "00:00:F0": "Samsung Electronics",
    "00:02:78": "Samsung Electronics",
    "00:07:AB": "Samsung Electronics",
    "00:12:47": "Samsung Electronics",
    "00:15:99": "Samsung Electronics",
    "00:18:AF": "Samsung Electronics",
    "28:BA:B5": "Samsung Electronics",
    "50:77:05": "Samsung Electronics",
    "A8:06:00": "Samsung Electronics",
    "BC:44:86": "Samsung Electronics",

    # Xiaomi / OnePlus
    "64:A2:F9": "Xiaomi Communications",
    "7C:49:EB": "Xiaomi Communications",
    "AC:F7:F3": "Xiaomi Communications",
    "88:C9:D0": "OnePlus Technology",
    "9C:28:B3": "OnePlus Technology",

    # Asus
    "00:0C:6E": "ASUSTek Computer Inc.",
    "00:15:F2": "ASUSTek Computer Inc.",
    "00:1B:FC": "ASUSTek Computer Inc.",
    "04:D9:F5": "ASUSTek Computer Inc.",
    "10:7B:44": "ASUSTek Computer Inc.",
    "2C:4D:54": "ASUSTek Computer Inc.",

    # Amazon
    "00:FC:8B": "Amazon Technologies Inc.",
    "40:B4:CD": "Amazon Technologies Inc.",
    "44:65:0D": "Amazon Technologies Inc.",
    "68:37:E9": "Amazon Technologies Inc.",
    "74:75:48": "Amazon Technologies Inc.",
    "AC:63:BE": "Amazon Technologies Inc.",
    "FC:65:DE": "Amazon Technologies Inc.",

    # Ubiquiti / UniFi
    "00:27:22": "Ubiquiti Networks",
    "04:18:D6": "Ubiquiti Networks",
    "24:A4:3C": "Ubiquiti Networks",
    "68:D7:9A": "Ubiquiti Networks",
    "78:8A:20": "Ubiquiti Networks",
    "B4:FB:E4": "Ubiquiti Networks",
    "F0:9F:C2": "Ubiquiti Networks",

    # Espressif / IoT (ESP32, ESP8266)
    "24:0A:C4": "Espressif Inc.",
    "24:62:AB": "Espressif Inc.",
    "30:AE:A4": "Espressif Inc.",
    "84:F3:EB": "Espressif Inc.",
    "A4:CF:12": "Espressif Inc.",
    "C4:4F:33": "Espressif Inc.",

    # Tuya Smart IoT
    "D8:1F:12": "Tuya Smart Inc.",
    "10:D5:61": "Tuya Smart Inc.",

    # Synology & QNAP NAS
    "00:11:32": "Synology Inc.",
    "00:08:9B": "QNAP Systems, Inc.",

    # Sony / PlayStation
    "00:04:1F": "Sony Corporation",
    "00:13:15": "Sony Interactive Entertainment",
    "70:9E:29": "Sony Interactive Entertainment",
    "F8:46:1C": "Sony Interactive Entertainment",

    # Nintendo
    "00:1F:32": "Nintendo Co., Ltd.",
    "34:AF:2C": "Nintendo Co., Ltd.",
    "70:48:0F": "Nintendo Co., Ltd.",
    "98:B6:E9": "Nintendo Co., Ltd.",

    # LG Electronics
    "00:1C:62": "LG Electronics",
    "10:F9:6F": "LG Electronics",
    "58:A2:B5": "LG Electronics",
    "CC:2D:8C": "LG Electronics",

    # Sonos
    "00:0E:58": "Sonos, Inc.",
    "5C:AA:FD": "Sonos, Inc.",
    "B8:E9:37": "Sonos, Inc.",

    # Virtualization (VirtualBox, VMware, QEMU)
    "08:00:27": "Oracle VirtualBox",
    "0A:00:27": "Oracle VirtualBox Host Adapter",
    "00:05:69": "VMware, Inc.",
    "00:0C:29": "VMware, Inc.",
    "00:50:56": "VMware, Inc."
}

def lookup_vendor(mac_address: str | None) -> str:
    """
    Given a MAC address (e.g., '3C:84:6A:12:34:56' or '3c-84-6a-12-34-56'),
    returns the manufacturer name or 'Generic Network Device'.
    """
    if not mac_address:
        return "Unknown"

    clean_mac = re.sub(r"[^0-9A-Fa-f]", "", mac_address).upper()
    if len(clean_mac) < 6:
        return "Unknown"

    prefix = f"{clean_mac[0:2]}:{clean_mac[2:4]}:{clean_mac[4:6]}"
    return OUI_DATABASE.get(prefix, "Generic Network Device")
