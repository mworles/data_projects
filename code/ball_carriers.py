import pyspark
import pyspark.sql.functions as F
import pyspark.sql.types as T


def carrier_name(play_text):
    """Return ball carrier string from play description text."""
    run_directions = ['left end', 'left tackle', 'left guard', 'up the middle',
                      'right guard', 'right tackle', 'right end']

    if any(tag in play_text for tag in run_directions):
        # list of all direction tags in the play description
        direction_tags = [tag for tag in run_directions if tag in play_text]

        # if one tag, the ball carrier is the string before it
        if len(direction_tags) == 1:
            direction = direction_tags[0]
            before_direction = play_text.split(direction)[0].rstrip()
            carrier = before_direction.split(' ')[-1]

        # if multiple tags play is not a valid rushing attempt
        else:
            carrier = 'NA'
    # if no tag there is no carrier
    else:
        carrier = 'NA'

    return carrier


def length_of_initial(name):
    """Return the length of first name abbreviation from play descripton."""
    first_abbrev = name.split('.')[0]
    return len(first_abbrev)


def truncate_display(display_name, first_length):
    """Return string with truncated first name and full last name."""
    name_split = display_name.split(' ')
    return "{}.{}".format(display_name[0:first_length], name_split[-1])


# initialize local spark sql context
spark = pyspark.sql.SparkSession.builder.master('local[8]').getOrCreate()
spark.conf.set('spark.sql.shuffle.partitions', 10)

# name files to obtain data and load
data_path = '../data/nfl/'
game_file = "{}{}".format(data_path, 'tracking/tracking_gameId_*.csv')
plays_file = "{}{}".format(data_path, 'plays.csv')
all_moments = spark.read.csv(game_file, header=True)
all_plays = spark.read.csv(plays_file, header=True)

# need unique plays containing a handoff event
handoff_moments = all_moments.filter(all_moments['event'].contains('handoff'))
handoff_ids = handoff_moments.select('gameId', 'playId').distinct()

# use join to filter play descriptions to those containing a handoff
plays = all_plays.select('playId', 'gameId', 'playDescription')
rushes = plays.join(handoff_ids, on=['gameId', 'playId'], how='inner')

# remove some plays that don't result in a rushing attempt
rushes = rushes.filter(~rushes['playDescription'].contains('pass'))
rushes = rushes.filter(~rushes['playDescription'].contains('TWO-POINT CONVERSION'))
rushes = rushes.filter(~rushes['playDescription'].contains('scrambles'))
rushes = rushes.filter(~rushes['playDescription'].contains('Aborted'))

# use play description to add column with name of the ball carrier
udf_carrier = F.udf(carrier_name, T.StringType())
rushes = rushes.withColumn('carrier', udf_carrier(rushes['playDescription']))

# get number of letters in ball carrier first initial
# need this below to truncate names in tracking data
udf_length = F.udf(length_of_initial, T.IntegerType())
rushes = rushes.withColumn('first_len', udf_length(rushes['carrier']))



# join ball carrier name and initial to moments from all handoff plays
rushes = rushes.select('gameId', 'playId', 'carrier', 'first_len')
handoffs = handoff_moments.join(F.broadcast(rushes), on=['gameId', 'playId'],
                                how='left')

# truncate the player name in tracking data to match ball carrier name format
udf_truncate = F.udf(truncate_display, T.StringType())
handoffs_carrier = handoffs.withColumn('display_trunc',
                                       udf_truncate('DisplayName',
                                                    'first_len'))

# keep rows where tracking name matches carrier name
carrier_moments = handoffs_carrier.filter('display_trunc = carrier')

# keep unique columns needed to identify ball carriers on plays
output = carrier_moments.select('gameId', 'playId', 'nflId', 'DisplayName')

output = output.orderBy('gameId', 'playId')

output.toPandas().to_csv('{}{}'.format(data_path, 'ball_carriers.csv'))
