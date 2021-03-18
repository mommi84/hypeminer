#!/usr/bin/env python
import pandas as pd
from fbprophet import Prophet


class MultivariateTSF(object):

	"""MultivariateTSF object."""
	def __init__(self, currency, forecast_days, target, regressors, yearly_seasonality=False):
		self.currency = currency
		self.forecast_days = forecast_days
		self.target = target
		self.regressors = regressors
		self.yearly_seasonality = yearly_seasonality

	def run(self, store_id, safe_timestamp):

		self.m = Prophet(yearly_seasonality=self.yearly_seasonality)

		df = pd.read_csv("data/{}/indices/{}.tsv".format(self.currency, store_id), sep='\t')

		dfp = pd.DataFrame()

		columns = {'timestamp': 'ds', self.target: 'y'}
		for i, r in enumerate(self.regressors):
			r_name = 'add' + str(i + 1)
			columns[r] = r_name
			self.m.add_regressor(r_name)

		for src, tgt in columns.items():
			dfp[tgt] = df[src]

		print(dfp)
 
		self.m.fit(dfp)

		future = self.m.make_future_dataframe(periods=self.forecast_days)
		unknown = [0 for i in range(len(future['ds']))]
		for r in self.regressors:
			future[columns[r]] = unknown

		forecast = self.m.predict(future)
		fig = self.m.plot(forecast)

		fig.savefig("data/{}/plots/{}-{}.png".format(self.currency, store_id, safe_timestamp))


if __name__ == '__main__':
	currency = "BTCUSDT"
	safe_timestamp = "20210318132039"
	forecast_days = 4
	target = 'currency'
	regressors = ['score', 'negative']

	multivar = MultivariateTSF(currency, forecast_days, target, regressors)
	multivar.run('test', safe_timestamp)
