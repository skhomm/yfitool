<!-- ABOUT THE PROJECT -->
## About The Project
### yfitool [waɪfaɪ tuːl]
**Yet Another Wi-Fi Diagnostic Tool** gathers wireless diagnostics and performs connectivity tests on macOS and Linux laptops. It generates an admin-friendly report useful for troubleshooting Wi-Fi issues. No need to collect diagnostic data manually anymore.

> :warning: **Do not share the report with untrusted entities - it contains sensitive information like system logs or a list of known networks**

The tool is highly customizable, feel free to adapt it to your environment.

Default Python3 is the only requirement to run the tool. Apple laptops with macOS are fully supported. As for Linux - it's tested on Ubuntu, but it will probably run on your distro too. Or won't.

Feel free to contribute!

<!-- GETTING STARTED -->
## Getting Started

The idea was to keep it simple. Just clone the repo and run `yfitool.py`.
Or you may receive `yfitool.py` by email. Or by flash drive. Just get it somehow and run with python3.

### Prerequisites

Python 3.6 or higher is required. No external modules are needed.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/skhomm/yfitool
   ```
2. Switch to the yfitool directory
   ```sh
   cd yfitool
   ```

<!-- USAGE EXAMPLES -->
## Usage

Just run the tool
```sh
python3 yfitool.py
```

Actually, running the tool with `sudo` will collect some additional diagnostics. And you may need it if superuser privileges are required to run tcpdump on your system. Anyway, the script will gather basic diagnostics even without `sudo`. But it's better with.
```sh
sudo python3 yfitool.py
```

The tool will run for a minute or two. It will generate report in `/var/tmp/yfi_reports/`. The report consists of:
- 0_archive_username_timestamp.zip
- 0_summary_username_timestamp.txt
- 1_logs_timestamp.log
- 1_markdown_timestamp.md
- 1_report_timestamp.json
- 2_diag_*.txt
- 3_test_*.txt
- dump_timestamp.pcap

`0_archive_username_timestamp.zip` is just the same folder with all collected files compressed for your convenience. Just send it to your system administrator if you don't care. 

If you do care, start with `0_summary_username_timestamp.txt`. It's a human-friendly report containing all diagnostics and test results.
If you want more - continue examing other files. They have all answers.
The dump is here for you too. If tcpdump was able to start.

You may also provide an external configuration file to the tool. Check the repo for example file: `config_yfitool_example.py`.
To use an external config simply specify its name as an argument:
```sh
python3 yfitool.py my_external_config
```

If you want to use an external config file by default - rename it to `config_yfitool.py`
If the file with such a name is in the same directory as `yfitool.py`, it will be used automatically.

<!-- HOW DOES IT WORK -->
## How does it work

In general, the tool works the following way:
- It determines OS version and adapter name
- It reads the configuration (external file or built-in)
- It starts tcpdump and runs it until the finish
- It gathers diagnostics and runs tests (using multithreading), saves the results to files
- It generates a human-friendly report

<details>
  <summary>Simplified block diagram</summary>
  Disclaimer.
  It is indeed simplified. And probably outdated. Many details omitted. You've been warned.

  ```mermaid
    graph TD;
        A["<h3>Get configuration from external file or built-in defaults, determine wireless adapter name</h3> read_config(), get_adapter_name(), set_constants()"]
        B["<h3>Create folders, enable logging, check capabilities</h3> initialize_system(), check_capabilities()"]
        C["<h3>Start tcpdump to capture everything while script works</h3> tcpdump_start()"]
        D["<h3>Get diagnostics according to DIAGNOSTICS dict, save results to report['diags'] and files</h3> run_simultaneous_collection(), get_diagnostics()"]
        E["<h3>Execute tests according to TESTS dict, save results to report['tests'] and files</h3> run_simultaneous_collection(), execute_test()"]
        F["<h3>Stop tcpdump, save pcap, read pcap applying filter, save results to report['tcpdump']</h3> tcpdump_finish()"]
        G["<h3>Parse report, calculate score, print highlights, save summary and .json to files</h3> parse_report(), calculate_score(), gather_highlights(), make_json()"]
        H["<h3>Make archive to simplify sharing</h3> make_archive()"]

        A-->B-->C-->D-->E-->F-->G-->H;
  ```
</details>

<!-- HOW TO ADD CUSTOM TEST TARGETS -->
## How to add custom test targets
Add a block like this to the `tests['universal']` dict:
```py
'mytest_name': {
   'target': 'mytestresource.com',
   'tasks': 'ping ping6 curl curl6',
   'filename': 'mytestresource'
},
```
Available 'tasks': 'ping ping6 traceroute traceroute6 curl curl6 route route6'

'6' stands for IPv6-variant of the task

<!-- ROADMAP -->
## Roadmap

- [ ] Add some kind of a speedtest (networkQuality for macOS)
- [ ] Improve score calculation (now it's too straightforward)
- [ ] Improve Linux support
- [ ] Security audit
- [ ] Refactoring
- [ ] Classes?
- [ ] Regression testing?
- [ ] Windows support?
- [ ] GUI version?

<!-- FAQ -->
## FAQ
#### It's 1000+ lines of code. Why not to move some parts to the separate modules?
> The tool should be fully functional even if it's only the yfitool.py available. Makes it much easier to distribute the tool. Just send the yfitool.py via email or messenger. No need for complicated instructions.

#### Will there be a version for Windows?
> Probably. Feel free to contribute!

#### Are you professional developer?
> No. That's why the code could be not so elegant. But I did my best to make it at least readable. Feel free to share your enhancement ideas.

#### Do you have access to the reports or any other personal data?
> No. The tool works locally on a laptop and do not send anything anywhere. Check the code.

<!-- CONTRIBUTING -->
## Contributing

You are welcome to contribute!

Please fork the repo and create a pull request. You can also simply open an issue. Check CONTRIBUTING.md for more details.

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<!-- CONTACT -->
## Contact
Leonid Tekanov - [@LTekanov](https://twitter.com/LTekanov)

Project Link: [https://github.com/skhomm/yfitool](https://github.com/skhomm/yfitool)

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Thanks to [Yandex](https://yandex.com/company/) for allowing me to publish the tool as an open-source project. And for the tasks that inspired me to develop it in the first place.
* Thanks to [@savamoti](https://github.com/Savamoti) and [@akims0n](https://github.com/akims0n) for help with adapting the tool for Linux.
* Thanks to Wi-Fi professional community all over the world for constant support and motivation.
* Special thanks to [@lytboris](https://github.com/lytboris).

