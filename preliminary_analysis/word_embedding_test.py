from db_configs import host, database, user, password
import psycopg2 as pg
import pandas as pd

from gensim.models.word2vec import Word2Vec, LineSentence


# connect to the database
connection = pg.connect(host=host, dbname=database, user=user, password=password)

# import a table:
sequences_table = pd.read_sql_query("SELECT * FROM telecom_pt.sequences_table WHERE concelhos_sequence!=''",con=connection)


def sequence_list(val):
    return val.split(',')

def length_of_sequences(val):
    return len(val)

sequences_table['sequences_listed'] = sequences_table['concelhos_sequence'].apply(sequence_list)
sequences_table['length_of_sequences'] = sequences_table['sequences_listed'].apply(length_of_sequences)


# create vectors
model = Word2Vec(sequences_table[sequences_table['length_of_sequences']>2]['sequences_listed'], size=2, window=1, min_count=1, workers=4)

sentences = model.predict_output_word(['Gare do Oriente', 'Vasco da Gama aquarium'], topn=5)

#sentences2 = LineSentence('Chelas', max_sentence_length=10, limit=None)
print(sequences_table[sequences_table['length_of_sequences']>2]['sequences_listed'])
print('all roamers: ',len(sequences_table['sequences_listed']),', after filters: ',len(sequences_table[sequences_table['length_of_sequences']>2]['sequences_listed']) )
print(sentences)

