#!/usr/bin/env python3

"""
Yet Another Wi-Fi Diagnostic Tool gathers wireless diagnostics
and performs connectivity tests on macOS and Linux laptops.

The script's operating mode is defined by constants:
FACTS, TESTS, SETTINGS, DIAGNOSTICS, HIGHLIGHTS_TEMPLATE.

Those constants are assigned in set_constants() function.
The exact same function also exists in an external configuration file.
If you want to tweak the script, the recommended way is to put any changes to
the external configuration file. It will be loaded automatically
if you name it "config_yfitool.py" and put it in the same directory as the main script.
Or you can specify external config as an argument when starting the script:
"python3 yfitool.py my_external_config"

Only highlights are being sent to the output.
Make sure to check the FOLDER_NAME for a full report.
"""

import time
import subprocess
import re
import json
import logging
import importlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sys import argv

# Do not rename these constants - they are used for integration purposes

VERSION = "1.5.0"
FOLDER_NAME = '/var/tmp/yfi_reports'
DEFAULT_EXTERNAL_CONFIG_FILE = 'config_yfitool'

SUBPROCESS_TIMEOUT = 30
MAX_WORKERS = 5 # Number of threads to run simultaneously

# Here comes a long block of configuration constants assignment
# Those constants will be used by read_config() during the script initialization
# The best practice is not to change those constants here in "yfitool.py"
# Better apply all changes to external configuration file "config_yfitool.py"

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


# Below we define functions responsible for executing tests
# Available 'tasks' for constants['tests'] are:
# 'ping ping6 traceroute traceroute6 curl curl6 route route6'

### START DEFINING FUNCTIONS FOR EACH TASK IN constants['tests'] ###

def test_ping(task, target):
    # In case target is a gateway, we need to determine its address first
    if target == 'gw_placeholder' and task == 'ping':
        gateway_ipv4, _ = get_gateway()
        command_to_execute = f"{task} {SETTINGS['ping_arguments']} {gateway_ipv4}"
    elif target == 'gw_placeholder' and task == 'ping6':
        _, gateway_ipv6 = get_gateway()
        command_to_execute = f"{task} {SETTINGS['ping_arguments']} {gateway_ipv6}"
    else:
        command_to_execute = f"{task} {SETTINGS['ping_arguments']} {target}"

    test_result, test_output = run_subprocess(command_to_execute)
    if SETTINGS['good_ping_pattern'] not in test_output:
        test_result = "Not OK"

    return command_to_execute, test_result, test_output


def test_traceroute(task, target):
    command_to_execute = f"{task} {SETTINGS['traceroute_arguments']} {target}"

    test_result, test_output = run_subprocess(command_to_execute)
    return command_to_execute, test_result, test_output


def test_curl(task, target):
    if task == 'curl':
        command_to_execute = f"{SETTINGS['curl_ipv4_command']} http://{target}"
    elif task == 'curl6':
        command_to_execute = f"{SETTINGS['curl_ipv6_command']} http://{target}"
    test_result, test_output = run_subprocess(command_to_execute)
    return command_to_execute, test_result, test_output


def test_get_route(task, target):
    if task == 'route':
        command_to_execute = f"{SETTINGS['route_get_ipv4_command']} {target}"
    elif task == 'route6':
        command_to_execute = f"{SETTINGS['route_get_ipv6_command']} {target}"
    test_result, test_output = run_subprocess(command_to_execute)
    if test_result == 'OK':
        test_result = 'Saved to file'
    return command_to_execute, test_result, test_output

### STOP DEFINING FUNCTIONS FOR EACH TASK IN constants['tests'] ###


def get_gateway():
    gateway_ipv4 = "<IPv4 gateway not determined>"
    gateway_ipv6 = "<IPv6 gateway not determined>"

    _, test_output = run_subprocess(SETTINGS['get_gateway_ipv4_command'])
    match = re.search(SETTINGS['gateway_ipv4_regex'], test_output)
    if match:
        gateway_ipv4 = match.group(1)

    _, test_output = run_subprocess(SETTINGS['get_gateway_ipv6_command'])
    match = re.search(SETTINGS['gateway_ipv6_regex'], test_output)
    if match:
        gateway_ipv6 = match.group(1)

    return gateway_ipv4, gateway_ipv6


def run_subprocess(command_to_execute, subprocess_timeout=SUBPROCESS_TIMEOUT):
    try:
        logging.info(f"Starting subprocess: {command_to_execute}")
        process = subprocess.run(
            command_to_execute.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=subprocess_timeout,
            encoding='utf-8',
            check=False
        )

        if process.returncode == 0:
            test_result = "OK"
        else:
            test_result = "Not OK"

        test_output = process.stdout + process.stderr

    except FileNotFoundError:
        print(f"<{command_to_execute}> is not supported or resulted in error")
        test_result = "Error"
        test_output = "Error"
        logging.exception(f"<{command_to_execute}> is not supported or resulted in error")
    except subprocess.TimeoutExpired:
        test_result = f"Timeout expired ({subprocess_timeout} seconds)"
        test_output = f"Timeout expired ({subprocess_timeout} seconds)"
        logging.exception('')
    except subprocess.SubprocessError:
        test_result = "Error"
        test_output = "Error"
        logging.exception('')

    return test_result, test_output


def get_diagnostics(task, subfolder_name='.'):
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    filename = f"2_diag_{task['filename']}_{timestamp}.txt"
    command_to_execute = task['command']
    _, task_output = run_subprocess(command_to_execute)

    with open(f'{subfolder_name}/{filename}', 'w', encoding='utf-8') as file:
        for line in task_output:
            file.write(line)

    search_results = []
    for expression in task['expressions']:
        search_results.extend(re.findall(expression, task_output))
    search_results = ('\n'.join(search_results))

    diagnostic_results = {
        'command': command_to_execute,
        'major_facts': search_results
    }

    return diagnostic_results


def execute_test(test, subfolder_name='.'):
    test_results = {}

    for task in test['tasks'].split():
        # Each test has it's own timestamp
        timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
        filename = f"3_test_{test['filename']}_{task}_{timestamp}.txt"

        if 'ping' in task:
            executed_command, command_result, command_output = test_ping(
                task, test['target'])

        elif 'traceroute' in task:
            executed_command, command_result, command_output = test_traceroute(
                task, test['target'])

        elif 'curl' in task:
            executed_command, command_result, command_output = test_curl(
                task, test['target'])

        elif 'route' in task:
            executed_command, command_result, command_output = test_get_route(
                task, test['target'])

        with open(f"{subfolder_name}/{filename}", 'w', encoding='utf-8') as file:
            file.write(f"Executed command: {executed_command}\n\n")
            for line in command_output:
                file.write(line)

        test_results[task] = {
            'executed_command': executed_command,
            'result': command_result
        }

    return test_results


def parse_report(start_time, report, subfolder_name='.'):
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    filename_summary = f"0_summary_{timestamp}.txt"
    script_name = f"Yet Another Wi-Fi Diagnostic Tool v{VERSION}\n"
    summary = []
    highlights_from_summary = []

    highlights_from_summary.append("\n--- ")
    highlights_from_summary.append(f"\nStarted at: {start_time}")

    summary.append("\n====Diagnostics====")
    for task in report['diags']:
        summary.append("\n--- ")
        summary.append(f"\nTask: {task}")
        summary.append(f"\nCommand: {report['diags'][task]['command']}")
        if report['diags'][task]['major_facts']:
            summary.append(f"\n{report['diags'][task]['major_facts']}")

    summary.append("\n\n====Tests====")
    for test in report['tests']:
        summary.append("\n--- ")
        summary.append(f"\nTest: {test}")
        for task in report['tests'][test]:
            summary.append(f"\nCommand: {report['tests'][test][task]['executed_command']}")
            if report['tests'][test][task]['result']:
                summary.append(f"\n{report['tests'][test][task]['result']}")

    summary.append("\n\n====Tcpdump====\n")
    summary.append(f"Filter: {SETTINGS['tcpdump_output_filter']}\n")
    summary.append(report['tcpdump']['result'])

    # Prepare highlights from the summary
    for _, value in HIGHLIGHTS_TEMPLATE.items():
        piece_of_highlights = gather_highlights(summary, value)
        if piece_of_highlights:
            highlights_from_summary.append(f"\n{piece_of_highlights}")

    score, ok_count, total_count = calculate_score(
        summary,
        HIGHLIGHTS_TEMPLATE['ok']['expressions'],
        HIGHLIGHTS_TEMPLATE['not_ok']['expressions']
        )

    highlights_from_summary.append(f"\n\nYour score: {score}%")
    highlights_from_summary.append(f"\n{ok_count}/{total_count} tests passed")
    highlights_from_summary.append("\n--- \n")

    final_report = [script_name] + highlights_from_summary + summary
    human_friendly_report = "".join(final_report)
    highlights_to_print = "".join(highlights_from_summary)

    with open(f'{subfolder_name}/{filename_summary}', 'w', encoding='utf-8') as file:
        for line in final_report:
            file.write(line)

    parsed_report = {
        'summary': summary,
        'highlights_from_summary': highlights_from_summary,
        'human_friendly_report': human_friendly_report,
        'highlights_to_print': highlights_to_print
    }

    return parsed_report


def calculate_score(data, ok_template, not_ok_template):
    prepared_data = "".join(data)
    ok_results = len(re.findall(ok_template, prepared_data))
    not_ok_results = len(re.findall(not_ok_template, prepared_data))
    total_results = ok_results + not_ok_results
    if total_results == 0:
        score = "error in calculating "
    else:
        score = round(ok_results / total_results * 100)

    return score, ok_results, total_results


def gather_highlights(data, template):
    prepared_data = "".join(data)
    highlights = ""
    search_results = re.findall(template['expressions'], prepared_data)

    if template['id'] == 'ok':
        pass
    elif template['id'] == 'not_ok':
        if search_results:
            output = '\n'.join(search_results)
            highlights = (f"\n{template['description']}\n{output}")
    elif template['id'] == 'error':
        if search_results:
            output = '\n'.join(search_results)
            highlights = (f"\n{template['description']}\n{output}")
    # # You need sudo to get BSSID value using airport
    # elif template['id'] == 'bssid_from_airport':
    #     if search_results:
    #         output = ' '.join(search_results)
    #         highlights = (f"{template['description']} {output}")
    #     else:
    #         highlights = ("! Failed parsing BSSID from airport output")
    elif template['id'] == 'bssid_from_logs':
        if search_results:
            bssid = search_results[0]
            formatted_bssid = ':'.join(bssid[i:i+2] for i in range(0,12,2))
            highlights = (f"{template['description']} {formatted_bssid}")
        else:
            highlights = ("! Failed parsing BSSID from logs")
    elif template['id'] == 'ipv6_address':
        if search_results:
            output = ' '.join(search_results)
            highlights = (f"{template['description']} {output}")
        else:
            highlights = ("! No valid IPv6 address")
    elif template['id'] == 'ra_received':
        if "Tcpdump error" in prepared_data:
            highlights = ("! Tcpdump error - check logs")
        elif search_results:
            output = len(search_results)
            highlights = (f"RA messages received: {output}")
        else:
            highlights = ("! No RA messages captured")
    elif template['id'] == 'ssid':
        output = ' '.join(search_results)
        # Start from new line for better readability
        highlights = (f"\n{template['description']} {output}")
    elif template['id'] == 'computer_name':
        output = ' '.join(search_results)
        # Start from new line for better readability
        highlights = (f"\n{template['description']} {output}")
    else:
        output = ' '.join(search_results)
        highlights = (f"{template['description']} {output}")

    return highlights


def make_json(report, subfolder_name='.'):
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    filename_json = f"1_report_{timestamp}.json"
    with open(f'{subfolder_name}/{filename_json}', 'w', encoding='utf-8') as file:
        json.dump(report, file)


def markdownify_report(report, parsed_report, subfolder_name='.'):
    timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
    filename_wiki = f"1_markdown_{timestamp}.md"
    diagnostics = []
    tests = []
    tcpdump_output = []

    for task in report['diags']:
        diagnostics.append("\n\n---\n")
        diagnostics.append(f"\n**Task:** `{task}`</br>")
        diagnostics.append(f"\n**Command:** `{report['diags'][task]['command']}`</br>")
        if report['diags'][task]['major_facts']:
            diagnostics.append(f"\n```\n{report['diags'][task]['major_facts']}\n```")

    for test in report['tests']:
        tests.append("\n\n---\n")
        tests.append(f"\n**Test:** `{test}`</br>")
        for task in report['tests'][test]:
            tests.append(f"\n**Command:** `{report['tests'][test][task]['executed_command']}`</br>")
            if report['tests'][test][task]['result'] == 'Not OK':
                tests.append(f"\n```diff\n- {report['tests'][test][task]['result']}\n```")
            elif report['tests'][test][task]['result']:
                tests.append(f"\n```\n{report['tests'][test][task]['result']}\n```")

    tcpdump_output.append('\n')
    tcpdump_output.append(report['tcpdump']['result'])

    with open(f'{subfolder_name}/{filename_wiki}', 'w', encoding='utf-8') as file:

        file.write(f"#### Yet Another Wi-Fi Diagnostic Tool v{VERSION}\n")
        file.write("```")
        for line in parsed_report['highlights_from_summary']:
            file.write(line)
        file.write("```\n\n")
        file.write("<details>\n  <summary>Diagnostics</summary>\n")
        for line in diagnostics:
            file.write(line)
        file.write("\n</details>")

        file.write("<details>\n  <summary>Tests</summary>\n")
        for line in tests:
            file.write(line)
        file.write("\n</details>")

        file.write("<details>\n  <summary>Tcpdump</summary>\n")
        file.write(f"\n**Filter:** `{SETTINGS['tcpdump_output_filter']}`\n")
        file.write("\n```")
        for line in tcpdump_output:
            file.write(line)
        file.write("\n```")
        file.write("\n</details>")


def run_simultaneous_collection(dataset, subfolder_name='.'):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        if dataset == DIAGNOSTICS:
            future_list = [ex.submit(get_diagnostics, dataset[data], subfolder_name)
                           for data in dataset]
        elif dataset == TESTS:
            future_list = [ex.submit(execute_test, dataset[data], subfolder_name)
                           for data in dataset]

        # Make a new dictionary out of dataset keys and future collection results
        dataset_keys = list(dataset.keys())
        future_results = [future.result() for future in future_list]
        collection_report = dict(zip(dataset_keys, future_results))

    return collection_report


def make_archive(diag_name, subfolder_name='.'):
    # Add folder contents to archive so that it's easy to share
    archive_name = f'0_archive_{diag_name}.zip'
    try:
        zip_command = f'zip -rj {subfolder_name}/{archive_name} {subfolder_name}'
        logging.info(f"Create archive: {zip_command}")
        subprocess.run(
            zip_command.split(),
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        logging.exception("Error while creating the archive")


def check_capabilities(started_by, os_type):
    # EXTERNAL_CONFIG is True if there is a properly named external configuration file
    # within the main scripts directory
    if EXTERNAL_CONFIG:
        logging.info("External configuration file is being used")
        print("External configuration file is being used")

    print("Checking capabilities...\n")
    conflicts = {
        'check_os': {},
        'check_tcpdump': {},
        'check_root': {},
    }

    # Check if OS is supported
    if os_type not in FACTS['supported_systems']:
        conflicts['check_os']['conflict'] = True
        conflicts['check_os']['message'] = f"{os_type} is not supported yet"
        logging.warning(f"Trying to run script on unsupported system: {os_type}")

    # Check if it's possible to use tcpdump
    try:
        subprocess.run(
            SETTINGS['tcpdump_check_capabilities'].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            timeout=5,
            check=True
        )

    except subprocess.CalledProcessError as error:
        conflicts['check_tcpdump']['conflict'] = True
        conflicts['check_tcpdump']['message'] = "Unable to start tcpdump"
        logging.exception('check_capabilities: unable to start tcpdump')
        logging.error(f"check_capabilities: {error.stderr}")
    except subprocess.TimeoutExpired:
        conflicts['check_tcpdump']['conflict'] = True
        conflicts['check_tcpdump']['message'] = "Unable to get any data from interface with tcpdump"
        logging.exception('check_capabilities: tcpdump timeout expired, no frames captured')

    # Check if we have started the script with sudo
    if started_by != "root":
        logging.warning("The script is not started by root")
        conflicts['check_root']['conflict'] = True
        conflicts['check_root']['message'] = (
            "The script is not started by root - "
            "it will not collect some advanced diagnostics")

    # Report on all found conflicts
    conflicts_found = False
    for check in conflicts.values():
        if check:
            print(check['message'])
            conflicts_found = True
    if not conflicts_found:
        print("All script features are supported")

    return conflicts


def initialize_system(start_time):
    timestamp = start_time.strftime('%y%m%d_%H%M%S')

    # If you start the script with sudo, <started_by> == 'root' != <username>
    started_by = subprocess.check_output("whoami", encoding='utf-8').strip()
    username = subprocess.check_output("logname", encoding='utf-8').strip()

    # Running the script without sudo will not gather all available diagnostics
    # So, lets mark all non-sudo attempts as "basic_wifi_diag"
    if started_by == "root":
        diag_name = (f"{username}_wifi_diag_{timestamp}")
    else:
        diag_name = (f"{username}_basic_wifi_diag_{timestamp}")

    # Each time we run the script, create a timestamped subfolder inside the <FOLDER_NAME>
    subfolder_name = (f"{FOLDER_NAME}/{diag_name}")
    subprocess.run(f"mkdir {FOLDER_NAME}".split(), stderr=subprocess.DEVNULL, check=False)
    try:
        subprocess.run(f"mkdir {subfolder_name}".split(), check=True)
    except subprocess.CalledProcessError:
        print(f"Error while creating {subfolder_name}")
        exit()

    # Add logging to the file in the created subfolder
    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        filename=f"{subfolder_name}/1_logs_{timestamp}.log",
        level=logging.INFO
    )
    logging.info(f"Yet Another Wi-Fi Diagnostic Tool v{VERSION} started by {started_by}")

    # Make sure that <username> owns the folder even if the script started as root
    try:
        logging.info(f"Ensuring the correct ownership of {FOLDER_NAME}")
        subprocess.run(f"chown {username} {FOLDER_NAME}".split(), check=True)
    except subprocess.CalledProcessError:
        logging.exception('')

    # Check if the script is fully compilant with the system
    os_type = subprocess.check_output("uname", encoding='utf-8').strip().lower()
    conflicts = check_capabilities(started_by, os_type)

    print("---")
    print(f"\nYet Another Wi-Fi Diagnostic Tool v{VERSION}")
    print(f"Results will be saved to {subfolder_name}")

    return timestamp, diag_name, subfolder_name, conflicts


def tcpdump_start(subfolder_name, timestamp, conflicts):
    tcpdump_filename = f'{subfolder_name}/dump_{timestamp}.pcap'
    # Run tcpdump only in case no conflicts found at check_compatibility() stage
    if True in conflicts['check_tcpdump'].values():
        dump = None
        logging.error("Not starting tcpdump due to previously found conflicts")
        return dump, tcpdump_filename
    try:
        logging.info(f"Starting {SETTINGS['tcpdump_command']} {tcpdump_filename}")
        # With Popen tcpdump will run in background until dump.terminate()
        # dump.terminate() will be executed in tcpdump_finish()
        dump = subprocess.Popen(
            f"{SETTINGS['tcpdump_command']} {tcpdump_filename}".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8'
        )

        time.sleep(1) # required for .poll() to produce the correct value
        tcpdump_exit_code = dump.poll()
        if tcpdump_exit_code and tcpdump_exit_code > 0:
            subprocess_stderr = dump.communicate()[1]
            logging.error(f'tcpdump_start: {subprocess_stderr}')
            print("Error while starting tcpdump, check logs")

    except subprocess.SubprocessError:
        logging.exception('')

    return dump, tcpdump_filename


def tcpdump_finish(dump, tcpdump_filename, start_time, conflicts):
    # Run tcpdump only in case no conflicts found at check_compatibility() stage
    if True in conflicts['check_tcpdump'].values():
        tcpdump_report = {
            'executed_command': None,
            'read_command': None,
            'result': "Tcpdump error"
        }
        logging.error("Not reading tcpdump file due to previously found conflicts")
        return tcpdump_report

    # If needed, wait for tcpdump to finish its job
    end_time = datetime.now()
    execution_time = (end_time - start_time).seconds

    if execution_time < SETTINGS['tcpdump_timeout']:
        extra_timeout = SETTINGS['tcpdump_timeout'] - execution_time
        print(f"\nWaiting extra {extra_timeout} seconds for tcpdump to finish its job...")
        time.sleep(extra_timeout)

    # Try to terminate tcpdump
    try:
        logging.info("Trying to terminate tcpdump")
        dump.terminate()
        logging.info("Successfully terminated tcpdump")
    except subprocess.SubprocessError:
        logging.exception('')

    # Adding the delay helps to close the file correctly before further reading
    time.sleep(1)

    # Read the contents of .pcap using the filter from SETTINGS
    try:
        read_tcpdump_command = (
            f"tcpdump \'{SETTINGS['tcpdump_output_filter']}\' -n -r {tcpdump_filename}")
        logging.info(f"Reading the tcpdump file: {read_tcpdump_command}")
        tcpdump_reading = subprocess.run(
            read_tcpdump_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            shell=True,
            check=True
        )
        if tcpdump_reading.stdout:
            tcpdump_output = tcpdump_reading.stdout
        else:
            tcpdump_output = "No RA messages captured"
    except subprocess.CalledProcessError as error:
        logging.exception("tcpdump_finish: unable to read tcpdump file")
        logging.error(f"tcpdump_finish: {error.stderr}")
        tcpdump_output = "Error"

    tcpdump_report = {
        'executed_command': SETTINGS['tcpdump_command'],
        'read_command': read_tcpdump_command,
        'result': tcpdump_output
    }

    return tcpdump_report


def get_adapter_name(os_type):
    if os_type == 'darwin':
        adapter_name = 'en0'
    elif os_type == 'linux':
        expression = r'Interface (\S*)'
        iw_output = subprocess.check_output("iw dev".split(), encoding='utf-8').strip()
        adapter_name = re.findall(expression, iw_output)[0]
    else:
        adapter_name = 'unknown'

    return adapter_name


def read_config():
    os_type = subprocess.check_output("uname", encoding='utf-8').strip().lower()
    adapter_name = get_adapter_name(os_type)

    # Check if external config filename is passed as an argument
    if len(argv) > 1:
        external_config_file = argv[1].rstrip('.py')
    else:
        external_config_file = DEFAULT_EXTERNAL_CONFIG_FILE

    # Try to import external configuration file
    try:
        ext = importlib.import_module(external_config_file, package=None)
        constants = ext.set_constants(adapter_name)
        external_config = True

    # If there is no external configuration file - use built-in config
    except ModuleNotFoundError:
        print("No external configuration provided, using built-in defaults")
        external_config = False
        constants = set_constants(adapter_name)

    facts = constants['facts']['universal']
    tests = constants['tests']['universal']
    settings = constants['settings'][os_type]
    diagnostics = constants['diagnostics'][os_type]
    highlights_template = constants['highlights_template'][os_type]

    return facts, tests, settings, diagnostics, highlights_template, external_config


def main():
    report = {'conflicts': {}, 'diags': {}, 'tests': {}, 'tcpdump': ''}
    start_time = datetime.now()

    # Create folders, start logs, check capabilities, look for conflicts
    timestamp, diag_name, subfolder_name, conflicts = initialize_system(start_time)
    report['conflicts'] = conflicts

    # Start the tcpdump in background; will terminate after all other jobs finished
    dump, tcpdump_filename = tcpdump_start(subfolder_name, timestamp, conflicts)

    # Collect diagnostics with accordance to the DIAGNOSTICS template
    print("\nCollecting diagnostics...")
    report['diags'] = run_simultaneous_collection(DIAGNOSTICS, subfolder_name)

    # Perform tests with accordance to the TESTS template
    print("Performing tests...")
    report['tests'] = run_simultaneous_collection(TESTS, subfolder_name)

    # Terminate the tcpdump and parse the output .pcap file to form a report
    report['tcpdump'] = tcpdump_finish(dump, tcpdump_filename, start_time, conflicts)

    # Save the <report> as .json file
    make_json(report, subfolder_name)

    # Parse the <report> to return a human-readable summary, save it to a file
    # Print the most important highlights
    parsed_report = parse_report(start_time, report, subfolder_name)
    print(parsed_report['highlights_to_print'])
    human_friendly_report = parsed_report['human_friendly_report']

    # Generate a markdown-syntax report and save it to a file
    markdownify_report(report, parsed_report, subfolder_name)

    # Gather all files into one archive, so that it's easy to share
    make_archive(diag_name, subfolder_name)

    end_time = datetime.now()
    execution_time = (end_time - start_time).seconds
    print(f"Completed in {execution_time} seconds")
    print(f"Full logs saved to {subfolder_name}")

    return report, human_friendly_report


if __name__ == '__main__':
    FACTS, TESTS, SETTINGS, DIAGNOSTICS, HIGHLIGHTS_TEMPLATE, EXTERNAL_CONFIG = read_config()
    main()
