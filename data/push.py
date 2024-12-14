import pyarrow as pa
import pyarrow.dataset as ds
import numpy as np
import psycopg2
import sys
import argparse
import urllib.parse
import os
import glob

class FileReader:
    @staticmethod
    def read_arrow_file(file_path: str, columns: list = None, filter_condition = None):
        """
        Read Arrow file with robust error handling
        
        :param file_path: Path to the Arrow file
        :param columns: Columns to read
        :param filter_condition: Optional filter to apply
        :return: PyArrow Table
        """
        try:
            # First, try using dataset API (works for single files and directories)
            try:
                dataset = ds.dataset(file_path, format='arrow')
                return dataset.to_table(columns=columns, filter=filter_condition)
            except Exception as dataset_error:
                # If dataset API fails, try file reader
                try:
                    # Try reading as a single Arrow file
                    reader = pa.ipc.open_file(file_path)
                    table = reader.read_table()
                    
                    # Apply columns and filter if specified
                    if columns:
                        table = table.select(columns)
                    
                    # Apply filter if specified (requires additional processing)
                    if filter_condition and callable(filter_condition):
                        mask = filter_condition(table)
                        table = table.filter(mask)
                    
                    return table
                
                except Exception as file_error:
                    raise ValueError(f"Could not read Arrow file. Errors:\n"
                                     f"Dataset API: {dataset_error}\n"
                                     f"File Reader: {file_error}")
        
        except Exception as e:
            raise ValueError(f"Error reading Arrow file {file_path}: {e}")

class DatabaseConnectionParser:
    @staticmethod
    def parse_connection_string(connection_string: str) -> dict:
        """
        Parse a PostgreSQL connection string into a dictionary of connection parameters.
        
        :param connection_string: Connection string to parse
        :return: Dictionary of connection parameters
        """
        # Check if it's an environment variable
        if connection_string.startswith('$'):
            env_var = connection_string[1:]
            connection_string = os.environ.get(env_var)
            if not connection_string:
                raise ValueError(f"Environment variable {env_var} not found")
        
        # Normalize the scheme
        if connection_string.startswith('postgresql://'):
            normalized_string = connection_string
        elif connection_string.startswith('postgres://'):
            normalized_string = connection_string.replace('postgres://', 'postgresql://', 1)
        else:
            # Try to parse as a standard connection string
            try:
                # Attempt to use urllib.parse
                parsed = urllib.parse.urlparse(f'postgresql://{connection_string}')
            except Exception:
                raise ValueError("Invalid connection string format")
        
        # Parse the URL
        parsed = urllib.parse.urlparse(normalized_string)
        
        # Extract components
        connection_params = {
            'dbname': parsed.path.lstrip('/'),  # Remove leading slash
            'user': parsed.username or '',
            'password': parsed.password or '',
            'host': parsed.hostname or 'localhost',
            'port': str(parsed.port or '5432')
        }
        
        # Remove any None or empty string values
        return {k: v for k, v in connection_params.items() if v}

class ECGDataProcessor:
    def __init__(self, 
                 arrow_file_path: str, 
                 connection_params: dict,
                 table_name: str = 'ecg_segments',
                 rows_to_process: int = 10):
        """
        Initialize the ECG data processor
        
        :param arrow_file_path: Path to the Arrow file
        :param connection_params: Dictionary of database connection parameters
        :param table_name: Name of the table to insert data into
        :param rows_to_process: Number of rows to process
        """
        self.arrow_file_path = arrow_file_path
        self.db_connection_params = connection_params
        self.table_name = table_name
        self.rows_to_process = rows_to_process
    
    def _create_timescaledb_table(self, cursor):
        """
        Create the TimescaleDB table if it doesn't exist
        
        :param cursor: Database cursor
        """
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            time TIMESTAMPTZ NOT NULL,
            infant_id INT,
            segment_id INT,
            channel_0 FLOAT[],
            channel_1 FLOAT[],
            label BIGINT
        );
        
        SELECT create_hypertable(
            '{self.table_name}', 
            'time', 
            if_not_exists => TRUE
        );
        """
        cursor.execute(create_table_query)
    
    def process_first_x_rows(self) -> list:
        """
        Read the first X rows from the Arrow file
        
        :return: List of processed rows
        """
        # Read the dataset
        table = FileReader.read_arrow_file(
            self.arrow_file_path, 
            columns=['infant_id', 'segment_id', 'input', 'label']
        )
        
        # Limit rows if necessary
        if len(table) > self.rows_to_process:
            table = table.slice(0, self.rows_to_process)
        
        # Convert to numpy for easier manipulation
        infant_ids = table['infant_id'].to_numpy()
        segment_ids = table['segment_id'].to_numpy()
        inputs = table['input'].to_numpy()
        labels = table['label'].to_numpy()
        
        # Prepare data for database insertion
        processed_rows = []
        for i in range(len(infant_ids)):
            processed_rows.append((
                infant_ids[i], 
                segment_ids[i], 
                inputs[i][0].tolist(),  # Channel 0 
                inputs[i][1].tolist(),  # Channel 1
                labels[i]
            ))
        
        return processed_rows
    
    def insert_to_timescaledb(self, rows: list):
        """
        Insert processed rows into TimescaleDB
        
        :param rows: List of processed row tuples
        """
        # Establish database connection
        conn = psycopg2.connect(**self.db_connection_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create table if not exists
        self._create_timescaledb_table(cursor)
        
        # Prepare insert query
        insert_query = f"""
        INSERT INTO {self.table_name} 
        (time, infant_id, segment_id, channel_0, channel_1, label)
        VALUES (
            NOW(),  -- Current timestamp
            %s,     -- infant_id
            %s,     -- segment_id
            %s,     -- channel_0
            %s,     -- channel_1
            %s      -- label
        )
        """
        
        # Execute batch insert
        cursor.executemany(insert_query, rows)
        
        # Close connection
        cursor.close()
        conn.close()
    
    def process_and_insert(self):
        """
        Process rows and insert into database
        """
        rows = self.process_first_x_rows()
        self.insert_to_timescaledb(rows)

def main():
    """
    Main entry point for CLI usage
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Process ECG data from Arrow file to TimescaleDB')
    parser.add_argument('connection_string', type=str, 
                        help='PostgreSQL connection string')
    parser.add_argument('file_path', type=str, 
                        help='Path to the Arrow file')
    parser.add_argument('--rows', type=int, default=10, 
                        help='Number of rows to process (default: 10)')
    parser.add_argument('--table', type=str, default='ecg_segments', 
                        help='Name of the table to insert data (default: ecg_segments)')
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Parse connection string
        connection_params = DatabaseConnectionParser.parse_connection_string(args.connection_string)
        
        # Create processor
        processor = ECGDataProcessor(
            arrow_file_path=args.file_path,
            connection_params=connection_params,
            table_name=args.table,
            rows_to_process=args.rows
        )
        
        # Process and insert data
        processor.process_and_insert()
        
        print(f"Successfully processed and inserted {args.rows} rows to {args.table}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
