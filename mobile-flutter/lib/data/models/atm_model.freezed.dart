// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'atm_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

AtmSummary _$AtmSummaryFromJson(Map<String, dynamic> json) {
  return _AtmSummary.fromJson(json);
}

/// @nodoc
mixin _$AtmSummary {
  @JsonKey(name: 'total_atms')
  int get totalAtms => throw _privateConstructorUsedError;
  @JsonKey(name: 'status_counts')
  StatusCounts get statusCounts => throw _privateConstructorUsedError;
  @JsonKey(name: 'overall_availability')
  double get overallAvailability => throw _privateConstructorUsedError;
  @JsonKey(name: 'last_updated')
  DateTime get lastUpdated => throw _privateConstructorUsedError;

  /// Serializes this AtmSummary to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AtmSummaryCopyWith<AtmSummary> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AtmSummaryCopyWith<$Res> {
  factory $AtmSummaryCopyWith(
          AtmSummary value, $Res Function(AtmSummary) then) =
      _$AtmSummaryCopyWithImpl<$Res, AtmSummary>;
  @useResult
  $Res call(
      {@JsonKey(name: 'total_atms') int totalAtms,
      @JsonKey(name: 'status_counts') StatusCounts statusCounts,
      @JsonKey(name: 'overall_availability') double overallAvailability,
      @JsonKey(name: 'last_updated') DateTime lastUpdated});

  $StatusCountsCopyWith<$Res> get statusCounts;
}

/// @nodoc
class _$AtmSummaryCopyWithImpl<$Res, $Val extends AtmSummary>
    implements $AtmSummaryCopyWith<$Res> {
  _$AtmSummaryCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalAtms = null,
    Object? statusCounts = null,
    Object? overallAvailability = null,
    Object? lastUpdated = null,
  }) {
    return _then(_value.copyWith(
      totalAtms: null == totalAtms
          ? _value.totalAtms
          : totalAtms // ignore: cast_nullable_to_non_nullable
              as int,
      statusCounts: null == statusCounts
          ? _value.statusCounts
          : statusCounts // ignore: cast_nullable_to_non_nullable
              as StatusCounts,
      overallAvailability: null == overallAvailability
          ? _value.overallAvailability
          : overallAvailability // ignore: cast_nullable_to_non_nullable
              as double,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $StatusCountsCopyWith<$Res> get statusCounts {
    return $StatusCountsCopyWith<$Res>(_value.statusCounts, (value) {
      return _then(_value.copyWith(statusCounts: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AtmSummaryImplCopyWith<$Res>
    implements $AtmSummaryCopyWith<$Res> {
  factory _$$AtmSummaryImplCopyWith(
          _$AtmSummaryImpl value, $Res Function(_$AtmSummaryImpl) then) =
      __$$AtmSummaryImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'total_atms') int totalAtms,
      @JsonKey(name: 'status_counts') StatusCounts statusCounts,
      @JsonKey(name: 'overall_availability') double overallAvailability,
      @JsonKey(name: 'last_updated') DateTime lastUpdated});

  @override
  $StatusCountsCopyWith<$Res> get statusCounts;
}

/// @nodoc
class __$$AtmSummaryImplCopyWithImpl<$Res>
    extends _$AtmSummaryCopyWithImpl<$Res, _$AtmSummaryImpl>
    implements _$$AtmSummaryImplCopyWith<$Res> {
  __$$AtmSummaryImplCopyWithImpl(
      _$AtmSummaryImpl _value, $Res Function(_$AtmSummaryImpl) _then)
      : super(_value, _then);

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalAtms = null,
    Object? statusCounts = null,
    Object? overallAvailability = null,
    Object? lastUpdated = null,
  }) {
    return _then(_$AtmSummaryImpl(
      totalAtms: null == totalAtms
          ? _value.totalAtms
          : totalAtms // ignore: cast_nullable_to_non_nullable
              as int,
      statusCounts: null == statusCounts
          ? _value.statusCounts
          : statusCounts // ignore: cast_nullable_to_non_nullable
              as StatusCounts,
      overallAvailability: null == overallAvailability
          ? _value.overallAvailability
          : overallAvailability // ignore: cast_nullable_to_non_nullable
              as double,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AtmSummaryImpl implements _AtmSummary {
  const _$AtmSummaryImpl(
      {@JsonKey(name: 'total_atms') required this.totalAtms,
      @JsonKey(name: 'status_counts') required this.statusCounts,
      @JsonKey(name: 'overall_availability') required this.overallAvailability,
      @JsonKey(name: 'last_updated') required this.lastUpdated});

  factory _$AtmSummaryImpl.fromJson(Map<String, dynamic> json) =>
      _$$AtmSummaryImplFromJson(json);

  @override
  @JsonKey(name: 'total_atms')
  final int totalAtms;
  @override
  @JsonKey(name: 'status_counts')
  final StatusCounts statusCounts;
  @override
  @JsonKey(name: 'overall_availability')
  final double overallAvailability;
  @override
  @JsonKey(name: 'last_updated')
  final DateTime lastUpdated;

  @override
  String toString() {
    return 'AtmSummary(totalAtms: $totalAtms, statusCounts: $statusCounts, overallAvailability: $overallAvailability, lastUpdated: $lastUpdated)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AtmSummaryImpl &&
            (identical(other.totalAtms, totalAtms) ||
                other.totalAtms == totalAtms) &&
            (identical(other.statusCounts, statusCounts) ||
                other.statusCounts == statusCounts) &&
            (identical(other.overallAvailability, overallAvailability) ||
                other.overallAvailability == overallAvailability) &&
            (identical(other.lastUpdated, lastUpdated) ||
                other.lastUpdated == lastUpdated));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, totalAtms, statusCounts, overallAvailability, lastUpdated);

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AtmSummaryImplCopyWith<_$AtmSummaryImpl> get copyWith =>
      __$$AtmSummaryImplCopyWithImpl<_$AtmSummaryImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AtmSummaryImplToJson(
      this,
    );
  }
}

abstract class _AtmSummary implements AtmSummary {
  const factory _AtmSummary(
      {@JsonKey(name: 'total_atms') required final int totalAtms,
      @JsonKey(name: 'status_counts') required final StatusCounts statusCounts,
      @JsonKey(name: 'overall_availability')
      required final double overallAvailability,
      @JsonKey(name: 'last_updated')
      required final DateTime lastUpdated}) = _$AtmSummaryImpl;

  factory _AtmSummary.fromJson(Map<String, dynamic> json) =
      _$AtmSummaryImpl.fromJson;

  @override
  @JsonKey(name: 'total_atms')
  int get totalAtms;
  @override
  @JsonKey(name: 'status_counts')
  StatusCounts get statusCounts;
  @override
  @JsonKey(name: 'overall_availability')
  double get overallAvailability;
  @override
  @JsonKey(name: 'last_updated')
  DateTime get lastUpdated;

  /// Create a copy of AtmSummary
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AtmSummaryImplCopyWith<_$AtmSummaryImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StatusCounts _$StatusCountsFromJson(Map<String, dynamic> json) {
  return _StatusCounts.fromJson(json);
}

/// @nodoc
mixin _$StatusCounts {
  int get available => throw _privateConstructorUsedError;
  int get warning => throw _privateConstructorUsedError;
  int get wounded => throw _privateConstructorUsedError;
  int get zombie => throw _privateConstructorUsedError;
  @JsonKey(name: 'out_of_service')
  int get outOfService => throw _privateConstructorUsedError;

  /// Serializes this StatusCounts to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of StatusCounts
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $StatusCountsCopyWith<StatusCounts> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StatusCountsCopyWith<$Res> {
  factory $StatusCountsCopyWith(
          StatusCounts value, $Res Function(StatusCounts) then) =
      _$StatusCountsCopyWithImpl<$Res, StatusCounts>;
  @useResult
  $Res call(
      {int available,
      int warning,
      int wounded,
      int zombie,
      @JsonKey(name: 'out_of_service') int outOfService});
}

/// @nodoc
class _$StatusCountsCopyWithImpl<$Res, $Val extends StatusCounts>
    implements $StatusCountsCopyWith<$Res> {
  _$StatusCountsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of StatusCounts
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? available = null,
    Object? warning = null,
    Object? wounded = null,
    Object? zombie = null,
    Object? outOfService = null,
  }) {
    return _then(_value.copyWith(
      available: null == available
          ? _value.available
          : available // ignore: cast_nullable_to_non_nullable
              as int,
      warning: null == warning
          ? _value.warning
          : warning // ignore: cast_nullable_to_non_nullable
              as int,
      wounded: null == wounded
          ? _value.wounded
          : wounded // ignore: cast_nullable_to_non_nullable
              as int,
      zombie: null == zombie
          ? _value.zombie
          : zombie // ignore: cast_nullable_to_non_nullable
              as int,
      outOfService: null == outOfService
          ? _value.outOfService
          : outOfService // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$StatusCountsImplCopyWith<$Res>
    implements $StatusCountsCopyWith<$Res> {
  factory _$$StatusCountsImplCopyWith(
          _$StatusCountsImpl value, $Res Function(_$StatusCountsImpl) then) =
      __$$StatusCountsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int available,
      int warning,
      int wounded,
      int zombie,
      @JsonKey(name: 'out_of_service') int outOfService});
}

/// @nodoc
class __$$StatusCountsImplCopyWithImpl<$Res>
    extends _$StatusCountsCopyWithImpl<$Res, _$StatusCountsImpl>
    implements _$$StatusCountsImplCopyWith<$Res> {
  __$$StatusCountsImplCopyWithImpl(
      _$StatusCountsImpl _value, $Res Function(_$StatusCountsImpl) _then)
      : super(_value, _then);

  /// Create a copy of StatusCounts
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? available = null,
    Object? warning = null,
    Object? wounded = null,
    Object? zombie = null,
    Object? outOfService = null,
  }) {
    return _then(_$StatusCountsImpl(
      available: null == available
          ? _value.available
          : available // ignore: cast_nullable_to_non_nullable
              as int,
      warning: null == warning
          ? _value.warning
          : warning // ignore: cast_nullable_to_non_nullable
              as int,
      wounded: null == wounded
          ? _value.wounded
          : wounded // ignore: cast_nullable_to_non_nullable
              as int,
      zombie: null == zombie
          ? _value.zombie
          : zombie // ignore: cast_nullable_to_non_nullable
              as int,
      outOfService: null == outOfService
          ? _value.outOfService
          : outOfService // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StatusCountsImpl implements _StatusCounts {
  const _$StatusCountsImpl(
      {required this.available,
      required this.warning,
      required this.wounded,
      required this.zombie,
      @JsonKey(name: 'out_of_service') required this.outOfService});

  factory _$StatusCountsImpl.fromJson(Map<String, dynamic> json) =>
      _$$StatusCountsImplFromJson(json);

  @override
  final int available;
  @override
  final int warning;
  @override
  final int wounded;
  @override
  final int zombie;
  @override
  @JsonKey(name: 'out_of_service')
  final int outOfService;

  @override
  String toString() {
    return 'StatusCounts(available: $available, warning: $warning, wounded: $wounded, zombie: $zombie, outOfService: $outOfService)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StatusCountsImpl &&
            (identical(other.available, available) ||
                other.available == available) &&
            (identical(other.warning, warning) || other.warning == warning) &&
            (identical(other.wounded, wounded) || other.wounded == wounded) &&
            (identical(other.zombie, zombie) || other.zombie == zombie) &&
            (identical(other.outOfService, outOfService) ||
                other.outOfService == outOfService));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, available, warning, wounded, zombie, outOfService);

  /// Create a copy of StatusCounts
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$StatusCountsImplCopyWith<_$StatusCountsImpl> get copyWith =>
      __$$StatusCountsImplCopyWithImpl<_$StatusCountsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StatusCountsImplToJson(
      this,
    );
  }
}

abstract class _StatusCounts implements StatusCounts {
  const factory _StatusCounts(
          {required final int available,
          required final int warning,
          required final int wounded,
          required final int zombie,
          @JsonKey(name: 'out_of_service') required final int outOfService}) =
      _$StatusCountsImpl;

  factory _StatusCounts.fromJson(Map<String, dynamic> json) =
      _$StatusCountsImpl.fromJson;

  @override
  int get available;
  @override
  int get warning;
  @override
  int get wounded;
  @override
  int get zombie;
  @override
  @JsonKey(name: 'out_of_service')
  int get outOfService;

  /// Create a copy of StatusCounts
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$StatusCountsImplCopyWith<_$StatusCountsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

AtmTerminal _$AtmTerminalFromJson(Map<String, dynamic> json) {
  return _AtmTerminal.fromJson(json);
}

/// @nodoc
mixin _$AtmTerminal {
  @JsonKey(name: 'terminal_id')
  String get terminalId => throw _privateConstructorUsedError;
  @JsonKey(name: 'external_id')
  String get externalId => throw _privateConstructorUsedError;
  String get location => throw _privateConstructorUsedError;
  @JsonKey(name: 'location_str')
  String get locationStr => throw _privateConstructorUsedError;
  String? get city => throw _privateConstructorUsedError;
  String? get region => throw _privateConstructorUsedError;
  String? get bank => throw _privateConstructorUsedError;
  String? get brand => throw _privateConstructorUsedError;
  String? get model => throw _privateConstructorUsedError;
  @JsonKey(name: 'issue_state_name')
  String get issueStateName => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  @JsonKey(name: 'fetched_status')
  String get fetchedStatus => throw _privateConstructorUsedError;
  @JsonKey(name: 'serial_number')
  String? get serialNumber => throw _privateConstructorUsedError;
  @JsonKey(name: 'retrieved_date')
  DateTime get retrievedDate => throw _privateConstructorUsedError;
  @JsonKey(name: 'last_updated')
  DateTime get lastUpdated => throw _privateConstructorUsedError;
  @JsonKey(name: 'fault_data')
  String? get faultData => throw _privateConstructorUsedError;
  String? get metadata => throw _privateConstructorUsedError;

  /// Serializes this AtmTerminal to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of AtmTerminal
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AtmTerminalCopyWith<AtmTerminal> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AtmTerminalCopyWith<$Res> {
  factory $AtmTerminalCopyWith(
          AtmTerminal value, $Res Function(AtmTerminal) then) =
      _$AtmTerminalCopyWithImpl<$Res, AtmTerminal>;
  @useResult
  $Res call(
      {@JsonKey(name: 'terminal_id') String terminalId,
      @JsonKey(name: 'external_id') String externalId,
      String location,
      @JsonKey(name: 'location_str') String locationStr,
      String? city,
      String? region,
      String? bank,
      String? brand,
      String? model,
      @JsonKey(name: 'issue_state_name') String issueStateName,
      String status,
      @JsonKey(name: 'fetched_status') String fetchedStatus,
      @JsonKey(name: 'serial_number') String? serialNumber,
      @JsonKey(name: 'retrieved_date') DateTime retrievedDate,
      @JsonKey(name: 'last_updated') DateTime lastUpdated,
      @JsonKey(name: 'fault_data') String? faultData,
      String? metadata});
}

/// @nodoc
class _$AtmTerminalCopyWithImpl<$Res, $Val extends AtmTerminal>
    implements $AtmTerminalCopyWith<$Res> {
  _$AtmTerminalCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AtmTerminal
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? terminalId = null,
    Object? externalId = null,
    Object? location = null,
    Object? locationStr = null,
    Object? city = freezed,
    Object? region = freezed,
    Object? bank = freezed,
    Object? brand = freezed,
    Object? model = freezed,
    Object? issueStateName = null,
    Object? status = null,
    Object? fetchedStatus = null,
    Object? serialNumber = freezed,
    Object? retrievedDate = null,
    Object? lastUpdated = null,
    Object? faultData = freezed,
    Object? metadata = freezed,
  }) {
    return _then(_value.copyWith(
      terminalId: null == terminalId
          ? _value.terminalId
          : terminalId // ignore: cast_nullable_to_non_nullable
              as String,
      externalId: null == externalId
          ? _value.externalId
          : externalId // ignore: cast_nullable_to_non_nullable
              as String,
      location: null == location
          ? _value.location
          : location // ignore: cast_nullable_to_non_nullable
              as String,
      locationStr: null == locationStr
          ? _value.locationStr
          : locationStr // ignore: cast_nullable_to_non_nullable
              as String,
      city: freezed == city
          ? _value.city
          : city // ignore: cast_nullable_to_non_nullable
              as String?,
      region: freezed == region
          ? _value.region
          : region // ignore: cast_nullable_to_non_nullable
              as String?,
      bank: freezed == bank
          ? _value.bank
          : bank // ignore: cast_nullable_to_non_nullable
              as String?,
      brand: freezed == brand
          ? _value.brand
          : brand // ignore: cast_nullable_to_non_nullable
              as String?,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      issueStateName: null == issueStateName
          ? _value.issueStateName
          : issueStateName // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      fetchedStatus: null == fetchedStatus
          ? _value.fetchedStatus
          : fetchedStatus // ignore: cast_nullable_to_non_nullable
              as String,
      serialNumber: freezed == serialNumber
          ? _value.serialNumber
          : serialNumber // ignore: cast_nullable_to_non_nullable
              as String?,
      retrievedDate: null == retrievedDate
          ? _value.retrievedDate
          : retrievedDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
      faultData: freezed == faultData
          ? _value.faultData
          : faultData // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AtmTerminalImplCopyWith<$Res>
    implements $AtmTerminalCopyWith<$Res> {
  factory _$$AtmTerminalImplCopyWith(
          _$AtmTerminalImpl value, $Res Function(_$AtmTerminalImpl) then) =
      __$$AtmTerminalImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'terminal_id') String terminalId,
      @JsonKey(name: 'external_id') String externalId,
      String location,
      @JsonKey(name: 'location_str') String locationStr,
      String? city,
      String? region,
      String? bank,
      String? brand,
      String? model,
      @JsonKey(name: 'issue_state_name') String issueStateName,
      String status,
      @JsonKey(name: 'fetched_status') String fetchedStatus,
      @JsonKey(name: 'serial_number') String? serialNumber,
      @JsonKey(name: 'retrieved_date') DateTime retrievedDate,
      @JsonKey(name: 'last_updated') DateTime lastUpdated,
      @JsonKey(name: 'fault_data') String? faultData,
      String? metadata});
}

/// @nodoc
class __$$AtmTerminalImplCopyWithImpl<$Res>
    extends _$AtmTerminalCopyWithImpl<$Res, _$AtmTerminalImpl>
    implements _$$AtmTerminalImplCopyWith<$Res> {
  __$$AtmTerminalImplCopyWithImpl(
      _$AtmTerminalImpl _value, $Res Function(_$AtmTerminalImpl) _then)
      : super(_value, _then);

  /// Create a copy of AtmTerminal
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? terminalId = null,
    Object? externalId = null,
    Object? location = null,
    Object? locationStr = null,
    Object? city = freezed,
    Object? region = freezed,
    Object? bank = freezed,
    Object? brand = freezed,
    Object? model = freezed,
    Object? issueStateName = null,
    Object? status = null,
    Object? fetchedStatus = null,
    Object? serialNumber = freezed,
    Object? retrievedDate = null,
    Object? lastUpdated = null,
    Object? faultData = freezed,
    Object? metadata = freezed,
  }) {
    return _then(_$AtmTerminalImpl(
      terminalId: null == terminalId
          ? _value.terminalId
          : terminalId // ignore: cast_nullable_to_non_nullable
              as String,
      externalId: null == externalId
          ? _value.externalId
          : externalId // ignore: cast_nullable_to_non_nullable
              as String,
      location: null == location
          ? _value.location
          : location // ignore: cast_nullable_to_non_nullable
              as String,
      locationStr: null == locationStr
          ? _value.locationStr
          : locationStr // ignore: cast_nullable_to_non_nullable
              as String,
      city: freezed == city
          ? _value.city
          : city // ignore: cast_nullable_to_non_nullable
              as String?,
      region: freezed == region
          ? _value.region
          : region // ignore: cast_nullable_to_non_nullable
              as String?,
      bank: freezed == bank
          ? _value.bank
          : bank // ignore: cast_nullable_to_non_nullable
              as String?,
      brand: freezed == brand
          ? _value.brand
          : brand // ignore: cast_nullable_to_non_nullable
              as String?,
      model: freezed == model
          ? _value.model
          : model // ignore: cast_nullable_to_non_nullable
              as String?,
      issueStateName: null == issueStateName
          ? _value.issueStateName
          : issueStateName // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      fetchedStatus: null == fetchedStatus
          ? _value.fetchedStatus
          : fetchedStatus // ignore: cast_nullable_to_non_nullable
              as String,
      serialNumber: freezed == serialNumber
          ? _value.serialNumber
          : serialNumber // ignore: cast_nullable_to_non_nullable
              as String?,
      retrievedDate: null == retrievedDate
          ? _value.retrievedDate
          : retrievedDate // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastUpdated: null == lastUpdated
          ? _value.lastUpdated
          : lastUpdated // ignore: cast_nullable_to_non_nullable
              as DateTime,
      faultData: freezed == faultData
          ? _value.faultData
          : faultData // ignore: cast_nullable_to_non_nullable
              as String?,
      metadata: freezed == metadata
          ? _value.metadata
          : metadata // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AtmTerminalImpl implements _AtmTerminal {
  const _$AtmTerminalImpl(
      {@JsonKey(name: 'terminal_id') required this.terminalId,
      @JsonKey(name: 'external_id') required this.externalId,
      required this.location,
      @JsonKey(name: 'location_str') required this.locationStr,
      this.city,
      this.region,
      this.bank,
      this.brand,
      this.model,
      @JsonKey(name: 'issue_state_name') required this.issueStateName,
      required this.status,
      @JsonKey(name: 'fetched_status') required this.fetchedStatus,
      @JsonKey(name: 'serial_number') this.serialNumber,
      @JsonKey(name: 'retrieved_date') required this.retrievedDate,
      @JsonKey(name: 'last_updated') required this.lastUpdated,
      @JsonKey(name: 'fault_data') this.faultData,
      this.metadata});

  factory _$AtmTerminalImpl.fromJson(Map<String, dynamic> json) =>
      _$$AtmTerminalImplFromJson(json);

  @override
  @JsonKey(name: 'terminal_id')
  final String terminalId;
  @override
  @JsonKey(name: 'external_id')
  final String externalId;
  @override
  final String location;
  @override
  @JsonKey(name: 'location_str')
  final String locationStr;
  @override
  final String? city;
  @override
  final String? region;
  @override
  final String? bank;
  @override
  final String? brand;
  @override
  final String? model;
  @override
  @JsonKey(name: 'issue_state_name')
  final String issueStateName;
  @override
  final String status;
  @override
  @JsonKey(name: 'fetched_status')
  final String fetchedStatus;
  @override
  @JsonKey(name: 'serial_number')
  final String? serialNumber;
  @override
  @JsonKey(name: 'retrieved_date')
  final DateTime retrievedDate;
  @override
  @JsonKey(name: 'last_updated')
  final DateTime lastUpdated;
  @override
  @JsonKey(name: 'fault_data')
  final String? faultData;
  @override
  final String? metadata;

  @override
  String toString() {
    return 'AtmTerminal(terminalId: $terminalId, externalId: $externalId, location: $location, locationStr: $locationStr, city: $city, region: $region, bank: $bank, brand: $brand, model: $model, issueStateName: $issueStateName, status: $status, fetchedStatus: $fetchedStatus, serialNumber: $serialNumber, retrievedDate: $retrievedDate, lastUpdated: $lastUpdated, faultData: $faultData, metadata: $metadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AtmTerminalImpl &&
            (identical(other.terminalId, terminalId) ||
                other.terminalId == terminalId) &&
            (identical(other.externalId, externalId) ||
                other.externalId == externalId) &&
            (identical(other.location, location) ||
                other.location == location) &&
            (identical(other.locationStr, locationStr) ||
                other.locationStr == locationStr) &&
            (identical(other.city, city) || other.city == city) &&
            (identical(other.region, region) || other.region == region) &&
            (identical(other.bank, bank) || other.bank == bank) &&
            (identical(other.brand, brand) || other.brand == brand) &&
            (identical(other.model, model) || other.model == model) &&
            (identical(other.issueStateName, issueStateName) ||
                other.issueStateName == issueStateName) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.fetchedStatus, fetchedStatus) ||
                other.fetchedStatus == fetchedStatus) &&
            (identical(other.serialNumber, serialNumber) ||
                other.serialNumber == serialNumber) &&
            (identical(other.retrievedDate, retrievedDate) ||
                other.retrievedDate == retrievedDate) &&
            (identical(other.lastUpdated, lastUpdated) ||
                other.lastUpdated == lastUpdated) &&
            (identical(other.faultData, faultData) ||
                other.faultData == faultData) &&
            (identical(other.metadata, metadata) ||
                other.metadata == metadata));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      terminalId,
      externalId,
      location,
      locationStr,
      city,
      region,
      bank,
      brand,
      model,
      issueStateName,
      status,
      fetchedStatus,
      serialNumber,
      retrievedDate,
      lastUpdated,
      faultData,
      metadata);

  /// Create a copy of AtmTerminal
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AtmTerminalImplCopyWith<_$AtmTerminalImpl> get copyWith =>
      __$$AtmTerminalImplCopyWithImpl<_$AtmTerminalImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AtmTerminalImplToJson(
      this,
    );
  }
}

abstract class _AtmTerminal implements AtmTerminal {
  const factory _AtmTerminal(
      {@JsonKey(name: 'terminal_id') required final String terminalId,
      @JsonKey(name: 'external_id') required final String externalId,
      required final String location,
      @JsonKey(name: 'location_str') required final String locationStr,
      final String? city,
      final String? region,
      final String? bank,
      final String? brand,
      final String? model,
      @JsonKey(name: 'issue_state_name') required final String issueStateName,
      required final String status,
      @JsonKey(name: 'fetched_status') required final String fetchedStatus,
      @JsonKey(name: 'serial_number') final String? serialNumber,
      @JsonKey(name: 'retrieved_date') required final DateTime retrievedDate,
      @JsonKey(name: 'last_updated') required final DateTime lastUpdated,
      @JsonKey(name: 'fault_data') final String? faultData,
      final String? metadata}) = _$AtmTerminalImpl;

  factory _AtmTerminal.fromJson(Map<String, dynamic> json) =
      _$AtmTerminalImpl.fromJson;

  @override
  @JsonKey(name: 'terminal_id')
  String get terminalId;
  @override
  @JsonKey(name: 'external_id')
  String get externalId;
  @override
  String get location;
  @override
  @JsonKey(name: 'location_str')
  String get locationStr;
  @override
  String? get city;
  @override
  String? get region;
  @override
  String? get bank;
  @override
  String? get brand;
  @override
  String? get model;
  @override
  @JsonKey(name: 'issue_state_name')
  String get issueStateName;
  @override
  String get status;
  @override
  @JsonKey(name: 'fetched_status')
  String get fetchedStatus;
  @override
  @JsonKey(name: 'serial_number')
  String? get serialNumber;
  @override
  @JsonKey(name: 'retrieved_date')
  DateTime get retrievedDate;
  @override
  @JsonKey(name: 'last_updated')
  DateTime get lastUpdated;
  @override
  @JsonKey(name: 'fault_data')
  String? get faultData;
  @override
  String? get metadata;

  /// Create a copy of AtmTerminal
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AtmTerminalImplCopyWith<_$AtmTerminalImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

RegionalData _$RegionalDataFromJson(Map<String, dynamic> json) {
  return _RegionalData.fromJson(json);
}

/// @nodoc
mixin _$RegionalData {
  @JsonKey(name: 'region_code')
  String get regionCode => throw _privateConstructorUsedError;
  @JsonKey(name: 'status_counts')
  StatusCounts get statusCounts => throw _privateConstructorUsedError;
  @JsonKey(name: 'availability_percentage')
  double get availabilityPercentage => throw _privateConstructorUsedError;

  /// Serializes this RegionalData to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RegionalDataCopyWith<RegionalData> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RegionalDataCopyWith<$Res> {
  factory $RegionalDataCopyWith(
          RegionalData value, $Res Function(RegionalData) then) =
      _$RegionalDataCopyWithImpl<$Res, RegionalData>;
  @useResult
  $Res call(
      {@JsonKey(name: 'region_code') String regionCode,
      @JsonKey(name: 'status_counts') StatusCounts statusCounts,
      @JsonKey(name: 'availability_percentage') double availabilityPercentage});

  $StatusCountsCopyWith<$Res> get statusCounts;
}

/// @nodoc
class _$RegionalDataCopyWithImpl<$Res, $Val extends RegionalData>
    implements $RegionalDataCopyWith<$Res> {
  _$RegionalDataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? regionCode = null,
    Object? statusCounts = null,
    Object? availabilityPercentage = null,
  }) {
    return _then(_value.copyWith(
      regionCode: null == regionCode
          ? _value.regionCode
          : regionCode // ignore: cast_nullable_to_non_nullable
              as String,
      statusCounts: null == statusCounts
          ? _value.statusCounts
          : statusCounts // ignore: cast_nullable_to_non_nullable
              as StatusCounts,
      availabilityPercentage: null == availabilityPercentage
          ? _value.availabilityPercentage
          : availabilityPercentage // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $StatusCountsCopyWith<$Res> get statusCounts {
    return $StatusCountsCopyWith<$Res>(_value.statusCounts, (value) {
      return _then(_value.copyWith(statusCounts: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$RegionalDataImplCopyWith<$Res>
    implements $RegionalDataCopyWith<$Res> {
  factory _$$RegionalDataImplCopyWith(
          _$RegionalDataImpl value, $Res Function(_$RegionalDataImpl) then) =
      __$$RegionalDataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'region_code') String regionCode,
      @JsonKey(name: 'status_counts') StatusCounts statusCounts,
      @JsonKey(name: 'availability_percentage') double availabilityPercentage});

  @override
  $StatusCountsCopyWith<$Res> get statusCounts;
}

/// @nodoc
class __$$RegionalDataImplCopyWithImpl<$Res>
    extends _$RegionalDataCopyWithImpl<$Res, _$RegionalDataImpl>
    implements _$$RegionalDataImplCopyWith<$Res> {
  __$$RegionalDataImplCopyWithImpl(
      _$RegionalDataImpl _value, $Res Function(_$RegionalDataImpl) _then)
      : super(_value, _then);

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? regionCode = null,
    Object? statusCounts = null,
    Object? availabilityPercentage = null,
  }) {
    return _then(_$RegionalDataImpl(
      regionCode: null == regionCode
          ? _value.regionCode
          : regionCode // ignore: cast_nullable_to_non_nullable
              as String,
      statusCounts: null == statusCounts
          ? _value.statusCounts
          : statusCounts // ignore: cast_nullable_to_non_nullable
              as StatusCounts,
      availabilityPercentage: null == availabilityPercentage
          ? _value.availabilityPercentage
          : availabilityPercentage // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$RegionalDataImpl implements _RegionalData {
  const _$RegionalDataImpl(
      {@JsonKey(name: 'region_code') required this.regionCode,
      @JsonKey(name: 'status_counts') required this.statusCounts,
      @JsonKey(name: 'availability_percentage')
      required this.availabilityPercentage});

  factory _$RegionalDataImpl.fromJson(Map<String, dynamic> json) =>
      _$$RegionalDataImplFromJson(json);

  @override
  @JsonKey(name: 'region_code')
  final String regionCode;
  @override
  @JsonKey(name: 'status_counts')
  final StatusCounts statusCounts;
  @override
  @JsonKey(name: 'availability_percentage')
  final double availabilityPercentage;

  @override
  String toString() {
    return 'RegionalData(regionCode: $regionCode, statusCounts: $statusCounts, availabilityPercentage: $availabilityPercentage)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RegionalDataImpl &&
            (identical(other.regionCode, regionCode) ||
                other.regionCode == regionCode) &&
            (identical(other.statusCounts, statusCounts) ||
                other.statusCounts == statusCounts) &&
            (identical(other.availabilityPercentage, availabilityPercentage) ||
                other.availabilityPercentage == availabilityPercentage));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, regionCode, statusCounts, availabilityPercentage);

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RegionalDataImplCopyWith<_$RegionalDataImpl> get copyWith =>
      __$$RegionalDataImplCopyWithImpl<_$RegionalDataImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RegionalDataImplToJson(
      this,
    );
  }
}

abstract class _RegionalData implements RegionalData {
  const factory _RegionalData(
      {@JsonKey(name: 'region_code') required final String regionCode,
      @JsonKey(name: 'status_counts') required final StatusCounts statusCounts,
      @JsonKey(name: 'availability_percentage')
      required final double availabilityPercentage}) = _$RegionalDataImpl;

  factory _RegionalData.fromJson(Map<String, dynamic> json) =
      _$RegionalDataImpl.fromJson;

  @override
  @JsonKey(name: 'region_code')
  String get regionCode;
  @override
  @JsonKey(name: 'status_counts')
  StatusCounts get statusCounts;
  @override
  @JsonKey(name: 'availability_percentage')
  double get availabilityPercentage;

  /// Create a copy of RegionalData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RegionalDataImplCopyWith<_$RegionalDataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CashInfo _$CashInfoFromJson(Map<String, dynamic> json) {
  return _CashInfo.fromJson(json);
}

/// @nodoc
mixin _$CashInfo {
  @JsonKey(name: 'terminal_id')
  String get terminalId => throw _privateConstructorUsedError;
  String get location => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_cash')
  double get totalCash => throw _privateConstructorUsedError;
  @JsonKey(name: 'cash_level_percentage')
  double get cashLevelPercentage => throw _privateConstructorUsedError;
  @JsonKey(name: 'last_refill')
  DateTime? get lastRefill => throw _privateConstructorUsedError;
  @JsonKey(name: 'estimated_days_remaining')
  int? get estimatedDaysRemaining => throw _privateConstructorUsedError;
  @JsonKey(name: 'denominations')
  Map<String, int>? get denominations => throw _privateConstructorUsedError;

  /// Serializes this CashInfo to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CashInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CashInfoCopyWith<CashInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CashInfoCopyWith<$Res> {
  factory $CashInfoCopyWith(CashInfo value, $Res Function(CashInfo) then) =
      _$CashInfoCopyWithImpl<$Res, CashInfo>;
  @useResult
  $Res call(
      {@JsonKey(name: 'terminal_id') String terminalId,
      String location,
      @JsonKey(name: 'total_cash') double totalCash,
      @JsonKey(name: 'cash_level_percentage') double cashLevelPercentage,
      @JsonKey(name: 'last_refill') DateTime? lastRefill,
      @JsonKey(name: 'estimated_days_remaining') int? estimatedDaysRemaining,
      @JsonKey(name: 'denominations') Map<String, int>? denominations});
}

/// @nodoc
class _$CashInfoCopyWithImpl<$Res, $Val extends CashInfo>
    implements $CashInfoCopyWith<$Res> {
  _$CashInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CashInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? terminalId = null,
    Object? location = null,
    Object? totalCash = null,
    Object? cashLevelPercentage = null,
    Object? lastRefill = freezed,
    Object? estimatedDaysRemaining = freezed,
    Object? denominations = freezed,
  }) {
    return _then(_value.copyWith(
      terminalId: null == terminalId
          ? _value.terminalId
          : terminalId // ignore: cast_nullable_to_non_nullable
              as String,
      location: null == location
          ? _value.location
          : location // ignore: cast_nullable_to_non_nullable
              as String,
      totalCash: null == totalCash
          ? _value.totalCash
          : totalCash // ignore: cast_nullable_to_non_nullable
              as double,
      cashLevelPercentage: null == cashLevelPercentage
          ? _value.cashLevelPercentage
          : cashLevelPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      lastRefill: freezed == lastRefill
          ? _value.lastRefill
          : lastRefill // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      estimatedDaysRemaining: freezed == estimatedDaysRemaining
          ? _value.estimatedDaysRemaining
          : estimatedDaysRemaining // ignore: cast_nullable_to_non_nullable
              as int?,
      denominations: freezed == denominations
          ? _value.denominations
          : denominations // ignore: cast_nullable_to_non_nullable
              as Map<String, int>?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CashInfoImplCopyWith<$Res>
    implements $CashInfoCopyWith<$Res> {
  factory _$$CashInfoImplCopyWith(
          _$CashInfoImpl value, $Res Function(_$CashInfoImpl) then) =
      __$$CashInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'terminal_id') String terminalId,
      String location,
      @JsonKey(name: 'total_cash') double totalCash,
      @JsonKey(name: 'cash_level_percentage') double cashLevelPercentage,
      @JsonKey(name: 'last_refill') DateTime? lastRefill,
      @JsonKey(name: 'estimated_days_remaining') int? estimatedDaysRemaining,
      @JsonKey(name: 'denominations') Map<String, int>? denominations});
}

/// @nodoc
class __$$CashInfoImplCopyWithImpl<$Res>
    extends _$CashInfoCopyWithImpl<$Res, _$CashInfoImpl>
    implements _$$CashInfoImplCopyWith<$Res> {
  __$$CashInfoImplCopyWithImpl(
      _$CashInfoImpl _value, $Res Function(_$CashInfoImpl) _then)
      : super(_value, _then);

  /// Create a copy of CashInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? terminalId = null,
    Object? location = null,
    Object? totalCash = null,
    Object? cashLevelPercentage = null,
    Object? lastRefill = freezed,
    Object? estimatedDaysRemaining = freezed,
    Object? denominations = freezed,
  }) {
    return _then(_$CashInfoImpl(
      terminalId: null == terminalId
          ? _value.terminalId
          : terminalId // ignore: cast_nullable_to_non_nullable
              as String,
      location: null == location
          ? _value.location
          : location // ignore: cast_nullable_to_non_nullable
              as String,
      totalCash: null == totalCash
          ? _value.totalCash
          : totalCash // ignore: cast_nullable_to_non_nullable
              as double,
      cashLevelPercentage: null == cashLevelPercentage
          ? _value.cashLevelPercentage
          : cashLevelPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      lastRefill: freezed == lastRefill
          ? _value.lastRefill
          : lastRefill // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      estimatedDaysRemaining: freezed == estimatedDaysRemaining
          ? _value.estimatedDaysRemaining
          : estimatedDaysRemaining // ignore: cast_nullable_to_non_nullable
              as int?,
      denominations: freezed == denominations
          ? _value._denominations
          : denominations // ignore: cast_nullable_to_non_nullable
              as Map<String, int>?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CashInfoImpl implements _CashInfo {
  const _$CashInfoImpl(
      {@JsonKey(name: 'terminal_id') required this.terminalId,
      required this.location,
      @JsonKey(name: 'total_cash') required this.totalCash,
      @JsonKey(name: 'cash_level_percentage') required this.cashLevelPercentage,
      @JsonKey(name: 'last_refill') this.lastRefill,
      @JsonKey(name: 'estimated_days_remaining') this.estimatedDaysRemaining,
      @JsonKey(name: 'denominations') final Map<String, int>? denominations})
      : _denominations = denominations;

  factory _$CashInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$CashInfoImplFromJson(json);

  @override
  @JsonKey(name: 'terminal_id')
  final String terminalId;
  @override
  final String location;
  @override
  @JsonKey(name: 'total_cash')
  final double totalCash;
  @override
  @JsonKey(name: 'cash_level_percentage')
  final double cashLevelPercentage;
  @override
  @JsonKey(name: 'last_refill')
  final DateTime? lastRefill;
  @override
  @JsonKey(name: 'estimated_days_remaining')
  final int? estimatedDaysRemaining;
  final Map<String, int>? _denominations;
  @override
  @JsonKey(name: 'denominations')
  Map<String, int>? get denominations {
    final value = _denominations;
    if (value == null) return null;
    if (_denominations is EqualUnmodifiableMapView) return _denominations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  String toString() {
    return 'CashInfo(terminalId: $terminalId, location: $location, totalCash: $totalCash, cashLevelPercentage: $cashLevelPercentage, lastRefill: $lastRefill, estimatedDaysRemaining: $estimatedDaysRemaining, denominations: $denominations)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CashInfoImpl &&
            (identical(other.terminalId, terminalId) ||
                other.terminalId == terminalId) &&
            (identical(other.location, location) ||
                other.location == location) &&
            (identical(other.totalCash, totalCash) ||
                other.totalCash == totalCash) &&
            (identical(other.cashLevelPercentage, cashLevelPercentage) ||
                other.cashLevelPercentage == cashLevelPercentage) &&
            (identical(other.lastRefill, lastRefill) ||
                other.lastRefill == lastRefill) &&
            (identical(other.estimatedDaysRemaining, estimatedDaysRemaining) ||
                other.estimatedDaysRemaining == estimatedDaysRemaining) &&
            const DeepCollectionEquality()
                .equals(other._denominations, _denominations));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      terminalId,
      location,
      totalCash,
      cashLevelPercentage,
      lastRefill,
      estimatedDaysRemaining,
      const DeepCollectionEquality().hash(_denominations));

  /// Create a copy of CashInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CashInfoImplCopyWith<_$CashInfoImpl> get copyWith =>
      __$$CashInfoImplCopyWithImpl<_$CashInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CashInfoImplToJson(
      this,
    );
  }
}

abstract class _CashInfo implements CashInfo {
  const factory _CashInfo(
      {@JsonKey(name: 'terminal_id') required final String terminalId,
      required final String location,
      @JsonKey(name: 'total_cash') required final double totalCash,
      @JsonKey(name: 'cash_level_percentage')
      required final double cashLevelPercentage,
      @JsonKey(name: 'last_refill') final DateTime? lastRefill,
      @JsonKey(name: 'estimated_days_remaining')
      final int? estimatedDaysRemaining,
      @JsonKey(name: 'denominations')
      final Map<String, int>? denominations}) = _$CashInfoImpl;

  factory _CashInfo.fromJson(Map<String, dynamic> json) =
      _$CashInfoImpl.fromJson;

  @override
  @JsonKey(name: 'terminal_id')
  String get terminalId;
  @override
  String get location;
  @override
  @JsonKey(name: 'total_cash')
  double get totalCash;
  @override
  @JsonKey(name: 'cash_level_percentage')
  double get cashLevelPercentage;
  @override
  @JsonKey(name: 'last_refill')
  DateTime? get lastRefill;
  @override
  @JsonKey(name: 'estimated_days_remaining')
  int? get estimatedDaysRemaining;
  @override
  @JsonKey(name: 'denominations')
  Map<String, int>? get denominations;

  /// Create a copy of CashInfo
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CashInfoImplCopyWith<_$CashInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
