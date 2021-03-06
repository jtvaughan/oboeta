#!/usr/bin/env python3

# Review Lines from the Selected Deck in Random Order Until All Pass
# Written in 2012 by 伴上段
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along
# with this software. If not, see
# <http://creativecommons.org/publicdomain/zero/1.0/>.

from argparse import *
from csv import *
from datetime import *
from os.path import *
from random import *
from sys import *

def Main(deckfile, logfile, commandfile, field_sep, date_format, is_dry_run, use_sm2):
  ret = 0
  if isinstance(deckfile, str) and not exists(deckfile):
    stderr.write("deck file does not exist: " + deckfile + "\n")
    ret = 1
  if not exists(logfile):
    stderr.write("log file does not exist: " + logfile + "\n")
    ret = 1
  if not exists(commandfile):
    stderr.write("command file (pipe?) does not exist: " + commandfile + "\n")
    ret = 1
  if ret != 0:
    return 1;

  reviewing_cards = []
  failed_cards = []

  deckf = None
  try:
    deckf = (open(deckfile, 'r') if isinstance(deckfile, str) else deckfile)
    for fields in reader(deckf, delimiter=field_sep):
      if len(fields) != 0:
        reviewing_cards.append([fields[0], field_sep.join(fields), False])
  finally:
    if deckf is not None:
      deckf.close()

  def logreview(logf, card, command):
    logf.write(card[0] + field_sep + datetime.now().strftime(date_format) + field_sep + command)

  sm2_commands = set(str(v) + "\n" for v in range(6))
  shuffle(reviewing_cards)
  with open(commandfile, 'r') as commandf:
    with open(logfile, 'a') as logf:
      while reviewing_cards or failed_cards:
        if not reviewing_cards:
          reviewing_cards, failed_cards = failed_cards, reviewing_cards
          shuffle(reviewing_cards)
        card = reviewing_cards.pop()
        stdout.write(card[1] + "\n")
        stdout.flush()
        command = commandf.readline()
        if use_sm2:
          if command in sm2_commands:
            if not (is_dry_run or card[-1]):
              logreview(logf, card, command)
            if int(command[0:1]) < 3:
              card[-1] = True
              failed_cards.append(card)
          elif command == "q\n":
            return 0
          else:
            stderr.write("unrecognized command: " + command + "\n")
            return 2
        else:
          # Leitner system
          if command == "+\n":
            if not (is_dry_run or card[-1]):
              logreview(logf, card, "+\n")
          elif command == "-\n":
            if not is_dry_run:
              logreview(logf, card, "-\n")
            card[-1] = True
            failed_cards.append(card)
          elif command.lower() == "q\n":
            return 0
          else:
            stderr.write("unrecognized command: " + command + "\n")
            return 2
        logf.flush()

  return 0

if __name__ == "__main__":
  parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description="""  Review lines from standard input as though they were flashcards
  and log the results.  Both standard input and the specified log file must be
  CSV files with the same field separator character, which is specified via -s.

  This program works with either the Leitner system or the SuperMemo algorithm,
  version 2 (SM-2).

formatting:

  This program treats the first field of each nonempty line from the deck as
  that line's unique ID; otherwise, this program is agnostic about formatting.

  New log file entries will have this format:

    <ID> <field-separator> <timestamp> <field-separator> <result>

  where <ID> is the unique ID of the line (card) associated with the record,
  <field-separator> is the CSV field separator, <timestamp> is the record's
  timestamp (you can modify its format via the -f option), and <result> is the
  result of the review.

  For Leitner-system-based reviews, <result> is either '+' or '-'.
  '+' indicates that the user passed the review at the specified time, whereas
  '-' indicates that the user failed at the specified time.

  For SM-2-based reviews, <result> is an integer in the range [0,5] indicating
  the "quality of review response" that the user provided.  (0 indicates a
  complete memory blackout whereas 5 means the review was a piece of cake.)

output:

  This program shuffles lines and prints them to standard output one at a time
  in CSV format.  After printing a card, this program will wait for a command
  from the specified command file.  Commands are single-word lines
  terminated by standard newline (\\n) characters.  For Leitner-system-based
  reviews, the commands are:

    +   the user passed the card
    -   the user didn't pass the card
    q   the user is terminating the quiz

  For SM-2-based reviews, the commands are:

    0   quality of review response 0
    1   quality of review response 1
    2   quality of review response 2
    3   quality of review response 3
    4   quality of review response 4
    5   quality of review response 5
    q   the user is terminating the quiz

  All other values are erroneous.""")
  parser.add_argument("-d", "--dry-run", default=False, action="store_true", help="don't log the results of the review")
  parser.add_argument("-f", "--date-format", default="%Y年%m月%d日", help="the format of dates/timestamps in the log file (uses date/strftime flags, default: %%Y年%%m月%%d日)")
  parser.add_argument("-s", "--field-sep", default="\t", help="the CSV field separator (default: \\t)")
  parser.add_argument("-2", "--use-sm2", default=False, action="store_true", help="use the SM-2 algorithm instead of the Leitner system")
  parser.add_argument("commandfile", help="a file (usually a named pipe) providing review commands")
  parser.add_argument("logfile", help="a CSV-formatted file containing records for the deck's lines")

  args = parser.parse_args()
  try:
    ret = Main(stdin, args.logfile, args.commandfile, args.field_sep, args.date_format, args.dry_run, args.use_sm2)
  except KeyboardInterrupt:
    ret = 0
  exit(ret)

