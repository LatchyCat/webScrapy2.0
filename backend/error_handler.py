# error_handler.py
import logging
from datetime import datetime
import json
import os

class ErrorLogger:
    def __init__(self):
        self.setup_logging()
        self.error_solutions = {
            'WorkingOutsideApplication': {
                'error_type': 'Working outside of application context',
                'solution': 'Use "with app.app_context():" when working with database operations.',
                'code_example': 'with app.app_context():\n    db.session.add(item)\n    db.session.commit()'
            },
            'DatabaseConnectionError': {
                'error_type': 'Database connection error',
                'solution': 'Check if database file exists and has proper permissions.',
                'code_example': 'ls -l instance/charleston_news.db'
            },
            'JSONSerializationError': {
                'error_type': 'JSON serialization error',
                'solution': 'Ensure data is JSON serializable before saving.',
                'code_example': 'json.dumps(data) # Test if serializable'
            }
        }

    def setup_logging(self):
        self.logger = logging.getLogger('ErrorHandler')
        handler = logging.FileHandler('errors.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.ERROR)

    def log_error(self, error_type, error_message, context=None):
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': str(error_message),
            'context': context,
            'solution': self.get_solution(error_type)
        }

        self.logger.error(json.dumps(error_entry, indent=2))
        return error_entry

    def get_solution(self, error_type):
        if error_type in self.error_solutions:
            return self.error_solutions[error_type]
        return {
            'error_type': 'Unknown Error',
            'solution': 'Search error message on Stack Overflow or GitHub issues.',
            'code_example': None
        }
