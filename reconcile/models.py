from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class ReconciliationConfig(models.Model):
    """Configuration for reconciliation fields and matching criteria"""
    name = models.CharField(max_length=100, default="Default Config")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Config {self.id} - {self.name}"


class ReconciliationField(models.Model):
    """Field configuration for reconciliation"""
    DATA_TYPE_CHOICES = [
        ('string', 'String'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
    ]
    
    config = models.ForeignKey(ReconciliationConfig, on_delete=models.CASCADE, related_name='fields')
    field_code = models.CharField(max_length=1)  # A, B, C, etc.
    field_name = models.CharField(max_length=50)  # Nomor Jurnal
    display_name = models.CharField(max_length=100)  # Display name
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, default='string')
    is_matching_criteria = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['config', 'field_code']
    
    def __str__(self):
        return f"{self.field_code}: {self.field_name}"


class ReconciliationSession(models.Model):
    """Session for each reconciliation process"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    config = models.ForeignKey(ReconciliationConfig, on_delete=models.CASCADE)
    file_a_name = models.CharField(max_length=255)
    file_b_name = models.CharField(max_length=255)
    file_a_path = models.CharField(max_length=500)
    file_b_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_records_a = models.IntegerField(default=0)
    total_records_b = models.IntegerField(default=0)
    matched_count = models.IntegerField(default=0)
    only_a_count = models.IntegerField(default=0)
    only_b_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.id} - {self.created_at}"


class ReconciliationResult(models.Model):
    """Individual reconciliation results"""
    STATUS_CHOICES = [
        ('match', 'MATCH'),
        ('only_a', 'ONLY_FILE_A'),
        ('only_b', 'ONLY_FILE_B'),
    ]
    
    session = models.ForeignKey(ReconciliationSession, on_delete=models.CASCADE, related_name='results')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    file_a_data = models.JSONField(default=dict)  # Store all field values from file A
    file_b_data = models.JSONField(default=dict)  # Store all field values from file B
    match_key = models.CharField(max_length=500, db_index=True)  # Combined matching key for performance
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['match_key']),
        ]
    
    def __str__(self):
        return f"Result {self.id} - {self.status}"