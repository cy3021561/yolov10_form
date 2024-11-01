from typing import List, Tuple, Optional, Any
from datetime import datetime
import re

class EMRData:
    """
    EMR data container with all optional fields
    """
    def __init__(self,
                 # Personal Information
                 person_last_name: Optional[str] = None,
                 person_first_name: Optional[str] = None,
                 person_birth_date: Optional[str] = None,
                 person_sex: Optional[str] = None,
                 person_ssn: Optional[str] = None,
                 
                 # Provider Information
                 provider_last_name: Optional[str] = None,
                 provider_first_name: Optional[str] = None,
                 
                 # Contact Information
                 contact_address_line1: Optional[str] = None,
                 contact_address_line2: Optional[str] = None,
                 contact_city: Optional[str] = None,
                 contact_state: Optional[str] = None,
                 contact_zip: Optional[str] = None,
                 contact_phone: Optional[str] = None,
                 contact_email: Optional[str] = None,
                 
                 # Insurance Information
                 insurance_primary_type: Optional[str] = None,
                 insurance_primary_company: Optional[str] = None,
                 insurance_primary_relationship: Optional[str] = None,
                 insurance_primary_subscriber_id: Optional[str] = None,
                 insurance_secondary_type: Optional[str] = None,
                 insurance_secondary_company: Optional[str] = None,
                 insurance_secondary_relationship: Optional[str] = None,
                 insurance_secondary_subscriber_id: Optional[str] = None,
                 
                 # Clinical Information
                 clinical_icd10_codes: Optional[List[str]] = None,
                 clinical_cpt_codes: Optional[List[Tuple[str, str]]] = None,
                 
                 # Billing Information
                 billing_facility: Optional[str] = None,
                 billing_provider: Optional[str] = None,
                 billing_service_date: Optional[str] = None):

        # Initialize all fields
        self.person_last_name = person_last_name
        self.person_first_name = person_first_name
        self.person_birth_date = person_birth_date
        self.person_sex = person_sex
        self.person_ssn = person_ssn
        self.provider_last_name = provider_last_name
        self.provider_first_name = provider_first_name
        self.contact_address_line1 = contact_address_line1
        self.contact_address_line2 = contact_address_line2
        self.contact_city = contact_city
        self.contact_state = contact_state
        self.contact_zip = contact_zip
        self.contact_phone = contact_phone
        self.contact_email = contact_email
        self.insurance_primary_type = insurance_primary_type
        self.insurance_primary_company = insurance_primary_company
        self.insurance_primary_relationship = insurance_primary_relationship
        self.insurance_primary_subscriber_id = insurance_primary_subscriber_id
        self.insurance_secondary_type = insurance_secondary_type
        self.insurance_secondary_company = insurance_secondary_company
        self.insurance_secondary_relationship = insurance_secondary_relationship
        self.insurance_secondary_subscriber_id = insurance_secondary_subscriber_id
        self.clinical_icd10_codes = clinical_icd10_codes or []
        self.clinical_cpt_codes = clinical_cpt_codes or []
        self.billing_facility = billing_facility
        self.billing_provider = billing_provider
        self.billing_service_date = billing_service_date


    def _validate(self) -> List[str]:
        """
        Validate only provided fields
        Returns list of validation errors
        """
        errors = []

        # Validate only if value is provided
        if not self.billing_service_date or not self.billing_service_date.strip():
            self.billing_service_date = datetime.now().strftime('%m%d%Y')

        if not re.match(r'^\d{8}$', self.billing_service_date):
            errors.append("Billing service date must be in MMDDYYYY format")

        if self.person_sex and self.person_sex not in ['Male', 'Female']:
            errors.append("Sex must be either 'Male' or 'Female'")

        if self.person_ssn and not re.match(r'^\d{9}$', self.person_ssn):
            errors.append("SSN must be 9 digits")

        if self.contact_zip and not re.match(r'^\d{5}$', self.contact_zip):
            errors.append("ZIP code must be 5 digits")

        if self.contact_phone and not re.match(r'^\d{10}$', self.contact_phone):
            errors.append("Phone must be 10 digits")

        if self.contact_email and not re.match(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 
            self.contact_email
        ):
            errors.append("Invalid email format")

        if self.insurance_primary_relationship and \
           self.insurance_primary_relationship not in ['Self', 'Spouse', 'Child', 'Other']:
            errors.append("Invalid primary insurance relationship")

        if self.insurance_secondary_relationship and \
           self.insurance_secondary_relationship not in ['Self', 'Spouse', 'Child', 'Other']:
            errors.append("Invalid secondary insurance relationship")

        if self.clinical_icd10_codes:
            if not all(isinstance(code, str) and len(code) == 4 for code in self.clinical_icd10_codes):
                errors.append("ICD10 codes must be 4-character strings")

        if self.clinical_cpt_codes:
            if not all(isinstance(code, tuple) and len(code) == 2 for code in self.clinical_cpt_codes):
                errors.append("CPT codes must be (code, modifier) tuples")

        return errors

    def validate(self) -> bool:
        """
        Validate all provided fields
        Returns True if valid, raises ValueError if invalid
        """
        errors = self._validate()
        if errors:
            raise ValueError("\n".join(errors))
        return True

    def get_value(self, field_name: str, default: Any = None) -> Any:
        """Get value of a field"""
        return getattr(self, field_name, default)

    def has_value(self, field_name: str) -> bool:
        """Check if field has a non-None value"""
        value = self.get_value(field_name)
        if isinstance(value, (list, tuple)):
            return bool(value)  # Return True if list/tuple is non-empty
        return value is not None and value != ""

    def update(self, new_data: dict) -> None:
        """
        Update with new values, keeping existing ones if not provided
        """
        for field_name, new_value in new_data.items():
            if hasattr(self, field_name):
                if new_value is not None:  # Update only if value is provided
                    setattr(self, field_name, new_value)
        
        # Validate after update
        self.validate()
