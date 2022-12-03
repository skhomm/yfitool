"""
This is the example of optional external configuration file.
Rename it to <config_yfitool.py> and yfitool will override
its default built-in configuration.

Try your best to apply changes only to external files
and not modify the main script.
"""


### START OF CONFIGURATION CONSTANTS ASSIGNMENT ###

def set_constants(adapter_name):
    # Constants keys could be 'universal', 'darwin' or 'linux'
    # The appropriate key will be automatically selected depending on your OS
    facts = {}
    tests = {}
    settings = {}
    diagnostics = {}
    highlights_template = {}

    facts['universal'] = {
        'supported_systems': ['darwin', 'linux']
    }

    # TESTS are constants used by execute_test() function
    # Available 'tasks': 'ping ping6 traceroute traceroute6 curl curl6 route route6'
    # '6' stands for IPv6-variant of the task
    # You may add or modify tests according to your needs

    tests['universal'] = {
        'google_dns': {
            'target': '8.8.8.8',
            'tasks': 'ping route',
            'filename': '8888'
        },
        'google_com': {
            'target': 'google.com',
            'tasks': 'ping ping6 curl curl6',
            'filename': 'googlecom'
        },
        'facebook': {
            'target': 'facebook.com',
            'tasks': 'ping ping6 curl curl6',
            'filename': 'facebook'
        },
        'youtube': {
            'target': 'youtube.com',
            'tasks': 'ping ping6 curl curl6',
            'filename': 'youtube'
        },
        'the_wlpc': {
            'target': 'thewlpc.com',
            'tasks': 'ping ping6 curl traceroute',
            'filename': 'wlpc'
        },
        # 'gateway' is treated in a special way, check test_ping()
        'gateway': {
            'target': 'gw_placeholder', # don't change 'gw_placeholder'
            'tasks': 'ping ping6',
            'filename': 'gateway'
        },
    }

    # General settings
    settings['darwin'] = {
        'ping_arguments': '-c 20',
        'good_ping_pattern': ' 0.0% packet loss',
        'traceroute_arguments': '-I',
        'route_get_ipv4_command': 'route -vn get',
        'route_get_ipv6_command': 'route -vn get -inet6',
        'curl_ipv4_command': 'curl -4Is',
        'curl_ipv6_command': 'curl -6Is',
        'get_gateway_ipv4_command': 'netstat -rn',
        'get_gateway_ipv6_command': 'netstat -rn',

        'gateway_ipv4_regex': rf'default +(\d+.\d+.\d+.\d+) +\S+ +{adapter_name}',
        'gateway_ipv6_regex': rf'default +(\S+:\S+) + +\S+ +{adapter_name}',

        'tcpdump_command': f'tcpdump -i {adapter_name} -W 1 -G 90 -w',
        'tcpdump_check_capabilities': f'tcpdump -i {adapter_name} -c 1',
        'tcpdump_timeout': 30,
        'tcpdump_output_filter': 'icmp6 && ip6[40] == 134',

        'throughput_command': 'networkQuality',
    }

    settings['linux'] = {
        'ping_arguments': '-c 20',
        'good_ping_pattern': ' 0% packet loss',
        'traceroute_arguments': '-I',
        'route_get_ipv4_command': 'ip route get',
        'route_get_ipv6_command': 'ip -6 route get',
        'curl_ipv4_command': 'curl -4Is',
        'curl_ipv6_command': 'curl -6Is',
        'get_gateway_ipv4_command': 'ip -4 route list',
        'get_gateway_ipv6_command': 'ip -6 route list',

        'gateway_ipv4_regex': r'default via (\S+)',
        'gateway_ipv6_regex': r'default via (\S+)',

        'tcpdump_command': f'tcpdump -i {adapter_name} -W 1 -G 90 -w',
        'tcpdump_check_capabilities': f'tcpdump -i {adapter_name} -c 1',
        'tcpdump_timeout': 30,
        'tcpdump_output_filter': 'icmp6 && ip6[40] == 134',

        'throughput_command': None, # Not supported yet
    }

    # DIAGNOSTICS are constants used by get_diagnostics() function
    diagnostics['darwin'] = {
        'log_show': {
            'command': 'log show --info --debug --last 5m',
            'filename': 'log_show',
            'expressions': []
        },
        'ifconfig': {
            'command': f'ifconfig {adapter_name}',
            'filename': 'ifconfig',
            'expressions': [
                r'ether \S+',
                r'inet6 .+',
                r'inet .+',
            ]
        },
        'public_ip': {
            'command': 'curl -s ifconfig.me',
            'filename': 'public_ip',
            'expressions': [
                r'\S+',
            ]
        },
        'gateway_ipv4': {
            'command': 'route get default',
            'filename': 'gateway4',
            'expressions': [
                r'gateway: \S+',
            ]
        },
        'gateway_ipv6': {
            'command': 'route -n get -inet6 default',
            'filename': 'gateway6',
            'expressions': [
                r'gateway: \S+',
            ]
        },
        'netstat': {
            'command': 'netstat -rn',
            'filename': 'netstat',
            'expressions': [
                r'default.+en\d+',
            ]
        },
        'system_profiler': {
            'command': (
                'system_profiler '
                'SPAirPortDataType SPHardwareDataType SPSoftwareDataType SPLogsDataType'),
            'filename': 'system_profiler',
            'expressions': [
                r'Computer Name: .+',
                r'User Name: .+',
                r'System Version: .+',
                r'Time since boot: .+',
                r'Card Type: .+',
                r'Firmware Version: .+',
                r'Supported Channels: .+',
                r'Supported PHY Modes: .+',
                r'Current Network Information:[\s\S]*MCS Index: \d+',
                r'"IO80211BSSID.+',
            ]
        },
        'airport': {
            'command': (
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/'
                'airport -Is'),
            'filename': 'airport',
            'expressions': [
                r'[\s\S]*',
            ]
        },
        'known_networks': {
            'command': f'networksetup -listpreferredwirelessnetworks {adapter_name}',
            'filename': 'known_networks',
            'expressions': [
                r'	(\S+)',
            ]
        },
        'wdutil': {
            'command': 'wdutil info',
            'filename': 'wdutil',
            'expressions': []
        },
    }

    diagnostics['linux'] = {
        'journalctl': {
            'command': 'journalctl -S -10m',
            'filename': 'log_journalctl',
            'expressions': []
        },
        'ip_addr': {
            'command': f'ip addr show {adapter_name}',
            'filename': 'ip_addr',
            'expressions': [
                r'ether \S+',
                r'inet6 .+',
                r'inet .+',
            ]
        },
        'public_ip': {
            'command': 'curl -s ifconfig.me',
            'filename': 'public_ip',
            'expressions': [
                r'\S+',
            ]
        },
        'gateway_ipv4': {
            'command': f'ip -4 route list type unicast dev {adapter_name}',
            'filename': 'gateway4',
            'expressions': [
                r'default via \S+',
            ]
        },
        'gateway_ipv6': {
            'command': f'ip -6 route list type unicast dev {adapter_name}',
            'filename': 'gateway6',
            'expressions': [
                r'default via \S+',
            ]
        },
        'ip_route_table': {
            'command': 'ip route show table all',
            'filename': 'ip_route_table',
            'expressions': [
                r'default via \S+ dev \S+',
            ]
        },
        'user_login': {
            'command': 'id',
            'filename': 'user_login',
            'expressions': [
                r'uid=\S+',
            ]
        },
        'boot_time': {
            'command': 'who -b',
            'filename': 'boot_time',
            'expressions': [
                r'system boot.+'
            ]
        },
        'iw_dev': {
            'command': 'iw dev',
            'filename': 'iw_dev',
            'expressions': [
                r'ssid \S+',
                r'channel .+',
            ]
        },
        'iwconfig': {
            'command': f'iwconfig {adapter_name}',
            'filename': 'iwconfig',
            'expressions': [
                r'Access Point: \S+',
                r'Link Quality=\S+',
                r'Signal level=\S+ dBm',
            ]
        },
        'supported_channels': {
            'command': f'iwlist {adapter_name} channel',
            'filename': 'supported_channels',
            'expressions': []
        },
        'hostnamectl': {
            'command': 'hostnamectl',
            'filename': 'hostnamectl',
            'expressions': [
                r'Static hostname: \S+',
                r'Operating System: .*',
                r'Kernel: .*',
                r'Architecture: \S+',
                r'Hardware Vendor: .*',
                r'Hardware Model: .*',
            ]
        },
        'adapter_info': {
            'command': f'nmcli -f GENERAL dev show {adapter_name}',
            'filename': 'adapter_info',
            'expressions': [
                r'DEVICE:.+',
                r'VENDOR:.+',
                r'PRODUCT:.+',
                r'DRIVER:.+',
                r'DRIVER-VERSION:.+',
            ]
        },
        'wifi_list': {
            'command': 'nmcli device wifi list',
            'filename': 'wifi_list',
            'expressions': []
        },
    }

    # Template for gathering the most important info from the summary
    # Highlights will be presented in the same order they go in this dictionary
    highlights_template['darwin'] = {
        'username': {
            'id': 'username',
            'expressions': r'User Name: (.+)',
            'description': 'Started by:',
        },
        'mac_address': {
            'id': 'mac_address',
            'expressions': r'ether (\S+)',
            'description': 'MAC address:',
        },
        'ipv4_address': {
            'id': 'ipv4_address',
            'expressions': r'inet (\S+) netmask',
            'description': 'IPv4 address:',
        },
        'ipv6_address': {
            'id': 'ipv6_address',
            'expressions': r'inet6 (\S+:[0-9a-f]*) ',
            'description': 'IPv6 address:',
        },
        'ra_received': {
            'id': 'ra_received',
            'expressions': r'ff02::1: ICMP6, router advertisement',
            'description': 'RA messages received:',
        },
        'dl_throughput': {
            'id': 'dl_throughput',
            'expressions': r'Download capacity: (\S+ \S+)',
            'description': 'DL throughput:',
        },
        'ul_throughput': {
            'id': 'ul_throughput',
            'expressions': r'Upload capacity: (\S+ \S+)',
            'description': 'UL throughput:',
        },
        'ssid': {
            'id': 'ssid',
            'expressions': r' SSID: (\S+)',
            'description': 'SSID:',
        },
        # # You need sudo to get BSSID value from airport
        # 'bssid_from_airport': {
        #     'id': 'bssid_from_airport',
        #     'expressions': r'BSSID: (\S+:\S+:\S+:\S+:\S+)\n.*SSID',
        #     'description': 'BSSID from airport:',
        # },
        'bssid_from_logs': {
            'id': 'bssid_from_logs',
            'expressions': r'"IO80211BSSID" = <(\S+)>',
            'description': 'BSSID:',
        },
        'rssi': {
            'id': 'rssi',
            'expressions': r'Signal / Noise: (\S+ dBm)',
            'description': 'RSSI:',
        },
        'noise': {
            'id': 'noise',
            'expressions': r'Signal / Noise: .+ / (\S+ dBm)',
            'description': 'Noise:',
        },
        'channel': {
            'id': 'channel',
            'expressions': r'Channel: (\d+)',
            'description': 'Channel:',
        },
        'computer_name': {
            'id': 'computer_name',
            'expressions': r'Computer Name: (.+)',
            'description': 'Computer Name:',
        },
        'macos_version': {
            'id': 'macos_version',
            'expressions': r'System Version: (.+)',
            'description': 'System Version:',
        },
        'time_since_boot': {
            'id': 'time_since_boot',
            'expressions': r'Time since boot: (.+)',
            'description': 'Time since boot:',
        },
        'ok': {
            'id': 'ok',
            'expressions': r'Command: (.*)\nOK',
            'description': 'OK:',
        },
        'not_ok': {
            'id': 'not_ok',
            'expressions': r'Command: (.*)\nNot OK',
            'description': 'Not OK:',
        },
        'error': {
            'id': 'error',
            'expressions': r'Command: (.*)\nError',
            'description': 'Error:',
        },
    }

    highlights_template['linux'] = {
        'mac_address': {
            'id': 'mac_address',
            'expressions': r'ether (\S+)',
            'description': 'MAC address:',
        },
        'ipv4_address': {
            'id': 'ipv4_address',
            'expressions': r'inet (\S+)/.{,2} brd',
            'description': 'IPv4 address:',
        },
        'ipv6_address': {
            'id': 'ipv6_address',
            'expressions': r'inet6 (\S+:[0-9a-f]*)(?=/.{,2})',
            'description': 'IPv6 address:',
        },
        'ra_received': {
            'id': 'ra_received',
            'expressions': r'ip6-allnodes: ICMP6, router advertisement',
            'description': 'RA messages received:',
        },
        # Throughput test for linux is not yet supported
        # So next two entries are just placeholders
        'dl_throughput': {
            'id': 'dl_throughput',
            'expressions': r'Non existing pattern placeholder: (\S+ \S+)',
            'description': 'DL throughput:',
        },
        'ul_throughput': {
            'id': 'ul_throughput',
            'expressions': r'Non existing pattern placeholder: (\S+ \S+)',
            'description': 'UL throughput:',
        },
        'ssid': {
            'id': 'ssid',
            'expressions': r'ssid (\S+)',
            'description': 'SSID:',
        },
        'bssid': {
            'id': 'bssid',
            'expressions': r'Access Point: (\S+)',
            'description': 'BSSID:',
        },
        'signal_level': {
            'id': 'signal_level',
            'expressions': r'Signal level=(\S+) dBm',
            'description': 'Signal level:',
        },
        'link_quality': {
            'id': 'link_quality',
            'expressions': r'Link Quality=(\S+)',
            'description': 'Link Quality:',
        },
        'channel': {
            'id': 'channel',
            'expressions': r'channel (.+)',
            'description': 'Channel:',
        },
        'computer_name': {
            'id': 'computer_name',
            'expressions': r'Static hostname: (\S+)',
            'description': 'Computer Name:',
        },
        'user_login': {
            'id': 'user_login',
            'expressions': r'uid=\d+\((\S+)\)',
            'description': 'Login:',
        },
        'boot_time': {
            'id': 'boot_time',
            'expressions': r'system boot + (.*)',
            'description': 'Boot time:'
        },
        'os_version': {
            'id': 'os_version',
            'expressions': r'Operating System: (.*)',
            'description': 'OS version:',
        },
        'kernel': {
            'id': 'kernel',
            'expressions': r'Kernel: (.*)',
            'description': 'Kernel:',
        },
        'hardware_name': {
            'id': 'hardware_name',
            'expressions': r'Hardware Vendor: (.*)',
            'description': 'Hardware vendor:',
        },
        'hardware_model': {
            'id': 'hardware_model',
            'expressions': r'Hardware Model: (.*)',
            'description': 'Hardware model:',
        },
        'adapter_vendor': {
            'id': 'adapter_vendor',
            'expressions': r'VENDOR: + (.*)',
            'description': 'Adapter vendor:',
        },
        'adapter_model': {
            'id': 'adapter_model',
            'expressions': r'PRODUCT: + (.*)',
            'description': 'Adapter model:',
        },
        'adapter_driver': {
            'id': 'adapter_diver',
            'expressions': r'DRIVER: + (.*)',
            'description': 'Adapter driver:',
        },
        'ok': {
            'id': 'ok',
            'expressions': r'Command: (.*)\nOK',
            'description': 'OK:',
        },
        'not_ok': {
            'id': 'not_ok',
            'expressions': r'Command: (.*)\nNot OK',
            'description': 'Not OK:',
        },
        'error': {
            'id': 'error',
            'expressions': r'Command: (.*)\nError',
            'description': 'Error:',
        },
    }

    constants = {
        'facts': facts,
        'tests': tests,
        'settings': settings,
        'diagnostics': diagnostics,
        'highlights_template': highlights_template
    }

    return constants

### END OF CONFIGURATION CONSTANTS ASSIGNMENT ###
