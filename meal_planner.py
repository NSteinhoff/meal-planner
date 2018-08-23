"""Create meal plans."""
import itertools
import sys
import json


PRECISION = 2
MAX_MEALS = 5
MAX_RESULTS = 10


def rnd(v, precision=PRECISION):
    """Round to the default precision."""
    return round(v, precision)


def load_data(fpath):
    """Load data from CSV file."""
    with open(fpath, 'r') as f:
        fields, *data = [
            [f.strip() for f in l.strip().split(',')]
            for l in f
        ]
        return [dict(zip(fields, r)) for r in data]


def calories(p, c, f):
    """Calculate calories from macros."""
    return p * 4 + f * 9 + c * 4


def clean(records, name='name', protein='protein', fat='fat', carbs='carbs'):
    """Add derived data to records"""
    def _clean(r):
        p, c, f = map(float, [r[protein], r[carbs], r[fat]])
        return {
            'name': r[name],
            'kcal': rnd(calories(p, c, f)),
            'p': rnd(p),
            'f': rnd(f),
            'c': rnd(c)
        }

    return [_clean(r) for r in records]


def combine(records):
    """Create all possible combinations"""
    cmbs = (
        list(itertools.combinations(records, l))
        for l in range(1, len(records))
    )
    return (c for cs in cmbs for c in cs)


def totals(meals):
    """Get the total macros and other statistics of the
    meal plan."""
    macros = {
        "p": rnd(sum(m['p'] for m in meals)),
        "f": rnd(sum(m['f'] for m in meals)),
        "c": rnd(sum(m['c'] for m in meals)),
    }
    kcal = calories(**macros)

    return {
        "kcal": kcal,
        "pi": rnd(macros['p'] * 4 / kcal),
        "meals": [m['name'] for m in meals],
        "kcal %": [rnd(m['kcal'] / kcal) for m in meals],
        "details": list(meals),
        **macros
    }


def print_help_and_exit(exit_code=0):
    """Print usage and exit."""
    opt_fmt = "  {:<20} {}"
    opt_help = "\n".join(
        opt_fmt.format(*opt) for opt in [
            ('-n', "Maximum number of meals in plan (default=5)."),
            ('-kcal', "Calories (kcal) MIN[:MAX]"),
            ('-p', "Protein (g) MIN[:MAX]"),
            ('-c', "Carbs (g) MIN[:MAX]"),
            ('-f', "Fat (g) MIN[:MAX]"),
            ('-pi', "Fraction of calories from protein MIN[:MAX]"),
            ('-results', "Maximum number of plans to produce (default=10)."),
            ('-h, --help', "Show this message and exit."),
        ]
    )
    msg = (
        "\nusage: meal_planner.py [OPTIONS] FILE\n"
        "\nCreate meal plans from recipes in CSV formatted file \n"
        "and print a JSON array with the results to stdout.\n"
        "\nExample recipe file contents:\n\n"
        "    name     , protein, carbs,  fat\n"
        "    meal-one ,    50.5,  10.6, 25.2\n"
        "    meal-two ,    42.3,    11, 15.3\n"
        "\nThe ranges for options take a minimum and an\n"
        "optional maximum value separated by ':'.\n"
        "\nExamples:\n"
        "  -c 50:100 -> between 50 and 100 grams of carbs\n"
        "  -f 75 -> minimum of 75 grams of fat\n"
        "\nOptions:\n"
    ) + opt_help

    print(msg)
    sys.exit(exit_code)


def parse_args(args):
    """Parse command line arguments."""
    try:
        fname = args[-1]
        opts = args[:-1]
        parsed = dict(zip(opts[:-1:2], opts[1::2]))
    except Exception as e:
        print(f"Error parsing arguments:\n{args}\n{e}")
        print_help_and_exit(1)

    print("\n---", file=sys.stderr)
    print(f"Options: {opts}", file=sys.stderr)
    print(f"Data: {fname}", file=sys.stderr)
    print("---\n", file=sys.stderr)

    return fname, parsed


def predicates(options):
    """Create predicates from the supplied options."""
    def range_checker(key, rng):
        """Predicate for checking if value under key is in range."""
        if len(rng) == 1:
            return lambda x: x[key] >= rng[0]
        else:
            return lambda x: x[key] >= rng[0] and x[key] <= rng[1]

    sanitized = {
        k.lstrip('-'): tuple(map(float, v.split(':')))
        for k, v in options.items()
        if k not in {"-n", "-results"}
    }
    max_meals = [
        lambda x: len(x['meals']) <= int(options.get('-n', MAX_MEALS))
    ]
    macro_ranges = [range_checker(k, v) for k, v in sanitized.items()]
    return max_meals + macro_ranges


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print_help_and_exit(0)
    fname, options = parse_args(args)
    criteria = predicates(options)
    print("Creating awesome meal plans:\n", file=sys.stderr)

    records = load_data(fname)
    cleaned = clean(records)
    combined = combine(cleaned)
    plans = (totals(c) for c in combined)

    matches = (
        plan for plan in plans
        if all(p(plan) for p in criteria)
    )
    n_results = int(options.get('-results', MAX_RESULTS))
    results = list(itertools.islice(matches, n_results))

    print(json.dumps(results, indent=4))
