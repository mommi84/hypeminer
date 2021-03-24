#!/usr/bin/env python
import pandas as pd


def regress(df_in, df_out, column, window):

	for i in range(window):
		df_out[column + '_t-' + str(i)] = df_in[column].shift(periods=i)


def create_sklearn_dataset(currency, store_id, window, regressors, save_to_csv=False):

	df = pd.read_csv("data/{}/samples/{}.tsv".format(currency, store_id), sep='\t')

	df_final = pd.DataFrame()

	df['currency'] = df['currency'].diff()

	regress(df, df_final, 'currency', window)

	for r in regressors:
		regress(df, df_final, r, window)

	data = df_final.tail(-window)

	data.to_csv("data/{}/datasets/{}-window{}.tsv".format(currency, store_id, window), sep='\t', index=False)

	return data



if __name__ == '__main__':
	data = create_sklearn_dataset('BTCUSDT', 'store', 5, ['score', 'negative'], save_to_csv=True)
	print(data)
