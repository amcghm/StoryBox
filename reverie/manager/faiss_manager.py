import sqlite3
import faiss
import numpy as np
from loguru import logger
from reverie.common.llm import embedding_model
from reverie.config.config import Config


class FaissManager:
    def __init__(self, dimension, sqlite_db_path, index_type='L2', batch_size=128):
        """
        Initialize the Faiss index manager
        :param dimension: Vector dimension
        :param sqlite_db_path: Path to the SQLite database file
        :param index_type: Index type ('L2' for Euclidean distance, 'IP' for Inner Product)
        :param batch_size: Batch size for importing from sqlite3 to faiss
        """
        self.dimension = dimension
        if index_type == 'L2':
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == 'IP':
            self.index = faiss.IndexFlatIP(dimension)
        else:
            raise ValueError("Unsupported index type. Use 'L2' or 'IP'.")

        self.batch_size = batch_size

        # Initialize database connection
        self._connect_with_db(sqlite_db_path)

    def _connect_with_db(self, db_path):
        """
        Connect to the sqlite3 database
        :param db_path: Path to the sqlite3 database file
        :return: None
        """
        self.conn = sqlite3.connect(db_path)

    def _get_event_by_id(self, event_id: int, return_str: bool = False):
        """
        Get an event from the sqlite3 database
        :param event_id: Event ID
        :param return_str: Whether to return in string format
        :return: Event
        """
        cursor = self.conn.cursor()
        cursor.execute("""SELECT * FROM event WHERE event_id = ?""", (event_id,))
        result = cursor.fetchone()
        return str(result) if return_str else result

    def _get_events_by_ids(self, event_ids: list[int], return_str: bool = False):
        """
        Get multiple events from the sqlite3 database
        :param event_ids: List of event IDs
        :param return_str: Whether to return in string format
        :return: List of events
        """
        cursor = self.conn.cursor()
        placeholders = ','.join(['?'] * len(event_ids))
        query = f"SELECT * FROM event WHERE event_id IN ({placeholders})"
        cursor.execute(query, event_ids)
        results = cursor.fetchall()
        return [str(result) for result in results] if return_str else results

    def add_embeddings(self, embeddings):
        """
        Add embeddings to the index
        :param embeddings: Numpy array, shape (n_samples, dimension)
        """
        if not isinstance(embeddings, np.ndarray):
            raise ValueError("Embeddings should be a numpy array.")
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embeddings should have dimension {self.dimension}.")
        self.index.add(embeddings.astype('float32'))

    def add_embeddings_from_db(self):
        logger.info("Starting to add embeddings from the database.")

        cursor = self.conn.cursor()
        cursor.execute("SELECT description, detail FROM event")
        rows = cursor.fetchall()

        logger.info(f"Fetched {len(rows)} rows from the database.")

        batch_embeddings = []
        total_batches = 0
        total_embeddings = 0

        for description, detail in rows:
            # detail might be empty, use description when empty
            text = detail if detail else description
            embedding = embedding_model.encode(text, truncate_dim=self.dimension).astype('float32')
            batch_embeddings.append(embedding)

            # When enough embeddings are collected, add them in batches to the Faiss index
            if len(batch_embeddings) == self.batch_size:
                self.index.add(np.array(batch_embeddings))
                total_batches += 1
                total_embeddings += len(batch_embeddings)
                logger.debug(f"Batch {total_batches}: Added {len(batch_embeddings)} rows to the index.")
                batch_embeddings = []  # Clear the buffer list, prepare for the next batch

        # Add the remaining embeddings
        if batch_embeddings:
            self.index.add(np.array(batch_embeddings))
            total_embeddings += len(batch_embeddings)
            logger.debug(f"Final batch: Added {len(batch_embeddings)} rows to the index.")

        logger.debug(f"Completed adding embeddings. Total embeddings added: {total_embeddings}.")

    def query(self, query_input: str | np.ndarray, k=5, return_events=True):
        """
        Query vectors most similar to the given embedding or text
        :param query_input: Query input, can be text (str) or embedding vector (numpy array)
        :param k: Number of nearest neighbors to return
        :param return_events: Whether to directly return instances
        :return: Instances or (distances and indices)
        """

        # If the input is in str format, it needs to be encoded first
        if isinstance(query_input, str):
            query_embedding = embedding_model.encode(query_input, truncate_dim=self.dimension).astype('float32').reshape(1, -1)

        elif isinstance(query_input, np.ndarray):
            query_embedding = query_input.astype('float32')
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            if query_embedding.shape[1] != self.dimension:
                raise ValueError(f"Query embedding should have dimension {self.dimension}.")
        else:
            raise ValueError("query_input must be either a string (text) or a numpy array (embedding).")

        distances, indices = self.index.search(query_embedding, k)
        if not return_events:
            return distances, indices

        # The indices here differ from event id by 1, so they all need + 1
        event_ids = [i + 1 for i in indices]
        events = self._get_events_by_ids(event_ids)
        return events

    def save_index(self, file_path):
        """
        Save the index to disk
        :param file_path: File path to save
        """
        faiss.write_index(self.index, file_path)

    def load_index(self, file_path):
        """
        Load the index from disk
        :param file_path: Index file path
        """
        self.index = faiss.read_index(file_path)

    def get_index_size(self):
        """
        Get the number of vectors in the current index
        :return: Number of vectors
        """
        return self.index.ntotal


faiss_manager = FaissManager(Config.faiss_manager['dimension'], Config.database_url.replace("sqlite:///", "", 1))
faiss_manager.add_embeddings_from_db()
