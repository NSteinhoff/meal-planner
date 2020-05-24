#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create meal plans.

usage: meal_planner.py RECIPE_FILE [OPTIONS]

Create meal plans from recipes in CSV formatted file
and print a JSON array with the results to stdout.

Example recipe file contents:

    name     , protein, carbs,  fat
    meal-one ,    50.5,  10.6, 25.2
    meal-two ,    42.3,    11, 15.3

The ranges for options take optional minimum and
maximum values separated by ':'.

Examples:
  -c 50:100 -> between 50 and 100 grams of carbs
  -f 75 or 75:-> minimum of 75 grams of fat
  -f :95 -> maximum of 95 grams of fat

Options:
  -n                   Number of meals MIN:MAX (default=3:5).
  -kcal                Calories (kcal) MIN:MAX
  -p                   Protein (g) MIN:MAX
  -c                   Carbs (g) MIN:MAX
  -f                   Fat (g) MIN:MAX
  -pi                  Fraction of calories from protein MIN:MAX
  --max-results        Maximum number of plans to produce (default=10).
  --timeout            Timeout in seconds, when no matching plan can be found.
  -h, --help           Show this message and exit.
"""
import itertools
import json
import os
import sys
import time

# TODO: "mainstays" -> meals that should be part of every plan
# TODO: smarter combination generation

PRECISION = 2
MEALS = "3:5"
MAX_RESULTS = 10
TIMEOUT = 1
(MIN_MEALS, MAX_MEALS) = (1, 10)


def timer():
    """Return the time since the first iteration.

    Yields:
        int: The time in seconds since the first iteration.
    """
    start = time.time()
    while True:
        yield time.time() - start


def timeout(iterable, timeout):
    """Timeout the iteration of an iterable.

    Args:
        iterable: An iterable
        timeout (int): Seconds after which the iteration should timeout.

    Yields:
        Elements from the provided iterable.
    """
    timed = zip(iterable, timer())
    for e, t in timed:
        yield e
        if t >= timeout:
            break


def print_help_and_exit(exit_code=0):
    """Print usage and exit.

    Args:
        exit_code (int): The code with which to exit.
    """
    print(__doc__)
    sys.exit(exit_code)


def parse_args(args):
    """Parse command line arguments.

    Args:
        args (list): Command line arguments.

    Returns:
        tuple (str, dict): The file path and a dictionary of options.

    Raises:
        FileNotFoundError: The file name provided does not exist.
    """
    try:
        fpath = args[0]
        if not os.path.isfile(fpath):
            raise FileNotFoundError("Unknown file: %s." % fpath)
        opts = args[1:]
        opt_names = [o.lstrip("-") for o in opts[:-1:2]]
        opt_values = opts[1::2]
        parsed = dict(zip(opt_names, opt_values))
    except Exception as e:
        print(r"(╯°□°）╯︵ ┻━┻" + "\n")
        print("Error parsing arguments: %s\n%s\n\n" % (args, e))
        print_help_and_exit(1)

    sys.stderr.write("\n---\n")
    sys.stderr.write("Options: %s\n" % (parsed,))
    sys.stderr.write("Data:%s\n" % (fpath,))
    sys.stderr.write("---\n\n")

    return fpath, parsed


def load_data(fpath):
    """Load data from CSV file."""
    with open(fpath, "r") as file:
        rows = [[field.strip() for field in line.strip().split(",")] for line in file]
    header = rows[0]
    data = rows[1:]
    return (dict(zip(header, row)) for row in data)


def clean(records):
    """Add derived data to records."""

    def derive(r):
        p, c, f = map(float, [r["protein"], r["carbs"], r["fat"]])
        count = int(r.get("count", "") or "1")
        return {
            "name": r["name"],
            "kcal": rnd(calories(p, c, f)),
            "p": rnd(p),
            "f": rnd(f),
            "c": rnd(c),
            "count": count,
        }

    return map(derive, records)


def combine(records, n):
    """Create all possible combinations."""
    recs = list(sorted(records, key=lambda x: x["kcal"], reverse=True))
    # Intersperse high with low calorie foods, allow for more diverse
    # combinations to occurr earlier.
    desc = recs[::2]
    asc = recs[1::2][::-1]
    interspersed = itertools.chain.from_iterable(zip(desc, asc))

    mults = list(itertools.chain.from_iterable([r] * r["count"] for r in interspersed))

    cmbs = (itertools.combinations(mults, l) for l in range(*n))
    return (c for cs in cmbs for c in cs)


def totals(meals):
    """Get the total macros and other statistics of the meal plan."""
    macros = {k: rnd(sum(m[k] for m in meals)) for k in {"p", "f", "c"}}
    kcal = calories(**macros)

    return {
        "kcal": kcal,
        "pi": rnd(macros["p"] * 4 / kcal),
        "meals": [m["name"] for m in meals],
        "kcal %": [rnd(m["kcal"] / kcal) for m in meals],
        "details": list(meals),
        **macros,
    }


def assemble(combinations):
    """Assemble plans from sequences of meals."""
    return (totals(c) for c in combinations)


def rnd(v, precision=PRECISION):
    """Round to the default precision."""
    return round(v, precision)


def calories(p, c, f):
    """Calculate calories from macros."""
    return p * 4 + f * 9 + c * 4


class Range:
    """Numeric range."""

    def __init__(self, start=None, stop=None):
        """Initialize a new range."""
        self.start = start
        self.stop = stop

    def __repr__(self):
        """Return repr."""
        return "Range(start=%s, stop=%s)" % (self.start, self.stop)

    def __contains__(self, item):
        """Return true if value is in range."""
        return (self.start is None or item >= self.start) and (
            self.stop is None or item <= self.stop
        )

    @classmethod
    def parse(cls, s):
        """Parse a string specification into a range."""
        return Range(*(None if not p else float(p) for p in s.split(":")))


def predicates(options):
    """Create predicates from the supplied options."""

    def make_predicate(key, range):
        """Make a range predicate."""
        return lambda x: x[key] in range

    ranges = {
        k: Range.parse(v)
        for k, v in options.items()
        if k in {"p", "c", "f", "kcal", "pi"}
    }
    macro_ranges = [make_predicate(k, v) for k, v in ranges.items()]

    return macro_ranges


def matches(plans, criteria):
    """Find plans matching the criteria."""
    return (
        dict(plan, combination=i)
        for i, plan in enumerate(plans)
        if all(c(plan) for c in criteria)
    )


def main():
    """Run meal planner."""
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print_help_and_exit(0 if args else 1)

    fpath, options = parse_args(args)
    sys.stderr.write("Creating awesome meal plans...\n\n")

    records = load_data(fpath)
    cleaned = clean(records)

    n_meals = (
        int(x) if x else y
        for x, y in itertools.zip_longest(
            options.get("n", MEALS).split(":"), (MIN_MEALS, MAX_MEALS)
        )
    )
    combined = combine(cleaned, n=n_meals)
    plans = assemble(combined)
    timed = timeout(plans, float(options.get("timeout", TIMEOUT)))
    results = matches(timed, predicates(options))

    max_results = int(options.get("max-results", MAX_RESULTS))
    top = list(itertools.islice(results, max_results))
    if not top:
        print(f"Unable to find a plan for your settings.", file=sys.stderr)
        print(f"Try relaxing the criteria, or increasing the timeout.", file=sys.stderr)
    else:
        json.dump(top, sys.stdout, indent=4)


if __name__ == "__main__":
    main()
