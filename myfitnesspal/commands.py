from __future__ import print_function

import argparse
from datetime import datetime
from getpass import getpass
import logging
from pprint import pprint

from blessed import Terminal
from dateutil.parser import parse as dateparse

from .keyring_utils import (
    delete_password_in_keyring,
    get_password_from_keyring_or_interactive,
    store_password_in_keyring,
)
from . import Client


COMMANDS = {}

logger = logging.getLogger(__name__)


def get_command_list():
    command_lines = []
    for name, info in COMMANDS.items():
        if info['is_alias']:
            continue
        message = "{0}: {1}".format(name, info['description'])
        if info['aliases']:
            message = message + '; aliases: {0}'.format(
                ', '.join(info['aliases'])
            )
        command_lines.append(message)
    prolog = 'available commands:\n'
    return prolog + '\n'.join(['  ' + cmd for cmd in command_lines])


def command(desc, name=None, aliases=None):
    if aliases is None:
        aliases = []

    def decorator(fn):
        main_name = name if name else fn.__name__
        command_details = {
            'function': fn,
            'description': desc,
            'is_alias': False,
            'aliases': [],
        }

        COMMANDS[main_name] = command_details
        for alias in aliases:
            COMMANDS[alias] = command_details.copy()
            COMMANDS[alias]['is_alias'] = True
            COMMANDS[main_name]['aliases'].append(alias)
        return fn
    return decorator


@command(
    "Store a MyFitnessPal password in your system keychain.",
    aliases=['store-password'],
)
def store_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'username',
        help='The MyFitnessPal username for which to store this password.'
    )
    args = parser.parse_args(extra)

    password = getpass(
        "MyFitnessPal Password for {username}: ".format(
            username=args.username
        )
    )

    store_password_in_keyring(args.username, password)


@command(
    "Delete a MyFitnessPal password from your system keychain.",
    aliases=['delete-password'],
)
def delete_password(args, *extra, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'username',
        help='The MyFitnessPal username for which to delete a stored password.'
    )
    args = parser.parse_args(extra)

    delete_password_in_keyring(args.username)


def _default_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'username',
        help='The MyFitnessPal username to obtain data for.'
    )
    return parser

@command(
    "Display MyFitnessPal data for a given date.",
)
def day(args, *extra, **kwargs):
    parser = _default_arg_parser()
    parser.add_argument(
        'date',
        nargs='?',
        default=datetime.now().strftime('%Y-%m-%d'),
        type=lambda datestr: dateparse(datestr).date(),
        help=u'The date for which to display information.'
    )
    args = parser.parse_args(extra)

    password = get_password_from_keyring_or_interactive(args.username)
    client = Client(args.username, password)
    day = client.get_date(args.date)

    t = Terminal()

    print(t.green(args.date.strftime('%Y-%m-%d')))
    for meal in day.meals:
        print(t.bold(meal.name.title()))
        for entry in meal.entries:
            print(u'* {entry.name}'.format(entry=entry))
            print(
                t.italic_bright_black(
                    u'  {entry.nutrition_information}'.format(entry=entry)
                )
            )
        print(u'')

    print(t.bold("Totals"))
    for key, value in day.totals.items():
        print(
            u'{key}: {value}'.format(
                key=key.title(),
                value=value,
            )
        )
    print(u'Water: {amount}'.format(amount=day.water))
    if day.notes:
        print(t.italic(day.notes))

@command(
    "Get Nutrition Goal macros.",
)
def get_nutri_goals(args, *extra, **kwargs):
    parser = _default_arg_parser()
    args = parser.parse_args(extra)

    password = get_password_from_keyring_or_interactive(args.username)
    client = Client(args.username, password)

    goals = client.get_nutrition_goals()

    _print_goals(goals)

@command(
    "Change Nutrition Goal macros.",
)
def change_nutri_goals(args, *extra, **kwargs):
    parser = _default_arg_parser()
    parser.add_argument('--protein', help='Protein (g)', type=float)
    parser.add_argument('--carbs', help='Carbohydrates (g)', type=float)
    parser.add_argument('--fat', help='Fat (g)', type=float)
    args = parser.parse_args(extra)

    password = get_password_from_keyring_or_interactive(args.username)
    client = Client(args.username, password)

    goals = client.set_all_nutrition_goals_by_macros(
        protein=args.protein, fat=args.fat, carbohydrates=args.carbs)

    _print_goals(goals)

def _print_goals(goals):
    t = Terminal()
    print(t.green(goals['valid_from']))
    pprint(goals['default_goal'])


@command(
    "Quick Add"
)
def quick_add(args, *extra, **kwargs):
    parser = _default_arg_parser()
    parser.add_argument('--calories', help='Calories', type=int, default=None)
    parser.add_argument('--protein', help='Protein (g)', type=float, default=None)
    parser.add_argument('--carbs', help='Carbohydrates (g)', type=float, default=None)
    parser.add_argument('--fat', help='Fat (g)', type=float, default=None)
    args = parser.parse_args(extra)

    password = get_password_from_keyring_or_interactive(args.username)
    client = Client(args.username, password)

    result = client.quick_add(
        protein=args.protein, fat=args.fat, carbs=args.carbs,
        calories=args.calories)

    pprint(result)
