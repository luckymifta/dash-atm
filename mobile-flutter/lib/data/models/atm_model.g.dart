// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'atm_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AtmSummaryImpl _$$AtmSummaryImplFromJson(Map<String, dynamic> json) =>
    _$AtmSummaryImpl(
      totalAtms: (json['total_atms'] as num).toInt(),
      statusCounts:
          StatusCounts.fromJson(json['status_counts'] as Map<String, dynamic>),
      overallAvailability: (json['overall_availability'] as num).toDouble(),
      lastUpdated: DateTime.parse(json['last_updated'] as String),
    );

Map<String, dynamic> _$$AtmSummaryImplToJson(_$AtmSummaryImpl instance) =>
    <String, dynamic>{
      'total_atms': instance.totalAtms,
      'status_counts': instance.statusCounts,
      'overall_availability': instance.overallAvailability,
      'last_updated': instance.lastUpdated.toIso8601String(),
    };

_$StatusCountsImpl _$$StatusCountsImplFromJson(Map<String, dynamic> json) =>
    _$StatusCountsImpl(
      available: (json['available'] as num).toInt(),
      warning: (json['warning'] as num).toInt(),
      wounded: (json['wounded'] as num).toInt(),
      zombie: (json['zombie'] as num).toInt(),
      outOfService: (json['out_of_service'] as num).toInt(),
    );

Map<String, dynamic> _$$StatusCountsImplToJson(_$StatusCountsImpl instance) =>
    <String, dynamic>{
      'available': instance.available,
      'warning': instance.warning,
      'wounded': instance.wounded,
      'zombie': instance.zombie,
      'out_of_service': instance.outOfService,
    };

_$AtmTerminalImpl _$$AtmTerminalImplFromJson(Map<String, dynamic> json) =>
    _$AtmTerminalImpl(
      terminalId: json['terminal_id'] as String,
      externalId: json['external_id'] as String,
      location: json['location'] as String,
      locationStr: json['location_str'] as String,
      city: json['city'] as String?,
      region: json['region'] as String?,
      bank: json['bank'] as String?,
      brand: json['brand'] as String?,
      model: json['model'] as String?,
      issueStateName: json['issue_state_name'] as String,
      status: json['status'] as String,
      fetchedStatus: json['fetched_status'] as String,
      serialNumber: json['serial_number'] as String?,
      retrievedDate: DateTime.parse(json['retrieved_date'] as String),
      lastUpdated: DateTime.parse(json['last_updated'] as String),
      faultData: json['fault_data'] as String?,
      metadata: json['metadata'] as String?,
    );

Map<String, dynamic> _$$AtmTerminalImplToJson(_$AtmTerminalImpl instance) =>
    <String, dynamic>{
      'terminal_id': instance.terminalId,
      'external_id': instance.externalId,
      'location': instance.location,
      'location_str': instance.locationStr,
      'city': instance.city,
      'region': instance.region,
      'bank': instance.bank,
      'brand': instance.brand,
      'model': instance.model,
      'issue_state_name': instance.issueStateName,
      'status': instance.status,
      'fetched_status': instance.fetchedStatus,
      'serial_number': instance.serialNumber,
      'retrieved_date': instance.retrievedDate.toIso8601String(),
      'last_updated': instance.lastUpdated.toIso8601String(),
      'fault_data': instance.faultData,
      'metadata': instance.metadata,
    };

_$RegionalDataImpl _$$RegionalDataImplFromJson(Map<String, dynamic> json) =>
    _$RegionalDataImpl(
      regionCode: json['region_code'] as String,
      statusCounts:
          StatusCounts.fromJson(json['status_counts'] as Map<String, dynamic>),
      availabilityPercentage:
          (json['availability_percentage'] as num).toDouble(),
    );

Map<String, dynamic> _$$RegionalDataImplToJson(_$RegionalDataImpl instance) =>
    <String, dynamic>{
      'region_code': instance.regionCode,
      'status_counts': instance.statusCounts,
      'availability_percentage': instance.availabilityPercentage,
    };

_$CashInfoImpl _$$CashInfoImplFromJson(Map<String, dynamic> json) =>
    _$CashInfoImpl(
      terminalId: json['terminal_id'] as String,
      location: json['location'] as String,
      totalCash: (json['total_cash'] as num).toDouble(),
      cashLevelPercentage: (json['cash_level_percentage'] as num).toDouble(),
      lastRefill: json['last_refill'] == null
          ? null
          : DateTime.parse(json['last_refill'] as String),
      estimatedDaysRemaining:
          (json['estimated_days_remaining'] as num?)?.toInt(),
      denominations: (json['denominations'] as Map<String, dynamic>?)?.map(
        (k, e) => MapEntry(k, (e as num).toInt()),
      ),
    );

Map<String, dynamic> _$$CashInfoImplToJson(_$CashInfoImpl instance) =>
    <String, dynamic>{
      'terminal_id': instance.terminalId,
      'location': instance.location,
      'total_cash': instance.totalCash,
      'cash_level_percentage': instance.cashLevelPercentage,
      'last_refill': instance.lastRefill?.toIso8601String(),
      'estimated_days_remaining': instance.estimatedDaysRemaining,
      'denominations': instance.denominations,
    };
