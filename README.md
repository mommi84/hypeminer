# Hypeminer

![Bitcoin](https://github.com/mommi84/hypeminer/blob/main/img/20210318172600.png "Bitcoin")

## Usage

### Install

```bash
pip3 install -r requirements.txt
cd hypeminer
export PYTHONPATH=${PYTHONPATH}:`pwd`
```
### Run

Bash:

```bash
# process all tweets in files ./data/BTCUSDT/tweets/*.json
python3 core.py
```

Python:

```python
from hypeminer import Hypeminer

h = Hypeminer('store', currency='BTCUSDT')

# process tweets in file ./data/BTCUSDT/tweets/20210318021353.json
h.single_run_from_dump("20210318021353")

# downloads and processes 10 tweets from Twitter streaming APIs (warning: it will consume API calls)
h.single_run_from_stream(n_tweets=10)
```

## Links

### Data

* [Google Drive folder](https://drive.google.com/drive/u/0/folders/1v18cyN7WX_D2cuxC3eM12Po2mfevu7DE)

### Notebooks

* [Twitter Sentiment Analysis RoBERTa](https://colab.research.google.com/drive/1EqUIfb5ykD6iNIqyImEKeUxd8P8BlJgE)
* [Sequence Analysis](https://colab.research.google.com/drive/1L7A6AUI8UyOGFcqDQWbW70saCDwJHneA)
* [Multivariate Time Series Forecasting](https://colab.research.google.com/drive/1jetjuTXeaDe3g02QjfNnVVUwyX483Dxj)
