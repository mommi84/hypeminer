#!/usr/bin/env python
import pandas as pd
from fbprophet import Prophet
from matplotlib import pyplot as plt

from hypeminer import utilities


MIN_DATAPOINTS = 250

plt.rcParams["figure.figsize"] = (15, 4)


class MultivariateTSF(object):

    """MultivariateTSF object."""
    def __init__(self, currency, forecast_hours, target, regressors, yearly_seasonality=False):
        self.currency = currency
        self.forecast_hours = forecast_hours
        self.target = target
        self.regressors = regressors
        self.yearly_seasonality = yearly_seasonality

    def estimate_regressor(self, columns, r0, dfp, store_id, safe_timestamp):
        to_drop = ['y']
        for r in self.regressors:
            if r != r0:
                to_drop.append(columns[r])
        df_r = pd.DataFrame(dfp).drop(columns=to_drop)
        df_r['y'] = df_r[columns[r0]]
        df_r = df_r.drop(columns=columns[r0])
        model_r = Prophet(yearly_seasonality=self.yearly_seasonality)
        with utilities.suppress_stdout_stderr():
            model_r.fit(df_r)
        future_r = model_r.make_future_dataframe(freq='H', periods=self.forecast_hours)
        forecast_r = model_r.predict(future_r)
        values_r = list(dfp[columns[r0]])
        values_r += list(forecast_r['yhat'].tail(self.forecast_hours))
        fig_r = model_r.plot(forecast_r)
        fig_r.savefig("data/{}/plots/{}-{}-{}.png".format(self.currency, store_id, r0, safe_timestamp))
        return values_r

    def run(self, store_id, safe_timestamp):

        model = Prophet(yearly_seasonality=self.yearly_seasonality)

        df = pd.read_csv("data/{}/indices/{}.tsv".format(self.currency, store_id), sep='\t')

        if len(df) < MIN_DATAPOINTS:
            print("Not enough datapoints for forecast. Skipping...")
            return

        dfp = pd.DataFrame()

        columns = {'timestamp': 'ds', self.target: 'y'}
        for i, r in enumerate(self.regressors):
            r_name = 'add' + str(i + 1)
            columns[r] = r_name
            model.add_regressor(r_name)

        for src, tgt in columns.items():
            dfp[tgt] = df[src]

        with utilities.suppress_stdout_stderr():
            model.fit(dfp)

        future = model.make_future_dataframe(freq='H', periods=self.forecast_hours)
        r_forecast = []
        for r in self.regressors:
            future[columns[r]] = self.estimate_regressor(columns, r, dfp, store_id, safe_timestamp)
            r_forecast.append(list(future[columns[r]]))

        forecast = model.predict(future)

        # plot whole series including forecast
        fig = model.plot(forecast)
        fig.savefig("data/{}/plots/{}-{}.png".format(self.currency, store_id, safe_timestamp))

        # plot trend line
        plt.clf()
        plt.plot(forecast['ds'], forecast['trend'])
        plt.savefig("data/{}/plots/{}-trend-{}.png".format(self.currency, store_id, safe_timestamp))

        # output predictions
        df_predictions = forecast.tail(self.forecast_hours)
        print(df_predictions)

        arr_forecast = []
        for (index, row), r_predictions in zip(df_predictions.iterrows(), zip(*r_forecast)):

            timestamp = str(row['ds'])
            yhat = row['yhat']

            arr_forecast.append({
                "predictedAt": utilities.to_epoch(safe_timestamp, is_safe=True),
                "predictedFor": utilities.to_epoch(timestamp, is_safe=False),
                "price": yhat,
                "priceDelta": None,
            })

        for i in range(len(arr_forecast)):
            old_price = forecast['yhat'].iloc[-self.forecast_hours-1] if i == 0 else arr_forecast[i-1]['price']
            arr_forecast[i]['priceDelta'] = arr_forecast[i]['price'] - old_price

        with open("data/{}/predictions/{}-{}.tsv".format(self.currency, store_id, safe_timestamp), 'w') as f_out:
            
            r_string = '\t'.join(self.regressors)
            f_out.write("timestamp\tcurrency\tdelta\t{}\n".format(r_string))

            for (index, row), r_predictions, elem_forecast in zip(df_predictions.iterrows(), zip(*r_forecast), arr_forecast):

                timestamp = str(row['ds'])

                r_string = '\t'.join([str(x) for x in r_predictions])
                f_out.write("{}\t{}\t{}\t{}\n".format(timestamp, elem_forecast['price'], elem_forecast['priceDelta'], r_string))

        predictions = { "forecast": arr_forecast }
        return predictions


if __name__ == '__main__':
    currency = "BTCUSDT"
    safe_timestamp = "20210317115500"
    forecast_hours = 96
    target = 'currency'
    regressors = ['score', 'negative']

    multivar = MultivariateTSF(currency, forecast_hours, target, regressors)
    predictions = multivar.run('store', safe_timestamp)
    
    print("First 5 predictions:", predictions['forecast'][:5])
    utilities.save_to_json("api-example.json", predictions)
