"""
Sample functional tests demonstrating application functionality testing.
"""
import pytest
import json
import os
from datetime import datetime

class TestCalculator:
    """Test calculator functionality."""
    
    def test_addition(self):
        """Test addition operation."""
        assert 5 + 3 == 8
        assert 0.1 + 0.2 == pytest.approx(0.3)  # Handle floating point
        assert -1 + 1 == 0
    
    def test_subtraction(self):
        """Test subtraction operation."""
        assert 10 - 5 == 5
        assert 5 - 10 == -5
        assert 0 - 0 == 0
    
    def test_multiplication(self):
        """Test multiplication operation."""
        assert 4 * 3 == 12
        assert -2 * 3 == -6
        assert 0 * 5 == 0
    
    def test_division(self):
        """Test division operation."""
        assert 10 / 2 == 5
        assert 5 / 2 == 2.5
        with pytest.raises(ZeroDivisionError):
            5 / 0

class TestFileOperations:
    """Test file operations functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_file = "test_data.json"
        self.test_data = {
            "name": "Test User",
            "age": 30,
            "timestamp": datetime.now().isoformat()
        }
    
    def teardown_method(self):
        """Cleanup test environment."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_file_write_read(self):
        """Test writing and reading from a file."""
        # Write data
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f)
        
        # Verify file exists
        assert os.path.exists(self.test_file)
        
        # Read data
        with open(self.test_file, 'r') as f:
            loaded_data = json.load(f)
        
        # Verify data
        assert loaded_data["name"] == self.test_data["name"]
        assert loaded_data["age"] == self.test_data["age"]
    
    def test_file_append(self):
        """Test appending to a file."""
        # Write initial data
        with open(self.test_file, 'w') as f:
            f.write("Line 1\n")
        
        # Append data
        with open(self.test_file, 'a') as f:
            f.write("Line 2\n")
        
        # Read and verify
        with open(self.test_file, 'r') as f:
            content = f.read()
        
        assert "Line 1" in content
        assert "Line 2" in content
        assert content.count("\n") == 2

class TestDataValidation:
    """Test data validation functionality."""
    
    def test_email_validation(self):
        """Test email address validation."""
        def is_valid_email(email):
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        
        # Valid emails
        assert is_valid_email("user@example.com")
        assert is_valid_email("user.name@domain.co.uk")
        assert is_valid_email("user+tag@example.com")
        
        # Invalid emails
        assert not is_valid_email("invalid.email")
        assert not is_valid_email("user@.com")
        assert not is_valid_email("@domain.com")
    
    def test_password_strength(self):
        """Test password strength validation."""
        def check_password_strength(password):
            if len(password) < 8:
                return False
            if not any(c.isupper() for c in password):
                return False
            if not any(c.islower() for c in password):
                return False
            if not any(c.isdigit() for c in password):
                return False
            return True
        
        # Strong passwords
        assert check_password_strength("StrongP@ss123")
        assert check_password_strength("Complex!Pass1")
        
        # Weak passwords
        assert not check_password_strength("weak")
        assert not check_password_strength("NoNumbers!")
        assert not check_password_strength("no-upper-1")
        assert not check_password_strength("NO-LOWER-1") 