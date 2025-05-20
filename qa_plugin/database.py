"""
Database module for QA Automation Plugin.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class TestResult(Base):
    """SQLAlchemy model for test results."""
    __tablename__ = 'test_results'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    test_type = Column(String)
    test_name = Column(String)
    status = Column(String)
    duration = Column(Float)
    error_message = Column(String, nullable=True)
    report_path = Column(String, nullable=True)
    is_cloud = Column(Boolean, default=False)

    def __repr__(self):
        return f"<TestResult(id={self.id}, test={self.test_name}, status={self.status})>"

class QADatabase:
    """Database manager for QA Automation Plugin."""
    
    def __init__(self, db_path='qa_results.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self._ensure_db_directory()
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self._init_db()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            except Exception as e:
                logger.error(f"Error creating database directory: {e}")
                raise
    
    def _init_db(self):
        """Initialize database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_results(self, limit=None):
        """Get test results from database."""
        session = self.Session()
        try:
            query = session.query(TestResult).order_by(TestResult.timestamp.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            raise
        finally:
            session.close()
    
    def add_result(self, test_type, test_name, status, duration, error_message=None, report_path=None):
        """Add a new test result to the database."""
        session = self.Session()
        try:
            result = TestResult(
                test_type=test_type,
                test_name=test_name,
                status=status,
                duration=duration,
                error_message=error_message,
                report_path=report_path,
                is_cloud=os.environ.get('STREAMLIT_CLOUD', 'false').lower() == 'true'
            )
            session.add(result)
            session.commit()
            logger.info(f"Added test result: {test_name} ({status})")
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding test result: {e}")
            raise
        finally:
            session.close()
    
    def clear_results(self):
        """Clear all test results from the database."""
        session = self.Session()
        try:
            session.query(TestResult).delete()
            session.commit()
            logger.info("Cleared all test results")
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing test results: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_result(self):
        """Get the most recent test result."""
        session = self.Session()
        try:
            return session.query(TestResult).order_by(TestResult.timestamp.desc()).first()
        except Exception as e:
            logger.error(f"Error fetching latest result: {e}")
            raise
        finally:
            session.close()
    
    def get_results_by_type(self, test_type):
        """Get test results filtered by test type."""
        session = self.Session()
        try:
            return session.query(TestResult).filter_by(test_type=test_type).order_by(TestResult.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching results by type: {e}")
            raise
        finally:
            session.close()
    
    def get_results_by_status(self, status):
        """Get test results filtered by status."""
        session = self.Session()
        try:
            return session.query(TestResult).filter_by(status=status).order_by(TestResult.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching results by status: {e}")
            raise
        finally:
            session.close()
    
    def get_results_by_date_range(self, start_date, end_date):
        """Get test results within a date range."""
        session = self.Session()
        try:
            return session.query(TestResult).filter(
                TestResult.timestamp >= start_date,
                TestResult.timestamp <= end_date
            ).order_by(TestResult.timestamp.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching results by date range: {e}")
            raise
        finally:
            session.close()
    
    def get_statistics(self):
        """Get test execution statistics."""
        session = self.Session()
        try:
            total = session.query(TestResult).count()
            passed = session.query(TestResult).filter_by(status="passed").count()
            failed = session.query(TestResult).filter_by(status="failed").count()
            skipped = session.query(TestResult).filter_by(status="skipped").count()
            
            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": (passed / total * 100) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            raise
        finally:
            session.close()
    
    def cleanup_old_results(self, days=30):
        """Clean up test results older than specified days."""
        session = self.Session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            old_results = session.query(TestResult).filter(TestResult.timestamp < cutoff_date).all()
            
            for result in old_results:
                # Delete associated report files if they exist
                if result.report_path and os.path.exists(result.report_path):
                    try:
                        os.remove(result.report_path)
                        logger.info(f"Deleted report file: {result.report_path}")
                    except Exception as e:
                        logger.warning(f"Error deleting report file {result.report_path}: {e}")
                
                session.delete(result)
            
            session.commit()
            logger.info(f"Cleaned up {len(old_results)} old test results")
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old results: {e}")
            raise
        finally:
            session.close()
    
    def __del__(self):
        """Cleanup when the database manager is destroyed."""
        try:
            self.Session.remove()
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")