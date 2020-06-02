import pyspark
import re
from itertools import chain
import pyspark.sql.functions as F
import pyspark.sql.types as T

def carrier_name(play_text):
    """Return the ball carrier string from a play description."""
    run_directions = ['left end', 'left tackle', 'left guard', 'up the middle',
                      'right guard', 'right tackle', 'right end']

    if any(tag in play_text for tag in run_directions):
        direction_tags = [tag for tag in run_directions if tag in play_text]
        if len(direction_tags) == 1:
            direction = direction_tags[0]
            before_direction = play_text.split(direction)[0].rstrip()
            carrier = before_direction.split(' ')[-1]
        else:
            carrier = 'NA'
    else:
        carrier = 'NA'

    return carrier


def player_name_id(row):
    name = "{}.{}".format(row[1][0], row[1].split(' ')[-1])
    return (name, row[0])

def abbrev_length(name):
    first_init = name.split('.')[0]
    return len(first_init)


# initialize local spark sql context
#sc = pyspark.SparkContext('local[8]')
spark = pyspark.sql.SparkSession.builder.master('local[8]').getOrCreate()
spark.conf.set('spark.sql.shuffle.partitions', 10)

path = '../data/nfl/'
game_id = '2017090700'
#game_file = "{}{}{}{}".format(path, 'tracking/tracking_gameId_', game_id,'.csv')
game_file = "{}{}".format(path, 'tracking/tracking_gameId_*.csv')
plays_file = "{}{}".format(path, 'plays.csv')

# load datasets
all_moments = spark.read.csv(game_file, header=True)
print(all_moments.count())
all_plays = spark.read.csv(plays_file, header=True)

# create list of play ids with a handoff event to filter plays
handoff_moments = all_moments.filter(all_moments['event'].contains('handoff'))
handoff_ids = handoff_moments.select('gameId', 'playId').distinct()

# use join to subset play descriptions
plays = all_plays.select('playId', 'gameId', 'playDescription')
rushes = plays.join(handoff_ids, on=['gameId', 'playId'], how='inner')

rushes = rushes.filter(~rushes['playDescription'].contains('pass'))
rushes = rushes.filter(~rushes['playDescription'].contains('TWO-POINT CONVERSION'))
rushes = rushes.filter(~rushes['playDescription'].contains('scrambles'))
rushes = rushes.filter(~rushes['playDescription'].contains('Aborted'))

udf_carrier = F.udf(carrier_name, T.StringType())
rushes = rushes.withColumn('carrier', udf_carrier(rushes['playDescription']))
first_init = F.udf(abbrev_length, T.IntegerType())
rushes = rushes.withColumn('first_len', first_init(rushes['carrier']))


# merge carrier name back into handoff_moments
handoff_moments = handoff_moments.select('playId', 'gameId', 'displayName')


handoffs_carrier = handoff_moments.join(rushes, on=['gameId', 'playId'],
                                        how='left')

def truncate_display(display_name, first_length):
    name_split = display_name.split(' ')
    return "{}.{}".format(display_name[0:first_length], name_split[-1])
    
udf_truncate = F.udf(truncate_display, T.StringType())

handoffs_carrier = handoffs_carrier.withColumn('display_trunc',
                                               udf_truncate('DisplayName',
                                                         'first_len'))

carrier_moments = handoffs_carrier.filter('display_trunc = carrier')
