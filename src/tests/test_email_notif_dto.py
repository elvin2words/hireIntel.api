import pytest
from datetime import datetime
from marshmallow import ValidationError
from src.Modules.Notification.NotificationDTOs import EmailNotificationDTO

# Test data
valid_data = {
    'candidate_id': '123',
    'email_type': 'accepted',
    'subject': 'Welcome!',
    'content': 'This is your welcome email.',
    'sent_at': datetime.utcnow(),
    'status': 'sent',
}

invalid_data = {
    'candidate_id': '123',
    'email_type': 'invalid_type',  # invalid email_type
    'subject': 'Welcome!',
    'content': 'This is your welcome email.',
    'sent_at': datetime.utcnow(),
    'status': 'sent',
}

# Test validation for valid data
def test_valid_email_notification_dto():
    dto = EmailNotificationDTO()
    result = dto.load(valid_data)  # Deserialization (validation happens here)
    # Ensure no validation errors
    assert result.errors == {}
    assert result.data['candidate_id'] == '123'
    assert result.data['email_type'] == 'accepted'
    assert result.data['status'] == 'sent'

# Test validation for invalid email_type
def test_invalid_email_type():
    dto = EmailNotificationDTO()
    with pytest.raises(ValidationError):
        dto.load(invalid_data)  # This should raise a validation error due to invalid email_type

# Test date formatting in serialization
def test_sent_at_date_formatting():
    dto = EmailNotificationDTO()
    valid_data['sent_at'] = datetime(2025, 2, 24, 12, 0, 0)  # Setting a fixed datetime
    result = dto.dump(valid_data)  # Serialization (post_dump hook is applied here)
    # Check that the sent_at field is formatted correctly
    assert 'sent_at' in result
    assert result['sent_at'] == '2025-02-24 12:00:00'

# Test missing required fields
def test_missing_required_fields():
    dto = EmailNotificationDTO()
    invalid_data_missing_fields = valid_data.copy()
    invalid_data_missing_fields.pop('email_type')  # Remove email_type
    with pytest.raises(ValidationError):
        dto.load(invalid_data_missing_fields)  # Should raise validation error for missing email_type
