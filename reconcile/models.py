from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models


class ReconciliationConfig(models.Model):
    """
    Master configuration.
    Example:
        - PPN vs Pembukuan
        - Bank Statement
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ReconciliationField(models.Model):
    """
    System field definition.
    Example:
        DPP
        No Faktur
        Tanggal
        PPN
    """

    DATA_TYPES = [
        ("string", "String"),
        ("number", "Number"),
        ("date", "Date"),
    ]

    config = models.ForeignKey(
        ReconciliationConfig,
        on_delete=models.CASCADE,
        related_name="fields"
    )

    field_name = models.CharField(max_length=100)

    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPES,
        default="string"
    )

    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sequence"]

    def __str__(self):
        return self.field_name


class FieldMapping(models.Model):
    """
    Mapping Excel column -> System Field
    """

    FILE_TYPES = [
        ("A", "File A"),
        ("B", "File B"),
    ]

    config = models.ForeignKey(
        ReconciliationConfig,
        on_delete=models.CASCADE,
        related_name="mappings"
    )

    field = models.ForeignKey(
        ReconciliationField,
        on_delete=models.CASCADE
    )

    file_type = models.CharField(
        max_length=1,
        choices=FILE_TYPES
    )

    excel_column = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.file_type} - {self.field.field_name}"


class ReconciliationRule(models.Model):
    """
    Matching Rule
    """

    OPERATORS = [
        ("=", "Equal"),
    ]

    config = models.ForeignKey(
        ReconciliationConfig,
        on_delete=models.CASCADE,
        related_name="rules"
    )

    left_field = models.ForeignKey(
        FieldMapping,
        on_delete=models.CASCADE,
        related_name="left_rules"
    )

    right_field = models.ForeignKey(
        FieldMapping,
        on_delete=models.CASCADE,
        related_name="right_rules"
    )

    operator = models.CharField(
        max_length=5,
        choices=OPERATORS,
        default="="
    )

    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sequence"]


class ReconciliationSession(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    config = models.ForeignKey(
        ReconciliationConfig,
        on_delete=models.CASCADE
    )

    file_a_path = models.CharField(max_length=500)  # Changed from file_a
    file_b_path = models.CharField(max_length=500)  # Changed from file_b
    file_a_name = models.CharField(max_length=255, blank=True)  # Added for display
    file_b_name = models.CharField(max_length=255, blank=True)  # Added for display

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    total_a = models.IntegerField(default=0)
    total_b = models.IntegerField(default=0)

    matched = models.IntegerField(default=0)
    only_a = models.IntegerField(default=0)
    only_b = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)  # Added for error handling

    def __str__(self):
        return f"Session {self.id} - {self.config.name}"


class ReconciliationResult(models.Model):

    STATUS = [

        ("MATCH", "MATCH"),
        ("ONLY_A", "ONLY FILE A"),
        ("ONLY_B", "ONLY FILE B"),
    ]

    session = models.ForeignKey(
        ReconciliationSession,
        on_delete=models.CASCADE,
        related_name="results"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS
    )

    row_a = models.IntegerField(null=True)

    row_b = models.IntegerField(null=True)

    match_key = models.CharField(
        max_length=300,
        db_index=True
    )

    file_a_data = models.JSONField(default=dict)

    file_b_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)