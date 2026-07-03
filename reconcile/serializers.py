from rest_framework import serializers
from .models import (
    ReconciliationConfig, ReconciliationField, FieldMapping,
    ReconciliationRule, ReconciliationSession, ReconciliationResult
)


class ReconciliationFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationField
        fields = '__all__'


class FieldMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldMapping
        fields = '__all__'


class ReconciliationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationRule
        fields = '__all__'


class ReconciliationConfigSerializer(serializers.ModelSerializer):
    fields = ReconciliationFieldSerializer(many=True, read_only=True)
    mappings = FieldMappingSerializer(many=True, read_only=True)
    rules = ReconciliationRuleSerializer(many=True, read_only=True)
    fields_count = serializers.SerializerMethodField()
    sessions_count = serializers.SerializerMethodField()

    class Meta:
        model = ReconciliationConfig
        fields = '__all__'

    def get_fields_count(self, obj):
        return obj.fields.count()

    def get_sessions_count(self, obj):
        return obj.reconciliationsession_set.count()


class ReconciliationConfigWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationConfig
        fields = '__all__'


class ReconciliationSessionSerializer(serializers.ModelSerializer):
    config_name = serializers.CharField(source='config.name', read_only=True)
    match_rate = serializers.SerializerMethodField()
    results_count = serializers.SerializerMethodField()

    class Meta:
        model = ReconciliationSession
        fields = '__all__'

    def get_match_rate(self, obj):
        if obj.total_a > 0:
            return round((obj.matched / obj.total_a) * 100, 2)
        return 0

    def get_results_count(self, obj):
        return obj.results.count()


class ReconciliationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationResult
        fields = '__all__'


class BulkConfigSerializer(serializers.Serializer):
    config_name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    fields = serializers.ListField(
        child=serializers.DictField()
    )
    matching_fields = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class ReconcileSerializer(serializers.Serializer):
    config_id = serializers.IntegerField()
    file_a = serializers.FileField()
    file_b = serializers.FileField()
