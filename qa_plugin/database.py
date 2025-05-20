from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

Base = declarative_base()

class TestResult(Base):
    __tablename__ = 'test_results'
    id = Column(Integer, primary_key=True)
    test_type = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    name = Column(String)

class QADatabase:
    """Database handler for test results."""
    
    def __init__(self, db_path: str = "qa_results.db"):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_result(self, test_type: str, status: str, name: Optional[str] = None) -> None:
        """Save a test result to the database.
        
        Args:
            test_type: Type of test (unit, e2e, sample, custom)
            status: Test status (pass, fail)
            name: Optional test name or identifier
        """
        with self.Session() as session:
            try:
                result = TestResult(
                    test_type=test_type,
                    status=status,
                    name=name,
                    timestamp=datetime.utcnow()
                )
                session.add(result)
                session.commit()
            except Exception as e:
                session.rollback()
                raise Exception(f"Error saving test result: {str(e)}")
    
    def get_results(self, limit: Optional[int] = None, test_type: Optional[str] = None) -> List[TestResult]:
        """Get test results from the database with optional filtering."""
        with self.Session() as session:
            try:
                query = session.query(TestResult)
                
                # Apply filters if provided
                if test_type and test_type != "all":
                    query = query.filter(TestResult.test_type == test_type)
                
                # Order by timestamp descending (newest first)
                query = query.order_by(TestResult.timestamp.desc())
                
                # Apply limit if provided
                if limit:
                    query = query.limit(limit)
                
                return query.all()
            except Exception as e:
                raise Exception(f"Error retrieving test results: {str(e)}")
    
    def get_result_by_id(self, result_id: int) -> Optional[TestResult]:
        """Get a specific test result by ID."""
        with self.Session() as session:
            try:
                return session.query(TestResult).filter(TestResult.id == result_id).first()
            except Exception as e:
                raise Exception(f"Error retrieving test result: {str(e)}")
    
    def clear_results(self) -> None:
        """Clear all test results from the database."""
        with self.Session() as session:
            try:
                session.query(TestResult).delete()
                session.commit()
            except Exception as e:
                session.rollback()
                raise Exception(f"Error clearing test results: {str(e)}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get a summary of test results."""
        with self.Session() as session:
            try:
                total = session.query(TestResult).count()
                passed = session.query(TestResult).filter(TestResult.status == "pass").count()
                failed = session.query(TestResult).filter(TestResult.status == "fail").count()
                
                # Get results by test type
                type_counts = {}
                for test_type in ["unit", "e2e", "sample", "custom"]:
                    count = session.query(TestResult).filter(TestResult.test_type == test_type).count()
                    type_counts[test_type] = count
                
                return {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "by_type": type_counts,
                    "pass_rate": (passed / total * 100) if total > 0 else 0
                }
            except Exception as e:
                raise Exception(f"Error getting test summary: {str(e)}")
    
    def get_recent_results(self, days: int = 7) -> List[TestResult]:
        """Get test results from the last N days."""
        with self.Session() as session:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                return session.query(TestResult)\
                    .filter(TestResult.timestamp >= cutoff_date)\
                    .order_by(TestResult.timestamp.desc())\
                    .all()
            except Exception as e:
                raise Exception(f"Error retrieving recent test results: {str(e)}")
    
    def get_test_history(self, test_name: Optional[str] = None) -> List[TestResult]:
        """Get history of a specific test or all tests."""
        with self.Session() as session:
            try:
                query = session.query(TestResult)
                if test_name:
                    query = query.filter(TestResult.name == test_name)
                return query.order_by(TestResult.timestamp.desc()).all()
            except Exception as e:
                raise Exception(f"Error retrieving test history: {str(e)}")