def compute_macd_diff_peak_and_limit(df_orig,
                                     take_profit=None,
                                     stop_loss=None,
                                     verbose=False,
                                     plot_chart=False):
    df = df_orig.copy()

    if take_profit and stop_loss:  # static values
        df['take_profit'] = take_profit
        df['stop_loss'] = stop_loss
    else:
        assert 'take_profit' in df and 'stop_loss' in df

    df['suggest'] = 'IDLE'
    df.loc[df['is_negative'] & df['is_upward'], 'suggest'] = 'BUY'

    df['limit'] = 0
    df.loc[df['suggest'] == 'BUY', 'limit'] = df['open'] * df['take_profit']

    df['stop'] = 0
    df.loc[df['suggest'] == 'BUY', 'stop'] = df['open'] * df['stop_loss']

    s = 'OUT'  # IN=invested, OUT=liquidated
    assets = 1
    limit = None
    stop = None

    assets_values = []
    actions = []
    results = []
    invest = []
    investment = None
    investment_when = None
    invest_when = []
    for index, row in df.iterrows():
        if s == 'IN':  # this depends on the previous state
            assets = assets / row['prev_open'] * row['open']
        if s == 'OUT' and row['suggest'] == 'BUY':
            s = 'IN'
            limit = row['limit']
            stop = row['stop']
            actions.append('BUY')
            assets = assets * (1 - FEES)
            investment = assets
            investment_when = row['ds']
            results.append(np.nan)
            invest.append(np.nan)
            invest_when.append(np.nan)
        elif s == 'IN' and (row['open'] * (1 - FEES) - limit >= 0 or row['open'] <= stop):
            s = 'OUT'
            limit = None
            stop = None
            actions.append('SELL')
            assets = assets * (1 - FEES)
            results.append('GAIN' if assets >= investment else 'LOSS')
            invest.append(investment)
            invest_when.append(investment_when)
        else:
            actions.append('----')
            results.append(np.nan)
            invest.append(np.nan)
            invest_when.append(np.nan)
        assets_values.append(assets)

    df['assets'] = assets_values
    df['action'] = actions
    df['result'] = results
    df['invest'] = invest
    df['invest-when'] = invest_when
    bnh = df['open'].iloc[-1] / df['open'].iloc[0]

    if verbose:
        display(df[:30])

    if plot_chart:
        df['buy-and-hold'] = df['open'] / df['open'].iloc[0]
        plot('line', df, ['assets', 'buy-and-hold'],
             title=f"{symbol} - {strategies[strategy]} take_profit={take_profit} stop_loss={stop_loss}")

    return assets, bnh, df

