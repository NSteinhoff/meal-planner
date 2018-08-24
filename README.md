# Simple meal plan generator

```
usage: meal_planner.py FILE [OPTIONS]

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
  -n                   Maximum number of meals in plan (default=5).
  -kcal                Calories (kcal) MIN:MAX
  -p                   Protein (g) MIN:MAX
  -c                   Carbs (g) MIN:MAX
  -f                   Fat (g) MIN:MAX
  -pi                  Fraction of calories from protein MIN:MAX
  --max-results        Maximum number of plans to produce (default=10).
  -h, --help           Show this message and exit.

```
