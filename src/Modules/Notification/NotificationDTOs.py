from marshmallow import fields, validate, post_dump

from src.Helpers.Utils import CamelCaseSchema
from src.Modules.Candidate.CandidateDTOs import CandidateDTO


## Data Transfer Object (DTO) for handling email notifications 
#  inherits camelCase serialization behavior
class EmailNotificationDTO(CamelCaseSchema):
        
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(required=True, validate=validate.Length(min=1, error="Candidate ID must not be empty."))
    email_type = fields.Str(required=True, validate=validate.OneOf(['accepted', 'rejected'], error="Invalid email type. Must be 'accepted' or 'rejected'."))
    subject = fields.Str(required=True, validate=validate.Length(min=1, max=255), error="Subject must be between 1 and 255 characters.")
    content = fields.Str(required=True, validate=validate.Length(min=1), error="Content must not be empty.")
    sent_at = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True, validate=validate.OneOf(['pending', 'sent', 'failed'], error="Status must be one of 'pending', 'sent', or 'failed'."), default='pending')

    # Include related data
    candidate = fields.Nested(CandidateDTO, dump_only=True)
    
    @post_dump
    def format_sent_at(self, data, **kwargs):
        """
        Format the sent_at datetime field to string format YYYY-MM-DD HH:MM:SS after serialization before return
        """
        if 'sent_at' in data and data['sent_at']:
            # Format the datetime to a string
            data['sent_at'] = data['sent_at'].strftime('%Y-%m-%d %H:%M:%S')
        return data
    
    class Meta:
        # Automatically convert field names to camelCase for consistency
        ordered = True  # Ensures fields are serialized in the defined order
        
        
        
        
