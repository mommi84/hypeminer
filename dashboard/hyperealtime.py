#!/usr/bin/env python
from flask import Flask
import json
import matplotlib
matplotlib.use('Agg')
from hypecommons import *
import sys

CRYPTO = sys.argv[1]
FIAT = sys.argv[2]
# MACD_INF = int(sys.argv[3])
# MACD_SUP = int(sys.argv[4])
# TRADER_START = sys.argv[5]

def get_js_clock():
    return '''
        <script>
            function get_data(file, fun) {
              var xhttp = new XMLHttpRequest();
              xhttp.onreadystatechange = fun;
              xhttp.open("GET", file, true);
              xhttp.send();
            }
            const zeropad = (num, places) => String(num).padStart(places, "0");
            function clock() {
                var today = new Date();
                var time = today.getHours() + ":" + zeropad(today.getMinutes(), 2) + ":" + zeropad(today.getSeconds(), 2);
                document.getElementById("current-time").innerHTML = time;
            }
            function get_charts() {
                get_data("/charts", function() {
                    if (this.readyState == 4 && this.status == 200) {
                        document.getElementById("price_chart").src = "/static/price_chart.png?" + new Date().getTime();
                        document.getElementById("macd_histo").src = "/static/macd_histo.png?" + new Date().getTime(); 
                    }
                });
            }
            function get_orders() {
                get_data("/orders", function() {
                    if (this.readyState == 4 && this.status == 200) {
                        document.getElementById("orders").innerHTML = this.responseText;
                    }
                });
            }
            var t_sec = setInterval(clock, 1000);
            var t_min = setInterval(update_page, 60000);
            function update_page() {
                get_orders();
                get_charts();
            }
        </script>
     '''

def load_data(crypto, fiat):
    df = pd.read_csv(f"../hypetrader/trader_{crypto}{fiat}.tsv", parse_dates=['ds'], sep='\t')
    df.set_index('ds', inplace=True)
    df['action'] = df['decision']
    return df

def get_orders(crypto, fiat):
    df = load_data(crypto, fiat)
    return df[(df['action'] == 'BUY') | (df['action'] == 'SELL')][['close', 'macd_histo_norm', 'action']].to_html().replace('<table border="1" class="dataframe">', '<table class="table">')

def update_charts(crypto, fiat):
    # load parameters from trader
    df = load_data(crypto, fiat)
    trader_start = df[['decision']].dropna().index[0] # UTC time
    freq = int((df.index[-1] - df.index[-2]).total_seconds() / 60.0)
    macd_thr = [df['macd_thr_a'].iloc[-1], df['macd_thr_b'].iloc[-1]]
    close_trader_start = df[df.index == trader_start]['close']
    df_chart = df.iloc[-100:].copy()
    print((trader_start, close_trader_start))
    output_chart(df_chart, f"{crypto}{fiat}", freq, save='static/price_chart.png', fig_size=(15,6), show=True, start_data=(trader_start, close_trader_start))
    plt.clf()
    df_chart['buy_signal'] = df_chart['macd_thr_a']
    df_chart['sell_signal'] = df_chart['macd_thr_b']
    plot(plt.plot, df_chart, ['buy_signal', 'sell_signal'], colours=['b', 'b'], linestyles=['--', '--'], clf=True)
    plot(plt.bar, df_chart, ['macd_histo_norm'], ['g'], bar_size=.04 * freq / len(df_chart), fig_size=(15,3), clf=False)
    plt.savefig('static/macd_histo.png')
    
    return "Done."

def render(crypto, fiat):
#     # TODO: load parameters from trader (add columns)
    
    return f"""<!DOCTYPE html>
        <head>
            <title>Hypetrader</title>
            <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css' rel='stylesheet' integrity='sha384-+0n0xVW2eSR5OomGNYDnhzAbDsOXxcvSN1TPprVMTNDbiYZCxYbOOl7+AMvyTG2x' crossorigin='anonymous'>
            <link rel="icon" type="image/png" href="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/google/274/currency-exchange_1f4b1.png">
        </head>
        <body onload="update_page();">
        <nav class="navbar navbar-light bg-light text-center" style="display: inherit;">
  <div class="container-fluid text-center" style="display: inherit;">
    <a class="navbar-brand" href="#" style="font-size: 1.8em !important;">
      <img src="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/240/google/274/currency-exchange_1f4b1.png" alt="" width="40" height="36" class="d-inline-block align-text-top">
      Hypetrader
    </a>
  </div>
</nav>
            <div style='width: 1100px; float: left;'>
                <img id='price_chart' width='1000'><br><img id='macd_histo' width='1000'>
            </div>
            <div style='float: left;'>
                <div class='shadow rounded' align='center' style='width: 400px; margin: 40px; padding-left: 40px; padding-right: 40px;'><h1 class="display-1" id='current-time'>{get_js_clock()}</h1></div>
                <div align='center' style='margin: 40px;'><img src='/static/symbols/{crypto}.png' style='-webkit-filter: drop-shadow(0px 5px 10px #cccccc); filter: drop-shadow(0px 5px 10px #cccccc);'></div>
                <div><h2>Orders</h2><div id='orders'></div></div>
            </div>
        </body>
    </html>"""


app = Flask(__name__, static_url_path='/static')

@app.route('/charts')
def charts():
    """Update charts."""
    return update_charts(CRYPTO, FIAT)

@app.route('/orders')
def orders():
    """Show orders."""
    return get_orders(CRYPTO, FIAT)

@app.route('/')
def root():
    """Show trader."""
    return render(CRYPTO, FIAT)

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080, debug=True)
        
