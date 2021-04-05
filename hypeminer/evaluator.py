#!/usr/bin/env python
import numpy as np
import pandas as pd


def compute_rmse(predictions_tsv, reference_tsv, samples_limit=None):

	pred = pd.read_csv(predictions_tsv, sep='\t')
	ref = pd.read_csv(reference_tsv, sep='\t')

	first_pred = pred['timestamp'].iloc[0]
	print("first_pred =", first_pred)
	index = ref.index[ref['timestamp'] == first_pred].tolist()[0]

	pred_values = pred['currency']
	ref_values = ref['currency'].iloc[index:]

	difference = []
	for p, r in zip(pred_values, ref_values):
		difference.append(p - r)
	if samples_limit:
		difference = difference[:samples_limit]
	print("Evaluating on {} datapoints.".format(len(difference)))

	se = np.square(np.array(difference))
	rmse = np.sqrt(np.mean(se))
	print('RMSE = {:.2f}'.format(rmse))

	return rmse

if __name__ == '__main__':

	limit = 36 # 4 days

	compute_rmse("data/BTCBUSD/predictions/store-20210308235900.tsv", "data/BTCBUSD/datasets/store-indices.tsv", samples_limit=limit)
