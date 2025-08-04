import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter/material.dart';

part 'atm_model.freezed.dart';
part 'atm_model.g.dart';

@freezed
class AtmSummary with _$AtmSummary {
  const factory AtmSummary({
    @JsonKey(name: 'total_atms') required int totalAtms,
    @JsonKey(name: 'status_counts') required StatusCounts statusCounts,
    @JsonKey(name: 'overall_availability') required double overallAvailability,
    @JsonKey(name: 'last_updated') required DateTime lastUpdated,
  }) = _AtmSummary;

  factory AtmSummary.fromJson(Map<String, dynamic> json) => _$AtmSummaryFromJson(json);
}

@freezed
class StatusCounts with _$StatusCounts {
  const factory StatusCounts({
    required int available,
    required int warning,
    required int wounded,
    required int zombie,
    @JsonKey(name: 'out_of_service') required int outOfService,
  }) = _StatusCounts;

  factory StatusCounts.fromJson(Map<String, dynamic> json) => _$StatusCountsFromJson(json);
}

@freezed
class AtmTerminal with _$AtmTerminal {
  const factory AtmTerminal({
    @JsonKey(name: 'terminal_id') required String terminalId,
    @JsonKey(name: 'external_id') required String externalId,
    required String location,
    @JsonKey(name: 'location_str') required String locationStr,
    String? city,
    String? region,
    String? bank,
    String? brand,
    String? model,
    @JsonKey(name: 'issue_state_name') required String issueStateName,
    required String status,
    @JsonKey(name: 'fetched_status') required String fetchedStatus,
    @JsonKey(name: 'serial_number') String? serialNumber,
    @JsonKey(name: 'retrieved_date') required DateTime retrievedDate,
    @JsonKey(name: 'last_updated') required DateTime lastUpdated,
    @JsonKey(name: 'fault_data') String? faultData,
    String? metadata,
  }) = _AtmTerminal;

  factory AtmTerminal.fromJson(Map<String, dynamic> json) => _$AtmTerminalFromJson(json);
}

extension AtmTerminalExtension on AtmTerminal {
  String get displayStatus {
    switch (status.toLowerCase()) {
      case 'available':
        return 'Online';
      case 'warning':
        return 'Maintenance';
      case 'wounded':
      case 'zombie':
        return 'Offline';
      case 'out_of_service':
        return 'Out of Service';
      default:
        return status;
    }
  }

  Color get statusColor {
    switch (status.toLowerCase()) {
      case 'available':
        return const Color(0xFF10B981); // Green
      case 'warning':
        return const Color(0xFFF59E0B); // Orange
      case 'wounded':
      case 'zombie':
        return const Color(0xFFEF4444); // Red
      case 'out_of_service':
        return const Color(0xFF6B7280); // Gray
      default:
        return const Color(0xFF6B7280);
    }
  }

  IconData get statusIcon {
    switch (status.toLowerCase()) {
      case 'available':
        return Icons.check_circle;
      case 'warning':
        return Icons.warning;
      case 'wounded':
      case 'zombie':
        return Icons.error;
      case 'out_of_service':
        return Icons.block;
      default:
        return Icons.help;
    }
  }
}

@freezed
class RegionalData with _$RegionalData {
  const factory RegionalData({
    @JsonKey(name: 'region_code') required String regionCode,
    @JsonKey(name: 'status_counts') required StatusCounts statusCounts,
    @JsonKey(name: 'availability_percentage') required double availabilityPercentage,
  }) = _RegionalData;

  factory RegionalData.fromJson(Map<String, dynamic> json) => _$RegionalDataFromJson(json);
}

@freezed
class CashInfo with _$CashInfo {
  const factory CashInfo({
    @JsonKey(name: 'terminal_id') required String terminalId,
    required String location,
    @JsonKey(name: 'total_cash') required double totalCash,
    @JsonKey(name: 'cash_level_percentage') required double cashLevelPercentage,
    @JsonKey(name: 'last_refill') DateTime? lastRefill,
    @JsonKey(name: 'estimated_days_remaining') int? estimatedDaysRemaining,
    @JsonKey(name: 'denominations') Map<String, int>? denominations,
  }) = _CashInfo;

  factory CashInfo.fromJson(Map<String, dynamic> json) => _$CashInfoFromJson(json);
}
