#/usr/bin/env python
# -*- coding: utf-8 -*-
"""usage: tdee_calculator.py FILE [OPTIONS]

Calculate Total Daily Energy Expenditure (TDEE).

Options:
    --weight                    Weight in kilograms
    --activity-level            sedentary | light | moderate | heavy | athelete
    --body-fat                  Body fat percentage
    -h, --help
"""
import collections
import itertools
from itertools import islice, tee, accumulate
import os
import sys


KCAL_IN_KG = 7700


def print_help_and_exit(exit_code=0):
    """Print usage and exit."""
    print(__doc__)
    sys.exit(exit_code)


def _parse_options(opts):
    try:
        opt_names = [o.lstrip('-') for o in opts[:-1:2]]
        opt_values = opts[1::2]
        parsed = dict(zip(opt_names, opt_values))
    except Exception as e:
        print(r"(╯°□°）╯︵ ┻━┻" + "\n")
        print("Error parsing arguments: %s\n%s\n\n" % (opts, e))
        print_help_and_exit(1)

    valid = {'weight', 'activity-level', 'body-fat'}
    required = {'weight', 'activity-level', 'body-fat'}
    missing = {
        option for option in required
        if option not in parsed
    }
    invalid = {
        option for option in parsed
        if option not in valid
    }
    if missing:
        print("Missign options: %s" % missing)
        print_help_and_exit(1)
    if invalid:
        print("Invalid options: %s" % invalid)
        print_help_and_exit(1)
    return parsed


def parse_args(args):
    """Parse command line arguments."""
    fpath = args[0]
    if os.path.isfile(fpath):
        sys.stderr.write("\n---\n")
        sys.stderr.write("Data:%s\n" % (fpath,))
        sys.stderr.write("---\n\n")
        return fpath, None
    else:
        parsed = _parse_options(args)
        sys.stderr.write("\n---\n")
        sys.stderr.write("Options:%s\n" % (parsed,))
        sys.stderr.write("---\n\n")
        return None, parsed


def tdee_from_params(options):
    """Calculate TDEE base on input parameters."""
    activity_factors = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'heavy': 1.725,
        'athelete': 1.9,
    }

    activity = options['activity-level']
    activity_factor = activity_factors[activity]
    weight = float(options['weight']) 
    body_fat = float(options['body-fat'])
    lean_body_mass = weight * (1 - (body_fat / 100))

    bmr = 370 + lean_body_mass * 21.6
    tdee = bmr * activity_factor
    sys.stderr.write("BMR of %.2f with %s activity.\n" % (bmr, activity))
    sys.stderr.write("Your TDEE is estimated to be around:\n")
    print("%.2f" % tdee)
    sys.exit(0)


def tdee_from_data(fpath):
    data = list(load_data(fpath))
    lag_kcal = list(
        dict(now, kcal=yesterday['kcal'])
        for now, yesterday
        in zip(*(islice(d, lag, None) for d, lag
                 in zip(tee(data, 2), (1, 0))))
    )
    windows = zip(
        *(islice(d, i, None) for i, d
          in enumerate(tee(lag_kcal, 7)))
    )
    averages = (
        {
            'start': window[0]['date'],
            'end': window[-1]['date'],
            'kcal': sum([float(x['kcal']) for x in window]) / 7,
            'kg': sum([float(x['kg']) for x in window]) / 7,
        }
        for window in windows
    )

    with_previous = zip(
        *(islice(x, i, None) for x, i
          in zip(tee(averages, 2), (7, 0)))
    )

    deltas = (
        dict(now, delta=now['kg'] - previous['kg'])
        for now, previous in with_previous
    )
    with_surplus = (
        dict(x, surplus=x['delta'] * KCAL_IN_KG)
        for x in deltas
    )
    with_daily_surplus = (
        dict(x, daily_surplus=x['surplus'] / 7)
        for x in with_surplus
    )
    with_expended, with_expended_2 = tee((
        dict(x, expended=x['kcal'] - x['daily_surplus'])
        for x in with_daily_surplus
    ), 2)

    tdees = (
        expended / i for i, expended in 
        enumerate(accumulate(e['expended'] for e in with_expended_2), 1)
    )
    with_tdee = (
        dict(x, tdee=tdee) for x, tdee in zip(with_expended, tdees)
    )
    results = [(x['end'], x['tdee']) for x in with_tdee]
    for d, t in results:
        print("%s,%.2f" % (d,t))

    date, tdee = results[-1]
    sys.stderr.write("\nYour TDEE as of %s is estimated to be around: %.2f\n" % (date, tdee))


def load_data(fpath):
    """Load data from CSV file."""
    with open(fpath, 'r') as f:
        rows = [
            [f.strip() for f in l.strip().split(',')]
            for l in f
        ]
    fields = rows[0]
    data = rows[1:]
    return (dict(zip(fields, r)) for r in data)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print_help_and_exit(0)

    fpath, params = parse_args(args)

    if fpath:
        tdee_from_data(fpath)
    else:
        tdee_from_params(params)
