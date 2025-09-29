"""
Modern SQLAlchemy-based database handling for ChristineAI
Replaces the old raw SQL implementation with proper type safety and security
"""
import os.path
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, Text, text
from sqlalchemy.sql import select, insert, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from christine import log
#pylint: disable=protected-access

class ChristineDB:
    """
    Modern SQLAlchemy-based database manager for ChristineAI.
    
    Provides type-safe, SQL-injection-proof database operations while maintaining
    compatibility with the existing interface used by sounds.py and status.py.
    """

    def __init__(self):
        # SQLite database path
        self.sqlite_path = "christine.sqlite"
        
        # Check if database exists
        existing_database_file = os.path.isfile(self.sqlite_path)
        
        # Create SQLAlchemy engine
        self.engine: Engine = create_engine(
            f"sqlite:///{self.sqlite_path}",
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,  # Verify connections before use
            connect_args={"check_same_thread": False}
        )
        
        # Define metadata and tables
        self.metadata = MetaData()
        self._define_tables()
        
        # Initialize database if it doesn't exist
        if not existing_database_file:
            self._initialize_database()

    def _define_tables(self):
        """Define database tables using SQLAlchemy schema."""
        
        # Status table for system state variables
        self.status_table = Table('status', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String(50), nullable=False),
            Column('value', String(255), nullable=True),
            Column('type', String(1), nullable=False)
        )
        
        # Sounds table for audio files and their metadata
        self.sounds_table = Table('sounds', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('text', Text, nullable=False),
            Column('file_path', String(255), nullable=False),
            Column('proximity_volume_adjust', Float, nullable=False, default=1.0),
            Column('intensity', Float, nullable=False, default=0.5),
            Column('replay_wait', Integer, nullable=False, default=0),
            Column('collections', String(255), nullable=False),
            Column('pause_processing', Boolean, nullable=False, default=False)
        )

    def _initialize_database(self):
        """Initialize database from SQL file if it doesn't exist."""
        try:
            # Create tables
            self.metadata.create_all(self.engine)
            
            # Load initial data from SQL file
            with open(file='christine.sql', mode='r', encoding='utf-8') as sql_file:
                sql_content = sql_file.read()
            
            # Execute the SQL file content (this is safe since it's our own SQL file)
            with self.engine.begin() as connection:
                # Split and execute statements (basic parsing)
                statements = sql_content.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            connection.execute(text(statement))
                        except SQLAlchemyError as e:
                            # Skip errors from CREATE TABLE IF NOT EXISTS, etc.
                            if "already exists" not in str(e).lower():
                                log.db.warning("SQL statement warning: %s", e)
                                
        except Exception as ex:
            log.db.error("Database initialization error: %s %s", ex.__class__, ex)
            raise

    def disconnect(self):
        """Properly close database connections."""
        try:
            self.engine.dispose()
        except Exception as ex:
            log.db.error("Database disconnect error: %s %s", ex.__class__, ex)

    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get all status records as a list of dictionaries."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.status_table))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as ex:
            log.db.error("Error fetching all status: %s", ex)
            return []

    def get_status_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific status record by name."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    select(self.status_table).where(self.status_table.c.name == name)
                )
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except SQLAlchemyError as ex:
            log.db.error("Error fetching status '%s': %s", name, ex)
            return None

    def update_status(self, name: str, value: str) -> bool:
        """Update a status value by name. Returns True if successful."""
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    update(self.status_table)
                    .where(self.status_table.c.name == name)
                    .values(value=value)
                )
                return result.rowcount > 0
        except SQLAlchemyError as ex:
            log.db.error("Error updating status '%s': %s", name, ex)
            return False

    def get_all_sounds(self) -> List[Dict[str, Any]]:
        """Get all sound records as a list of dictionaries."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.sounds_table))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as ex:
            log.db.error("Error fetching all sounds: %s", ex)
            return []

    def get_sounds_by_collection(self, collection: str) -> List[Dict[str, Any]]:
        """Get sounds that belong to a specific collection."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    select(self.sounds_table)
                    .where(self.sounds_table.c.collections.like(f'%{collection}%'))
                )
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as ex:
            log.db.error("Error fetching sounds for collection '%s': %s", collection, ex)
            return []

    def add_sound(self, sound_text: str, file_path: str, collections: str, 
                  intensity: float = 0.5, replay_wait: int = 0, 
                  proximity_volume_adjust: float = 1.0, 
                  pause_processing: bool = False) -> Optional[int]:
        """Add a new sound record. Returns the new sound ID if successful."""
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    insert(self.sounds_table).values(
                        text=sound_text,
                        file_path=file_path,
                        collections=collections,
                        intensity=intensity,
                        replay_wait=replay_wait,
                        proximity_volume_adjust=proximity_volume_adjust,
                        pause_processing=pause_processing
                    )
                )
                return result.inserted_primary_key[0]
        except SQLAlchemyError as ex:
            log.db.error("Error adding sound: %s", ex)
            return None

    def add_status(self, name: str, value: str, type_code: str) -> Optional[int]:
        """Add a new status record. Returns the new status ID if successful."""
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    insert(self.status_table).values(
                        name=name,
                        value=value,
                        type=type_code
                    )
                )
                return result.inserted_primary_key[0]
        except SQLAlchemyError as ex:
            log.db.error("Error adding status: %s", ex)
            return None

    # ===== HEALTH CHECK AND UTILITIES =====
    
    def health_check(self) -> bool:
        """Verify database connectivity and basic functionality."""
        try:
            with self.engine.connect() as connection:
                # Simple query to test connectivity
                result = connection.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as ex:
            log.db.error("Database health check failed: %s", ex)
            return False

    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables - useful for monitoring."""
        counts = {}
        try:
            with self.engine.connect() as connection:
                for table_name in ['status', 'sounds']:
                    if table_name == 'status':
                        table = self.status_table
                    else:
                        table = self.sounds_table
                    
                    result = connection.execute(select(table.c.id).count())
                    counts[table_name] = result.scalar()
        except Exception as ex:
            log.db.error("Error getting table counts: %s", ex)
            
        return counts


# Instantiate the database
database = ChristineDB()
