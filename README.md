[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/EvanGottschalk/ArrayOrderAutomator">
    <img src="images/logo.png" alt="Logo" width="250" height="130">
  </a>

  <h3 align="center">ArrayOrderAutomator</h3>

  <p align="center">
    A cryptocurrency trading bot that profits by creating and modifying groups of orders
    <br />
    <a href="https://github.com/EvanGottschalk/ArrayOrderAutomator"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/EvanGottschalk/ArrayOrderAutomator">View Demo</a>
    ·
    <a href="https://github.com/EvanGottschalk/ArrayOrderAutomator/issues">Report Bug</a>
    ·
    <a href="https://github.com/EvanGottschalk/ArrayOrderAutomator/issues">Request Feature</a>
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

`ArrayOrderAutomator` is a program I've been working towards (and working on) for some time. The idea for it first crossed my mind while trading cryptocurrency manually. Generally, one wants to buy or sell in a particular range, and not necessarily at an exact price. Buying or selling with a limit order at an exact price runs the risk of missing a better entry point, or missing the trade entirely. Instead, one would be better off creating a group of orders with consecutively increasing or decreasing sizes. This way, the odds that one gets into their trade are higher, and the odds that an even better price is missed is reduced.

This idea initially manifested itself as [`OperateExchangeGUI.py`](https://github.com/EvanGottschalk/OperateExchangeGUI), which allows users to create groups of array orders with customizable distributions of order volume and price. In testing it, I realized that a simple strategy of creating an Array Order on the buy side and a matching array order on the sell side would gradually net profits over time. It also sounded like a strategy that would be simple enough easily automate. And, thus, `ArrayOrderAutomator` was born.


### Built With

* `Python 3.6`

* `Pandas`

* [`CCXT`](https://github.com/ccxt/ccxt) - The fantastic `CCXT` library is critical to this program. Huge thanks to [@kroitor](https://github.com/kroitor) and the many other `CCXT` contributors that made this program possible.

* [`OperateExchange`](https://github.com/EvanGottschalk/OperateExchange) - This program is the brains behind `ArrayOrderAutomator`. The bot sends Array Order settings to `OperateExchange`, which then interprets them, checks them, and finally executes them via `ConnectToExchange`. You can read more about it here: [https://github.com/EvanGottschalk/OperateExchange](https://github.com/EvanGottschalk/OperateExchange)

* [`ConnectToExchange`](https://github.com/EvanGottschalk/connecttoexchange) - This program creates the initial connection to a cryptocurrency exchange. You can read more about it here: [github.com/EvanGottschalk/ConnectToExchange](https://github.com/EvanGottschalk/connecttoexchange)

* [`GetCurrentTime`](https://github.com/EvanGottschalk/GetCurrentTime) - This program is imported to help collect time data in a legible fashion. It also allows for the translation of time stamps. You can read more about it here: [github.com/EvanGottschalk/GetCurrentTime](https://github.com/EvanGottschalk/GetCurrentTime)

* [`AudioPlayer`](https://github.com/EvanGottschalk/AudioPlayer) - This is a simple program for playing custom audio alerts. It can be helpful as an alert in response to errors. You can read more about it here: [github.com/EvanGottschalk/AudioPlayer](https://github.com/EvanGottschalk/AudioPlayer)

* [`QuadraticFormula`](https://github.com/EvanGottschalk/OperateExchangeGUI/blob/main/QuadraticFormula.py) - This is a simple program for calculating the solutions to a quadratic equation using the quadratic formula.



<!-- GETTING STARTED -->
## Getting Started

`ArrayOrderAutomator` is easy to get up and running. Let [me](https://github.com/EvanGottschalk) know if you have any trouble! I'm always trying to make installation as smooth as possible.

### Prerequisites

Before using `ArrayOrderAutomator`, you must first obtain an API key and secret from the cryptocurrency exchange of their choosing. You also need to install the `Pandas` and [`CCXT`](https://github.com/ccxt/ccxt) libraries.

### Installation

EXAMPLE FROM OPERATEEXCHANGEGUI

1. Install [`CCXT`](https://github.com/ccxt/ccxt), and optionally `Pandas` and `Matplotlib` if you want to see data visualizations. The easiest way to do this to download `requirements.txt` and use `pip`:
    ```
    pip install -r requirements.txt
    ```

2. Download the `.py` files from this repository (`ArrayOrderAutomator.py`,`OperateExchange.py`, `ConnectToExchange.py`, `GetCurrentTime.py`, `QuadraticFormula.py`, and optionally `AudioPlayer.py`)

3. In the same folder as `ConnectToExchange.py`, create a `.txt` file to store your API information. Its name should start with the exchange you are using, followed by an underscore, followed by the name of the account you're using, and ending with `_API.txt`.

    For example, if you are using your **Main** account on **Coinbase**, you would name the `.txt` file **`Coinbase_Main_API.txt`**

    If your API key is `view-only`, you can save your cryptocurrency exchange API key on the 1st line, and your API secret on the 2nd. However, **if your API key has `trade` priveleges, you should save an encrypted version of both your key and secret on those lines instead.**

    To encrypt your API information, I recommend using `CustomEncryptor.py`, which can be downloaded here: [github.com/EvanGottschalk/CustomEncryptor](https://github.com/EvanGottschalk/CustomEncryptor)

4. Modify the automation settings in the `self.automationSettingsDict` dictionary in `ArrayOrderAutomator.py` to your liking.

5. Run `ArrayOrderAutomator.py`

6. Congratulations! You can now use `ArrayOrderAutomator` to automatically calculate, create and cancel Array Orders on your chosen cryptocurrency exchange!



<!-- USAGE EXAMPLES -->
## Usage

`ArrayOrderAutomator` will automatically create groups of buy and sell orders based on the chosen settings. After it's running, you don't need to do anything. The key is choosing settings that match your appetite for risk. Setting `Long Entry Spread` and `Short Entry Spread` to bigger values will make the bot behave more conservatively, profiting more effectively off of bigger price swings. Meanwhile, a larger `Long Entry Amount` or `Short Entry Amount` is always riskier, because that means the bot is trading with a larger sum.


<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/EvanGottschalk/ArrayOrderAutomator/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the GNU GPL-3 License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Evan Gottschalk - [@Fort1Evan](https://twitter.com/Fort1Evan) - evan@fort1e.com

Project Link: [https://github.com/EvanGottschalk/ArrayOrderAutomator](https://github.com/EvanGottschalk/ArrayOrderAutomator)



<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements

Thinking about contributing to this project? Please do! Your Github username will then appear here.





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/EvanGottschalk/ArrayOrderAutomator.svg?style=for-the-badge
[contributors-url]: https://github.com/EvanGottschalk/ArrayOrderAutomator/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/EvanGottschalk/ArrayOrderAutomator.svg?style=for-the-badge
[forks-url]: https://github.com/EvanGottschalk/ArrayOrderAutomator/network/members
[stars-shield]: https://img.shields.io/github/stars/EvanGottschalk/ArrayOrderAutomator.svg?style=for-the-badge
[stars-url]: https://github.com/EvanGottschalk/ArrayOrderAutomator/stargazers
[issues-shield]: https://img.shields.io/github/issues/EvanGottschalk/ArrayOrderAutomator.svg?style=for-the-badge
[issues-url]: https://github.com/EvanGottschalk/ArrayOrderAutomator/issues
[license-shield]: https://img.shields.io/github/license/EvanGottschalk/ArrayOrderAutomator.svg?style=for-the-badge
[license-url]: https://github.com/EvanGottschalk/ArrayOrderAutomator/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/EvanGottschalk
