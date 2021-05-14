#!/usr/bin/env python
from hypetrader import macddiffpnl
from hypetrader import stockperceptron


def do_nothing(state):
    pass


class State(object):
    def __getattr__(self, name):
        return None



STRATEGY_PLANNING = {
    'MACDDiffAdaptivePeakAndLimit': {
        'init': macddiffpnl.optimise_parameters,
        'daily': do_nothing,
        'hourly': do_nothing,
        'periodically': macddiffpnl.macddpnl_periodically,
        'after_buying': do_nothing,
        'after_selling': macddiffpnl.optimise_parameters,
        'output_cols': ['ds', 'open', 'suggest', 'limit', 'decision'],
    },
    'StockPerceptron': {
        'init': stockperceptron.initialise,
        'daily': do_nothing,
        'hourly': do_nothing,
        'periodically': stockperceptron.act,
        'after_buying': do_nothing,
        'after_selling': do_nothing,
        'output_cols': ['ds', 'open'],
    },
}
