import pyspark
import re
from itertools import chain
import pyspark.sql.functions as F
import pyspark.sql.types as T

def carrier_name(row):
    """Return the ball carrier string from a play description."""
    play = row['playDescription']
    run_directions = ['left end', 'left tackle', 'left guard', 'up the middle',
                      'right guard', 'right tackle', 'right end']

    if any(tag in play for tag in run_directions):
        direction_tags = [tag for tag in run_directions if tag in play]
        if len(direction_tags) == 1:
            direction = direction_tags[0]
            before_direction = play.split(direction)[0].rstrip()
            carrier = before_direction.split(' ')[-1]
        else:
            carrier = 'NA'
    else:
        carrier = 'NA'

    return carrier

def player_name_id(row):
    name = "{}.{}".format(row[1][0], row[1].split(' ')[-1])
    return (name, row[0])


# initialize local spark sql context
sc = pyspark.SparkContext('local[8]')
spark = pyspark.sql.SparkSession.builder.master('local[8]').getOrCreate()
spark.conf.set('spark.sql.shuffle.partitions', 10)

path = '../data/nfl/'
game_id = '2017090700'
#game_file = "{}{}{}{}".format(path, 'tracking/tracking_gameId_', game_id,
#                              '.csv')
game_file = "{}{}".format(path, 'tracking/tracking_gameId_*.csv')
plays_file = "{}{}".format(path, 'plays.csv')

# load datasets
game_moments = spark.read.csv(game_file, header=True)
all_plays = spark.read.csv(plays_file, header=True)

game_players = game_moments.select('nflId', 'displayName').distinct().rdd
names_ids = game_players.map(lambda line: player_name_id(line))
id_map = names_ids.collectAsMap()
#mapper = F.create_map([F.lit(x) for x in chain(*id_map.items())])

# create list of play ids with a handoff event to filter plays
handoffs = game_moments.filter(game_moments['event'].contains('handoff'))
handoff_ids = handoffs.select('playId').distinct()
id_list = [row['playId'] for row in handoff_ids.rdd.collect()]

# select plays from game and filter to those with a handoff
plays_game = all_plays #.filter(all_plays['gameId'] == int(game_id))
rushes = plays_game.filter(plays_game['playId'].isin(id_list))

# list of words in play descriptions to filter out undesired plays
tags_remove = ['pass', 'TWO-POINT CONVERSION', 'scrambles', 'Aborted']
for word in tags_remove:
    rushes = rushes.filter(~rushes['playDescription'].contains(word))

# get ball carrier names
carriers = rushes.select('playDescription').rdd.map(carrier_name)


sc.stop()
