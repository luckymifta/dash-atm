import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/config/api_config.dart';
import '../models/user_model.dart';
import '../models/auth_models.dart';

class AuthService {
  static const String _tokenKey = 'access_token';
  static const String _userKey = 'user_data';
  static const String _refreshTokenKey = 'refresh_token';
  
  final Dio _dio = Dio(BaseOptions(
    baseUrl: ApiConfig.userApiUrl,
    connectTimeout: ApiConfig.connectTimeout,
    receiveTimeout: ApiConfig.receiveTimeout,
    sendTimeout: ApiConfig.sendTimeout,
    headers: ApiConfig.defaultHeaders,
  ));

  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainItemAccessibility.first_unlock_this_device,
    ),
  );

  AuthService() {
    _setupInterceptors();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Add token to requests automatically
          final token = await getToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          // Handle 401 errors with token refresh
          if (error.response?.statusCode == 401) {
            final refreshed = await _tryRefreshToken();
            if (refreshed) {
              // Retry the original request
              final clonedRequest = await _dio.fetch(error.requestOptions);
              handler.resolve(clonedRequest);
              return;
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  Future<LoginResponse> login(LoginRequest request) async {
    try {
      final response = await _dio.post(
        ApiConfig.endpoints['login']!,
        data: request.toJson(),
      );

      final loginResponse = LoginResponse.fromJson(response.data);
      
      // Store tokens securely
      await _secureStorage.write(key: _tokenKey, value: loginResponse.accessToken);
      
      if (loginResponse.refreshToken != null) {
        await _secureStorage.write(key: _refreshTokenKey, value: loginResponse.refreshToken!);
      }

      // Create and store user data since API might not return it
      final user = User(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        username: request.username,
        email: '${request.username}@company.com',
        role: request.username.toLowerCase() == 'admin' ? 'Administrator' : 'User',
        isActive: true,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
        lastLogin: DateTime.now(),
      );

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey, jsonEncode(user.toJson()));

      return loginResponse;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthException('Invalid credentials');
      } else if (e.response?.statusCode == 422) {
        throw AuthException('Invalid input format');
      } else if (e.type == DioExceptionType.connectionTimeout) {
        throw AuthException('Connection timeout');
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw AuthException('Server response timeout');
      }
      throw AuthException('Login failed: ${e.message}');
    } catch (e) {
      throw AuthException('Unexpected error: ${e.toString()}');
    }
  }

  Future<void> logout() async {
    try {
      // Attempt to logout on server
      await _dio.post(ApiConfig.endpoints['logout']!);
    } catch (e) {
      // Continue with local logout even if server logout fails
    } finally {
      // Clear all stored data
      await _secureStorage.delete(key: _tokenKey);
      await _secureStorage.delete(key: _refreshTokenKey);
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_userKey);
    }
  }

  Future<String?> getToken() async {
    return await _secureStorage.read(key: _tokenKey);
  }

  Future<User?> getCurrentUser() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString(_userKey);
      
      if (userJson != null) {
        return User.fromJson(jsonDecode(userJson));
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  Future<bool> _tryRefreshToken() async {
    try {
      final refreshToken = await _secureStorage.read(key: _refreshTokenKey);
      if (refreshToken == null) return false;

      final response = await _dio.post(
        ApiConfig.endpoints['refresh']!,
        data: {'refresh_token': refreshToken},
      );

      final newToken = response.data['access_token'] as String?;
      if (newToken != null) {
        await _secureStorage.write(key: _tokenKey, value: newToken);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
}

class AuthException implements Exception {
  final String message;
  AuthException(this.message);

  @override
  String toString() => message;
}
