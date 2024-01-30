"""
This script works on a smart meter reading available from IEC at:
https://www.iec.co.il/login?returnPath=%2Fremote-reading-info
goes over the data and calculates the discount for different PLANS.

Usage:
    analyze_smart_meter_readings.py <csv_file> [--no-graph]

Options:
    -h           help, show this screen
    --no-graph   don't plot and display usage graphs
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from docopt import docopt

__version__ = '1.0.0'
__author__ = 'Amir Kiperwas'

# constants

KWH_PRICE_NIS = 0.48 * 1.17

PLANS = []
PLANS.append({'plan name': 'PazGaz flat discount', 'percent discount': 5, 'from weekday': 0, 'to weekday': 6,
              'from hour': '00:00', 'to hour': '23:59'})
PLANS.append({'plan name': 'PazGaz day discount', 'percent discount': 15, 'from weekday': 6, 'to weekday': 3,
              'from hour': '08:00', 'to hour': '15:59'})
PLANS.append({'plan name': 'PazGaz Weekend discount', 'percent discount': 10, 'from weekday': 4, 'to weekday': 5,
              'from hour': '00:00', 'to hour': '23:59'})
PLANS.append({'plan name': 'PazGaz Night discount', 'percent discount': 15, 'from weekday': 6, 'to weekday': 3,
              'from hour': '00:00', 'to hour': '06:59'})

PLANS.append({'plan name': 'Electra Power flat discount', 'percent discount': 7, 'from weekday': 0, 'to weekday': 6,
              'from hour': '00:00', 'to hour': '23:59'})
PLANS.append({'plan name': 'Electra Power Hi-Tec discount', 'percent discount': 10, 'from weekday': 0, 'to weekday': 6,
              'from hour': '23:00', 'to hour': '16:59'})
PLANS.append({'plan name': 'Electra Power Night discount', 'percent discount': 20, 'from weekday': 0, 'to weekday': 6,
              'from hour': '23:00', 'to hour': '6:59'})

PLANS.append({'plan name': 'Cellcom Nights discount', 'percent discount': 20, 'from weekday': 6, 'to weekday': 3,
              'from hour': '22:00', 'to hour': '06:59'})
PLANS.append(
    {'plan name': 'Cellcom Work from home discount', 'percent discount': 15, 'from weekday': 6, 'to weekday': 3,
     'from hour': '07:00', 'to hour': '16:59'})
PLANS.append({'plan name': 'Cellcom flat discount', 'percent discount': 7, 'from weekday': 0, 'to weekday': 6,
              'from hour': '00:00', 'to hour': '23:59'})

PLANS.append({'plan name': 'Amisragas flat discount', 'percent discount': 6.5, 'from weekday': 0, 'to weekday': 6,
              'from hour': '00:00', 'to hour': '23:59'})


def print_df(df_data):
    for ind in df_data.index:
        print(df_data['Interval starting date'][ind], df_data['day_of_week'][ind],
              df_data['Interval starting time'][ind],
              df_data['Consumption, kWh'][ind])


def map_days_of_week(df_data, col_name):
    df_data[col_name] = df_data[col_name].map({
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    })
    # display(df_data)
    df_data.head()
    return df_data


def get_meter_data_from_csv(csv_file_name):
    meter_data = pd.read_csv(csv_file_name, header=11)
    if "Interval starting" in (list(meter_data.columns.values)):
        meter_data[['Interval starting date', 'Interval starting time']] = meter_data['Interval starting'].str.split(
            ' ', expand=True)
    else:
        meter_data.columns = ['Interval starting date', 'Interval starting time', 'Consumption, kWh']
        meter_data[['Interval starting']] = str(meter_data['Interval starting date']) + ' ' + str(
            meter_data['Interval starting time'])

    meter_data['Interval starting date'] = pd.to_datetime(meter_data['Interval starting date'].astype(str),
                                                          format='%d/%m/%Y')
    meter_data['Interval starting time'] = pd.to_datetime(meter_data['Interval starting time'].astype(str),
                                                          format='%H:%M')
    meter_data['day_of_week'] = meter_data['Interval starting date'].dt.dayofweek
    return meter_data


def main():
    args = docopt(__doc__)
    args_str = str(args)
    args_str = args_str.replace('\n', '')
    csv_file_name = args['<csv_file>']
    no_graph_flag = args['--no-graph']
    data = get_meter_data_from_csv(csv_file_name)

    PLANS_df = pd.DataFrame(PLANS)
    PLANS_df = map_days_of_week(PLANS_df, 'from weekday')
    PLANS_df = map_days_of_week(PLANS_df, 'to weekday')
    print(PLANS_df.to_string())

    total_no_discount = data['Consumption, kWh'].sum() * KWH_PRICE_NIS

    print('Total without dicount: ', "{:.2f}".format(total_no_discount), ' NIS')
    results = []

    for plan in PLANS:
        plan_name = plan['plan name']
        if plan['from weekday'] <= plan['to weekday']:
            mask1 = (data['day_of_week'] >= plan['from weekday']) & (data['day_of_week'] <= plan['to weekday'])
        else:
            mask1 = (data['day_of_week'] >= plan['from weekday']) | (data['day_of_week'] <= plan['to weekday'])
        df = data.loc[mask1]
        df = df.set_index('Interval starting time')
        df = df.between_time(plan['from hour'], plan['to hour'])
        discounted = df['Consumption, kWh'].sum() * KWH_PRICE_NIS
        df = df.reset_index()
        new_total = total_no_discount - discounted * plan['percent discount'] / 100;
        saving_pecent = (discounted * plan['percent discount'] / 100 / total_no_discount) * 100;
        results.append(
            {'plan name': plan_name, 'total with discount': new_total, 'savings': total_no_discount - new_total,
             'savings %': saving_pecent})
        print(plan['plan name'], 'new total : %d NIS a saving of %.2f %%' % (new_total, saving_pecent))

    max_savings_plan = max(results, key=lambda x: x['savings'])
    print('\nBest plan for you: plan "', max_savings_plan['plan name'], '" would have saved you',
          "{:.2f}".format(max_savings_plan['savings']), ' NIS', 'which is',
          "{:.2f}".format(max_savings_plan['savings %']), '%')

    if not no_graph_flag:
        data_pivot = data.drop(['Interval starting', 'Interval starting date'], axis=1)
        data_pivot['Interval starting time'] = data_pivot['Interval starting time'].dt.strftime('%H:%M')
        data_pivot = map_days_of_week(data_pivot, 'day_of_week')
        #    data_pivot = pd.pivot_table(data, index='Interval starting time', values='Consumption, kWh', aggfunc='sum')
        data_pivot = pd.pivot_table(data_pivot, index='Interval starting time', values='Consumption, kWh',
                                    columns='day_of_week', aggfunc='sum')
        cols = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        data_pivot = data_pivot[cols]
        plt.figure(1)
        sns.heatmap(data_pivot, annot=True)
        plt.suptitle('Day of the week Consumption heat-map', fontsize=16)
        plt.show(block=False)

        data_pivot = data.drop(['Interval starting', 'day_of_week'], axis=1)
        data_pivot['Interval starting time'] = data_pivot['Interval starting time'].dt.strftime('%H:%M')
        data_pivot['Interval starting date'] = data_pivot['Interval starting date'].dt.strftime('%Y/%m/%d')
        data_pivot = pd.pivot_table(data_pivot, index='Interval starting time', values='Consumption, kWh',
                                    columns='Interval starting date', aggfunc='sum')
        plt.figure(2)
        sns.heatmap(data_pivot, annot=False)
        plt.suptitle('Daily Consumption heat-map', fontsize=16)
        plt.show(block=False)
        plt.pause(0.01)
        input("Press enter to continue...")
        plt.close()


if __name__ == "__main__":
    main()
