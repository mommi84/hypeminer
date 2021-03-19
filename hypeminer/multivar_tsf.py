#!/usr/bin/env python
import pandas as pd
from fbprophet import Prophet
from matplotlib import pyplot as plt


plt.rcParams["figure.figsize"] = (15, 4)


def build_figure(dfp_train, forecast):
	plt.clf()
	past = list(dfp_train['y'])
	fut = list(forecast['yhat'])[len(past):]
	print('yhat:', fut)
	complete = [None] * (len(past)-1) + fut
	plt.plot(past, 'b', label='btcusd')
	plt.plot(complete, 'r', label='forecast')

	plt.legend(loc="upper left")
	plt.grid(True)

	# plt.plot(prev + list(forecast['yhat_upper']), 'r--', label='forecast upper')
	# plt.plot(prev + list(forecast['yhat']), 'r', label='forecast')
	# plt.plot(prev + list(forecast['yhat_lower']), 'r--', label='forecast lower')
	return plt


class MultivariateTSF(object):

	"""MultivariateTSF object."""
	def __init__(self, currency, forecast_days, target, regressors, yearly_seasonality=False):
		self.currency = currency
		self.forecast_days = forecast_days
		self.target = target
		self.regressors = regressors
		self.yearly_seasonality = yearly_seasonality

	def estimate_regressor(self, columns, r0, dfp):
		to_drop = ['y']
		for r in self.regressors:
			if r != r0:
				to_drop.append(columns[r])
		print(to_drop)
		df_r = pd.DataFrame(dfp).drop(columns=to_drop)
		df_r['y'] = df_r[columns[r0]]
		df_r = df_r.drop(columns=columns[r0])
		print(df_r)
		model_r = Prophet(yearly_seasonality=self.yearly_seasonality)
		model_r.fit(df_r)
		future_r = model_r.make_future_dataframe(freq='H', periods=self.forecast_days)
		print("FUTURE_R")
		print(future_r)
		forecast_r = model_r.predict(future_r)
		values_r = list(dfp[columns[r0]])
		values_r += list(forecast_r['yhat'].tail(self.forecast_days))
		print(values_r)
		return values_r

	def run(self, store_id, safe_timestamp):

		model = Prophet(yearly_seasonality=self.yearly_seasonality)

		df = pd.read_csv("data/{}/indices/{}.tsv".format(self.currency, store_id), sep='\t')

		dfp = pd.DataFrame()

		columns = {'timestamp': 'ds', self.target: 'y'}
		for i, r in enumerate(self.regressors):
			r_name = 'add' + str(i + 1)
			columns[r] = r_name
			model.add_regressor(r_name)

		for src, tgt in columns.items():
			dfp[tgt] = df[src]

		print(dfp)
 
		model.fit(pd.DataFrame(dfp))

		future = model.make_future_dataframe(freq='H', periods=self.forecast_days)
		# unknown = [0.5 for i in range(len(future['ds']))]
		for r in self.regressors:
			future[columns[r]] = self.estimate_regressor(columns, r, dfp)
			# future[columns[r]] = unknown

		print(future)

		forecast = model.predict(future)

		# fig = model.plot(forecast)
		fig = build_figure(dfp, forecast)
		fig.savefig("data/{}/plots/{}-{}.png".format(self.currency, store_id, safe_timestamp))


if __name__ == '__main__':
	currency = "BTCUSDT"
	safe_timestamp = "20210309024000" # "20210318132039"
	forecast_days = 4
	target = 'currency'
	regressors = ['score', 'negative']

	multivar = MultivariateTSF(currency, forecast_days, target, regressors)
	multivar.run('store', safe_timestamp)
