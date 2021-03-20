#!/usr/bin/env python
import pandas as pd
from fbprophet import Prophet
from matplotlib import pyplot as plt


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

	def estimate_regressor(self, columns, r0, dfp):
		to_drop = ['y']
		for r in self.regressors:
			if r != r0:
				to_drop.append(columns[r])
		df_r = pd.DataFrame(dfp).drop(columns=to_drop)
		df_r['y'] = df_r[columns[r0]]
		df_r = df_r.drop(columns=columns[r0])
		model_r = Prophet(yearly_seasonality=self.yearly_seasonality)
		model_r.fit(df_r)
		future_r = model_r.make_future_dataframe(freq='H', periods=self.forecast_hours)
		forecast_r = model_r.predict(future_r)
		values_r = list(dfp[columns[r0]])
		values_r += list(forecast_r['yhat'].tail(self.forecast_hours))
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

		print(dfp)
 
		model.fit(dfp)

		future = model.make_future_dataframe(freq='H', periods=self.forecast_hours)
		for r in self.regressors:
			future[columns[r]] = self.estimate_regressor(columns, r, dfp)

		print(future)

		forecast = model.predict(future)

		fig = model.plot(forecast)
		fig.savefig("data/{}/plots/{}-{}.png".format(self.currency, store_id, safe_timestamp))


if __name__ == '__main__':
	currency = "BTCUSDT"
	safe_timestamp = "20210309024000"
	forecast_hours = 144
	target = 'currency'
	regressors = ['score', 'negative']

	multivar = MultivariateTSF(currency, forecast_hours, target, regressors)
	multivar.run('store', safe_timestamp)
