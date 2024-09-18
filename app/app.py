import json
import os
import asyncio
import logging
import psycopg2
from psycopg2 import sql 
from panoramisk import Manager

manager = Manager(loop=asyncio.get_event_loop(),
                  host=os.environ['AMI_HOST'],
                  port=os.environ['AMI_PORT'],
                  username=os.environ['AMI_USERNAME'],
                  secret=os.environ['AMI_PASSWORD'])

# Log config
logger = logging.getLogger('AMI')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def log(msg):
    return logger.info(msg)


class PostgresDB:
    def __init__(self, host, port, dbname, user, password):
        """Initialize the connection to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password
            )
            self.cursor = self.connection.cursor()
            log("Connected to the PostgreSQL database")
        except (Exception, psycopg2.DatabaseError) as error:
            log(f"Error connecting to PostgreSQL: {error}")
            self.connection = None


    def update_column_value(self, table_name, column_name, new_value, condition_column, condition_value):
        """Update the value of a specific column based on a condition."""
        if not self.connection:
            log("No connection to the database.")
            return

        try:
            # Create the SQL query to update the column
            query = sql.SQL("UPDATE {table} SET {column} = %s WHERE {condition_col} = %s").format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name),
                condition_col=sql.Identifier(condition_column)
            )

            # Execute the query
            self.cursor.execute(query, (new_value, condition_value))

            # Commit the transaction
            self.connection.commit()
            log(f"Successfully updated {column_name} in {table_name} where {condition_column} = {condition_value}")

        except (Exception, psycopg2.DatabaseError) as error:
            log(f"Error while updating column: {error}")
            self.connection.rollback()  # Rollback in case of error

db = PostgresDB(host=os.environ['DB_HOST'], port=os.environ['DB_PORT'], dbname=os.environ['DB_NAME'], user=os.environ['DB_USERNAME'], password=os.environ['DB_PASSWORD'])

@manager.register_event('PeerStatus')
def callback(manager, message):      
    data = json.dumps(dict(message.items()),indent=4)    
    dict_message_event = json.loads(data)        
    peer_name = dict_message_event['Peer'].split('/')[1]
    log(f"Operadora: {peer_name} - Status: {dict_message_event['PeerStatus']}")
    db.update_column_value(table_name="ps_endpoints", column_name="operadora_status", new_value=dict_message_event['PeerStatus'], condition_column="id", condition_value=peer_name)


def main():
    manager.connect()
    try:
        manager.loop.run_forever()
    except KeyboardInterrupt:
        manager.loop.close()


if __name__ == '__main__':
    main()