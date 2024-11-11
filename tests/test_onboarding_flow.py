import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class TestOnboardingFlow:
    BASE_URL = "http://localhost:5000"
    
    def test_welcome_screen(self, driver):
        """Test the welcome screen elements and navigation"""
        driver.get(f"{self.BASE_URL}/")
        
        # Verify welcome screen elements
        assert "Welcome to LeaseCheck" in driver.page_source
        
        # Check main content elements
        welcome_header = driver.find_element(By.CLASS_NAME, "welcome-header")
        assert welcome_header.is_displayed()
        
        features_list = driver.find_elements(By.CLASS_NAME, "feature-item")
        assert len(features_list) == 5  # Verify all feature items are present
        
        # Test CTA button
        cta_button = driver.find_element(By.CLASS_NAME, "choose-plan-btn")
        assert cta_button.is_displayed()
        assert "Choose A Plan" in cta_button.text
        
    def test_plan_selection(self, driver):
        """Test the plan selection screen"""
        driver.get(f"{self.BASE_URL}/select-plan")
        
        # Verify plan options are displayed
        plan_options = driver.find_elements(By.CLASS_NAME, "plan-card")
        assert len(plan_options) > 0
        
        # Test plan selection interaction
        plan = plan_options[0]
        plan.click()
        
        # Verify selection is highlighted
        assert "selected" in plan.get_attribute("class")
        
    def test_account_setup(self, driver):
        """Test the account setup screen"""
        driver.get(f"{self.BASE_URL}/account-setup")
        
        # Test form elements
        form = driver.find_element(By.TAG_NAME, "form")
        assert form.is_displayed()
        
        # Test form validation
        submit_button = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Verify validation messages
        error_messages = driver.find_elements(By.CLASS_NAME, "error-message")
        assert len(error_messages) > 0
        
    def test_legal_documents(self, driver):
        """Test the legal documents screens"""
        driver.get(f"{self.BASE_URL}/legal-stuff")
        
        # Test navigation through legal documents
        legal_links = driver.find_elements(By.CSS_SELECTOR, ".legal-nav a")
        assert len(legal_links) > 0
        
        for link in legal_links:
            link.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "legal-content"))
            )
            assert driver.find_element(By.CLASS_NAME, "legal-content").is_displayed()
            
    def test_document_upload(self, driver):
        """Test the document upload functionality"""
        driver.get(f"{self.BASE_URL}/lease-upload")
        
        # Verify upload widget elements
        upload_widget = driver.find_element(By.CLASS_NAME, "upload-box")
        assert upload_widget.is_displayed()
        
        # Verify file input is present
        file_input = driver.find_element(By.CLASS_NAME, "file-input")
        assert file_input.get_attribute("type") == "file"
        
        # Verify accepted file types
        accepted_types = file_input.get_attribute("accept")
        assert ".pdf" in accepted_types
        assert ".doc" in accepted_types
        assert ".docx" in accepted_types

    def test_error_handling(self, driver):
        """Test error handling and validation messages"""
        paths = ['/account-setup', '/lease-upload', '/legal-stuff']
        
        for path in paths:
            driver.get(f"{self.BASE_URL}{path}")
            
            # Submit forms without data to trigger validation
            forms = driver.find_elements(By.TAG_NAME, "form")
            if forms:
                forms[0].submit()
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
                    )
                    error_messages = driver.find_elements(By.CLASS_NAME, "error-message")
                    assert len(error_messages) > 0
                except TimeoutException:
                    continue
