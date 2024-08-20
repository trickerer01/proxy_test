# proxy test
Find and / or test multiple proxies for target website and more

##### Python 3.7 or greater required
- Cmdline tool, there is no GUI
- See `requirements.txt` for additional dependencies. Install with:
  - `python -m pip install -r requirements.txt`
- Invoke `python px_main.py --help` to list possible arguments
- For bug reports, questions and feature requests use our [issue tracker](https://github.com/trickerer01/proxy_test/issues)

#### Examples
- Simply find valid proxies for a single web address
  - `python px_main.py --target <ADDRESS>`
- Find a big set of valid proxies for a single web address
  - `python px_main.py --target <ADDRESS> --proxy 4`
- Test a specific proxy against a single web address:
  - `python px_main.py --target <ADDRESS> --proxy <ADDRESS:PORT>`
- Test a range of proxies against random web addresses in range
  - `python px_main.py --target https://example.com/1#2001-3000#/ --proxy socks5://127.0.0.#1-255#:3128`
- Test all proxies listed within a text file against random web addresses listed within a second text file, test up to 50 proxies simultaneously, save results to a specific folder
  - `python px_main.py --target <FILEPATH> --proxy <FILEPATH> --pool-size 50 --dest <DIRPATH>`
- File format is uniform - every address or range is separed by a newline, range size is limited to `1000`, the only difference is proxy type can be either `http` or `socks5` and web address can be either `http` or `https`:
- ```text
  http://example.com/
  http://example.com/1/
  http://example.com/#200-299#/
  https://8.8.8.8/
  http://1.1.1.#1-255#/
  socks5://2.2.2.#2-5#:#8080-8888#
  ```
