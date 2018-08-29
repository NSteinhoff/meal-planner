#/usr/bin/env python
"""usage: tdee_calculator.py FILE [OPTIONS]

Calculate Total Daily Energy Expenditure (TDEE).

Options:
    --weight                    Weight in kilograms
    --activity-level            sedentary | light | moderate | heavy | athelete
    --body-fat                  Body fat percentage
    -h, --help
"""
import sys


def print_help_and_exit(exit_code=0):
    """Print usage and exit."""
    print(__doc__)
    sys.exit(exit_code)


def parse_args(args):
    """Parse command line arguments."""
    try:
        opt_names = [o.lstrip('-') for o in args[:-1:2]]
        opt_values = args[1::2]
        parsed = dict(zip(opt_names, opt_values))
    except Exception as e:
        print(r"(╯°□°）╯︵ ┻━┻" + "\n")
        print("Error parsing arguments: %s\n%s\n\n" % (args, e))
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

    print("\n---", file=sys.stderr)
    print("Options: %s" % (args,), file=sys.stderr)
    print("---\n", file=sys.stderr)

    return parsed

def main(options):
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

    bmr = (370 + lean_body_mass * 21.6)
    tdee = bmr * activity_factor
    print("BMR of %.2f with %s activity." % (bmr, activity), file=sys.stderr)
    print("Your TDEE is estimated to be around:", file=sys.stderr)
    print("%.2f" % tdee)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print_help_and_exit(0)

    options = parse_args(args)

    try:
        main(options)
    except Exception as e:
        print("Error: %s %s\n" % (e.__class__.__name__, e), file=sys.stderr)
        print_help_and_exit(1)
