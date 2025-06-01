#!/usr/bin/env python3
"""
Django REST Framework API for ATM Status Counts - Option 3

A robust, enterprise-grade REST API using Django REST Framework with
comprehensive authentication, permissions, and data management features.

Features:
- Django ORM models for type safety and validation
- Built-in admin interface for data management
- User authentication and permissions
- Serializers for data validation and transformation
- Pagination and filtering
- Comprehensive error handling
- Built-in API documentation with DRF browsable API
- Throttling and rate limiting
- Database migrations and model management

Endpoints:
- GET /api/v1/atm/status/summary/ - Overall ATM status summary
- GET /api/v1/atm/status/regional/ - Regional breakdown with filters
- GET /api/v1/atm/status/trends/ - Historical trends analysis
- GET /api/v1/atm/status/latest/ - Latest data from all tables
- GET /api/v1/health/ - API health check
- GET /admin/ - Django admin interface
- GET /api/ - Browsable API documentation

Installation:
pip install django djangorestframework psycopg2-binary django-cors-headers django-filter

Setup:
1. Create Django project: django-admin startproject atm_api
2. Add this as an app: python manage.py startapp atm_status
3. Configure settings.py with database and installed apps
4. Run migrations: python manage.py migrate
5. Create superuser: python manage.py createsuperuser
6. Run server: python manage.py runserver

Author: ATM Monitoring System
Created: 2025-01-30
"""

# Django imports
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Django REST Framework imports
from rest_framework import viewsets, serializers, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

# Standard library imports
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='django-insecure-atm-api-key-for-development-only',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'atm_monitor'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
                'HOST': os.getenv('DB_HOST', 'localhost'),
                'PORT': os.getenv('DB_PORT', '5432'),
            }
        },
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'django_filters',
            'corsheaders',
            '__main__',  # This module as an app
        ],
        MIDDLEWARE=[
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        ROOT_URLCONF=__name__,
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework.authentication.SessionAuthentication',
                'rest_framework.authentication.TokenAuthentication',
            ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticatedOrReadOnly',
            ],
            'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
            'PAGE_SIZE': 50,
            'DEFAULT_FILTER_BACKENDS': [
                'django_filters.rest_framework.DjangoFilterBackend',
                'rest_framework.filters.SearchFilter',
                'rest_framework.filters.OrderingFilter',
            ],
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle'
            ],
            'DEFAULT_THROTTLE_RATES': {
                'anon': '100/hour',
                'user': '1000/hour'
            }
        },
        CORS_ALLOW_ALL_ORIGINS=True,  # Configure appropriately for production
        STATIC_URL='/static/',
        USE_TZ=True,
        TIME_ZONE='UTC',
    )

import django
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('atm_django_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ATM_Django_API')

# Django Models
class RegionalATMCounts(models.Model):
    """Model for legacy regional_atm_counts table"""
    
    class Meta:
        db_table = 'regional_atm_counts'
        managed = False  # Don't let Django manage this table
        ordering = ['-date_creation']
    
    unique_request_id = models.UUIDField(primary_key=True)
    region_code = models.CharField(max_length=10)
    count_available = models.IntegerField(default=0)
    count_warning = models.IntegerField(default=0)
    count_zombie = models.IntegerField(default=0)
    count_wounded = models.IntegerField(default=0)
    count_out_of_service = models.IntegerField(default=0)
    date_creation = models.DateTimeField()
    total_atms_in_region = models.IntegerField(null=True, blank=True)
    percentage_available = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    percentage_warning = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    percentage_zombie = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    percentage_wounded = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    percentage_out_of_service = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)

    def __str__(self):
        return f"{self.region_code} - {self.date_creation}"

    @property
    def total_count(self):
        """Calculate total ATM count"""
        return (self.count_available + self.count_warning + self.count_zombie + 
                self.count_wounded + self.count_out_of_service)

    @property
    def availability_percentage(self):
        """Calculate availability percentage"""
        if self.total_atms_in_region and self.total_atms_in_region > 0:
            return round((self.count_available / self.total_atms_in_region) * 100, 2)
        return 0

    @property
    def health_status(self):
        """Determine health status based on availability"""
        availability = self.availability_percentage
        if availability >= 85:
            return 'HEALTHY'
        elif availability >= 70:
            return 'ATTENTION'
        elif availability >= 50:
            return 'WARNING'
        else:
            return 'CRITICAL'

class RegionalData(models.Model):
    """Model for new regional_data table with JSONB support"""
    
    class Meta:
        db_table = 'regional_data'
        managed = False  # Don't let Django manage this table
        ordering = ['-retrieval_timestamp']
    
    id = models.AutoField(primary_key=True)
    unique_request_id = models.UUIDField()
    region_code = models.CharField(max_length=10)
    retrieval_timestamp = models.DateTimeField()
    raw_regional_data = models.JSONField()
    count_available = models.IntegerField(null=True, blank=True)
    count_warning = models.IntegerField(null=True, blank=True)
    count_zombie = models.IntegerField(null=True, blank=True)
    count_wounded = models.IntegerField(null=True, blank=True)
    count_out_of_service = models.IntegerField(null=True, blank=True)
    total_atms_in_region = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.region_code} - {self.retrieval_timestamp}"

class TerminalDetails(models.Model):
    """Model for terminal_details table"""
    
    class Meta:
        db_table = 'terminal_details'
        managed = False  # Don't let Django manage this table
        ordering = ['-retrieved_date']
    
    id = models.AutoField(primary_key=True)
    unique_request_id = models.UUIDField()
    terminal_id = models.CharField(max_length=50)
    location = models.TextField(null=True, blank=True)
    issue_state_name = models.CharField(max_length=50, null=True, blank=True)
    serial_number = models.CharField(max_length=50, null=True, blank=True)
    retrieved_date = models.DateTimeField()
    fetched_status = models.CharField(max_length=50)
    raw_terminal_data = models.JSONField()
    fault_data = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.terminal_id} - {self.fetched_status}"

# Serializers
class ATMStatusCountsSerializer(serializers.Serializer):
    """Serializer for ATM status counts"""
    available = serializers.IntegerField(min_value=0)
    warning = serializers.IntegerField(min_value=0)
    zombie = serializers.IntegerField(min_value=0)
    wounded = serializers.IntegerField(min_value=0)
    out_of_service = serializers.IntegerField(min_value=0)
    total = serializers.IntegerField(min_value=0)

class RegionalATMCountsSerializer(serializers.ModelSerializer):
    """Serializer for RegionalATMCounts model"""
    availability_percentage = serializers.ReadOnlyField()
    health_status = serializers.ReadOnlyField()
    total_count = serializers.ReadOnlyField()
    
    class Meta:
        model = RegionalATMCounts
        fields = '__all__'

class RegionalDataSerializer(serializers.ModelSerializer):
    """Serializer for RegionalData model"""
    
    class Meta:
        model = RegionalData
        fields = '__all__'

class TerminalDetailsSerializer(serializers.ModelSerializer):
    """Serializer for TerminalDetails model"""
    
    class Meta:
        model = TerminalDetails
        fields = '__all__'

class ATMSummarySerializer(serializers.Serializer):
    """Serializer for ATM summary response"""
    total_atms = serializers.IntegerField(min_value=0)
    status_counts = ATMStatusCountsSerializer()
    overall_availability = serializers.FloatField(min_value=0, max_value=100)
    total_regions = serializers.IntegerField(min_value=0)
    last_updated = serializers.DateTimeField()
    data_source = serializers.CharField()

class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response"""
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    database_connected = serializers.BooleanField()
    api_version = serializers.CharField()
    django_version = serializers.CharField()

# Filters
class RegionalATMCountsFilter(django_filters.FilterSet):
    """Filter for RegionalATMCounts"""
    region_code = django_filters.CharFilter(lookup_expr='icontains')
    date_creation_after = django_filters.DateTimeFilter(field_name='date_creation', lookup_expr='gte')
    date_creation_before = django_filters.DateTimeFilter(field_name='date_creation', lookup_expr='lte')
    availability_min = django_filters.NumberFilter(method='filter_availability_min')
    availability_max = django_filters.NumberFilter(method='filter_availability_max')
    
    class Meta:
        model = RegionalATMCounts
        fields = ['region_code', 'date_creation_after', 'date_creation_before']
    
    def filter_availability_min(self, queryset, name, value):
        """Filter by minimum availability percentage"""
        # This would need custom SQL for calculated field
        return queryset
    
    def filter_availability_max(self, queryset, name, value):
        """Filter by maximum availability percentage"""
        # This would need custom SQL for calculated field
        return queryset

# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

# ViewSets
class RegionalATMCountsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RegionalATMCounts"""
    queryset = RegionalATMCounts.objects.all()
    serializer_class = RegionalATMCountsSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RegionalATMCountsFilter
    search_fields = ['region_code']
    ordering_fields = ['date_creation', 'region_code', 'count_available']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def latest_by_region(self, request):
        """Get latest data for each region"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT ON (region_code)
                        unique_request_id, region_code, count_available, count_warning,
                        count_zombie, count_wounded, count_out_of_service,
                        total_atms_in_region, date_creation
                    FROM regional_atm_counts
                    ORDER BY region_code, date_creation DESC
                """)
                
                results = []
                for row in cursor.fetchall():
                    available = row[2] or 0
                    total = row[6] or 0
                    availability_pct = (available / total * 100) if total > 0 else 0
                    
                    results.append({
                        'unique_request_id': str(row[0]),
                        'region_code': row[1],
                        'count_available': available,
                        'count_warning': row[3] or 0,
                        'count_zombie': row[4] or 0,
                        'count_wounded': row[5] or 0,
                        'count_out_of_service': row[6] or 0,
                        'total_atms_in_region': total,
                        'date_creation': row[8],
                        'availability_percentage': round(availability_pct, 2),
                        'health_status': self._calculate_health_status(availability_pct)
                    })
                
                return Response({
                    'success': True,
                    'data': results,
                    'count': len(results),
                    'timestamp': timezone.now()
                })
                
        except Exception as e:
            logger.error(f"Error fetching latest regional data: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_health_status(self, availability_percentage):
        """Calculate health status"""
        if availability_percentage >= 85:
            return 'HEALTHY'
        elif availability_percentage >= 70:
            return 'ATTENTION'
        elif availability_percentage >= 50:
            return 'WARNING'
        else:
            return 'CRITICAL'

class RegionalDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for RegionalData (new JSONB table)"""
    queryset = RegionalData.objects.all()
    serializer_class = RegionalDataSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['region_code']
    ordering_fields = ['retrieval_timestamp', 'region_code']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class TerminalDetailsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TerminalDetails"""
    queryset = TerminalDetails.objects.all()
    serializer_class = TerminalDetailsSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['terminal_id', 'location', 'serial_number', 'fetched_status']
    ordering_fields = ['retrieved_date', 'terminal_id', 'fetched_status']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# API Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """API health check endpoint"""
    try:
        # Test database connection
        from django.db import connection
        db_connected = False
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_connected = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
        
        health_data = {
            'status': 'healthy' if db_connected else 'degraded',
            'timestamp': timezone.now(),
            'database_connected': db_connected,
            'api_version': '3.0.0',
            'django_version': django.get_version()
        }
        
        serializer = HealthCheckSerializer(health_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def atm_summary(request):
    """Get overall ATM status summary"""
    try:
        table_type = request.GET.get('table_type', 'legacy')
        
        from django.db import connection
        with connection.cursor() as cursor:
            if table_type == 'legacy':
                cursor.execute("""
                    WITH latest_data AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            date_creation
                        FROM regional_atm_counts
                        ORDER BY region_code, date_creation DESC
                    )
                    SELECT 
                        SUM(count_available) as total_available,
                        SUM(count_warning) as total_warning,
                        SUM(count_zombie) as total_zombie,
                        SUM(count_wounded) as total_wounded,
                        SUM(count_out_of_service) as total_out_of_service,
                        SUM(total_atms_in_region) as total_atms,
                        COUNT(DISTINCT region_code) as total_regions,
                        MAX(date_creation) as last_updated
                    FROM latest_data
                """)
            else:
                cursor.execute("""
                    WITH latest_data AS (
                        SELECT DISTINCT ON (region_code)
                            region_code, count_available, count_warning, count_zombie,
                            count_wounded, count_out_of_service, total_atms_in_region,
                            retrieval_timestamp
                        FROM regional_data
                        ORDER BY region_code, retrieval_timestamp DESC
                    )
                    SELECT 
                        SUM(count_available) as total_available,
                        SUM(count_warning) as total_warning,
                        SUM(count_zombie) as total_zombie,
                        SUM(count_wounded) as total_wounded,
                        SUM(count_out_of_service) as total_out_of_service,
                        SUM(total_atms_in_region) as total_atms,
                        COUNT(DISTINCT region_code) as total_regions,
                        MAX(retrieval_timestamp) as last_updated
                    FROM latest_data
                """)
            
            row = cursor.fetchone()
            
            if not row or row[5] is None:
                return Response(
                    {'success': False, 'error': 'No ATM data found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            total_atms = row[5] or 0
            available = row[0] or 0
            availability_percentage = (available / total_atms * 100) if total_atms > 0 else 0
            
            summary_data = {
                'total_atms': total_atms,
                'status_counts': {
                    'available': available,
                    'warning': row[1] or 0,
                    'zombie': row[2] or 0,
                    'wounded': row[3] or 0,
                    'out_of_service': row[4] or 0,
                    'total': total_atms
                },
                'overall_availability': round(availability_percentage, 2),
                'total_regions': row[6] or 0,
                'last_updated': row[7] or timezone.now(),
                'data_source': table_type
            }
            
            serializer = ATMSummarySerializer(summary_data)
            return Response({
                'success': True,
                'data': serializer.data,
                'timestamp': timezone.now()
            })
            
    except Exception as e:
        logger.error(f"Error fetching ATM summary: {e}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def regional_trends(request):
    """Get regional trends data"""
    try:
        region_code = request.GET.get('region_code')
        hours = int(request.GET.get('hours', 24))
        table_type = request.GET.get('table_type', 'legacy')
        
        if not region_code:
            return Response(
                {'success': False, 'error': 'region_code parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.db import connection
        with connection.cursor() as cursor:
            if table_type == 'legacy':
                cursor.execute("""
                    SELECT 
                        date_creation, count_available, count_warning, count_zombie,
                        count_wounded, count_out_of_service, total_atms_in_region
                    FROM regional_atm_counts
                    WHERE region_code = %s 
                        AND date_creation >= NOW() - INTERVAL '%s hours'
                    ORDER BY date_creation ASC
                """, [region_code, hours])
            else:
                cursor.execute("""
                    SELECT 
                        retrieval_timestamp, count_available, count_warning, 
                        count_zombie, count_wounded, count_out_of_service, 
                        total_atms_in_region
                    FROM regional_data
                    WHERE region_code = %s 
                        AND retrieval_timestamp >= NOW() - INTERVAL '%s hours'
                    ORDER BY retrieval_timestamp ASC
                """, [region_code, hours])
            
            rows = cursor.fetchall()
            
            if not rows:
                return Response(
                    {'success': False, 'error': f'No trend data found for region {region_code}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            trends = []
            availability_values = []
            
            for row in rows:
                available = row[1] or 0
                total = row[6] or 0
                availability_pct = (available / total * 100) if total > 0 else 0
                availability_values.append(availability_pct)
                
                trends.append({
                    'timestamp': row[0],
                    'status_counts': {
                        'available': available,
                        'warning': row[2] or 0,
                        'zombie': row[3] or 0,
                        'wounded': row[4] or 0,
                        'out_of_service': row[5] or 0,
                        'total': total
                    },
                    'availability_percentage': round(availability_pct, 2)
                })
            
            summary_stats = {
                'data_points': len(trends),
                'time_range_hours': hours,
                'avg_availability': round(sum(availability_values) / len(availability_values), 2) if availability_values else 0,
                'min_availability': round(min(availability_values), 2) if availability_values else 0,
                'max_availability': round(max(availability_values), 2) if availability_values else 0,
                'first_reading': trends[0]['timestamp'] if trends else None,
                'last_reading': trends[-1]['timestamp'] if trends else None
            }
            
            return Response({
                'success': True,
                'data': {
                    'region_code': region_code,
                    'time_period': f"{hours} hours",
                    'trends': trends,
                    'summary_stats': summary_stats
                },
                'timestamp': timezone.now()
            })
            
    except Exception as e:
        logger.error(f"Error fetching trends for region {region_code}: {e}")
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Admin configuration
admin.site.register(RegionalATMCounts, list_display=['region_code', 'date_creation', 'count_available', 'total_atms_in_region'])
admin.site.register(RegionalData, list_display=['region_code', 'retrieval_timestamp', 'count_available'])
admin.site.register(TerminalDetails, list_display=['terminal_id', 'fetched_status', 'retrieved_date'])

# URL Configuration
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'legacy/regional-counts', RegionalATMCountsViewSet)
router.register(r'new/regional-data', RegionalDataViewSet)
router.register(r'terminal-details', TerminalDetailsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/atm/status/summary/', atm_summary, name='atm_summary'),
    path('api/v1/atm/status/trends/', regional_trends, name='regional_trends'),
    path('api-auth/', include('rest_framework.urls')),
]

# WSGI Application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

if __name__ == "__main__":
    import sys
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
