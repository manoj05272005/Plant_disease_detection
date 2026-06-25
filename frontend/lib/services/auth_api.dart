import 'package:dio/dio.dart';

import 'api_config.dart';

class AuthApi {
  AuthApi({Dio? dio}) : _dio = dio ?? Dio(_defaultOptions());

  final Dio _dio;

  static BaseOptions _defaultOptions() {
    // Shared timeouts and headers for auth endpoints.
    return BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Accept': 'application/json'},
    );
  }

  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String phone,
    required String password,
    required String preferredLanguage,
    required double latitude,
    required double longitude,
    required String address,
  }) async {
    final response = await _dio.post(
      '/auth/register',
      data: {
        'name': name,
        'email': email,
        'phone': phone,
        'password': password,
        'preferred_language': preferredLanguage,
        'location': 'lat:$latitude, lng:$longitude, $address',
      },
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> login({
    required String username,
    required String password,
  }) async {
    final response = await _dio.post(
      '/auth/login',
      data: {'username': username, 'password': password},
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> forgotPassword({
    required String username,
  }) async {
    final response = await _dio.post(
      '/auth/forgot-password',
      data: {'username': username},
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> resetPassword({
    required String token,
    required String otp,
    required String newPassword,
  }) async {
    final response = await _dio.post(
      '/auth/reset-password',
      data: {'token': token, 'otp': otp, 'new_password': newPassword},
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> refreshToken({
    required String refreshToken,
  }) async {
    final response = await _dio.post(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> beginPasskeyRegistration({
    required String username,
  }) async {
    final response = await _dio.post(
      '/auth/passkeys/register/begin',
      data: {'username': username},
    );
    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> finishPasskeyRegistration({
    required String username,
    required Map<String, dynamic> credential,
  }) async {
    final response = await _dio.post(
      '/auth/passkeys/register/finish',
      data: {'username': username, 'credential': credential},
    );
    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> beginPasskeyLogin({
    required String username,
  }) async {
    final response = await _dio.post(
      '/auth/passkeys/login/begin',
      data: {'username': username},
    );
    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> finishPasskeyLogin({
    required String username,
    required Map<String, dynamic> credential,
  }) async {
    final response = await _dio.post(
      '/auth/passkeys/login/finish',
      data: {'username': username, 'credential': credential},
    );
    return _toJsonMap(response.data);
  }

  Map<String, dynamic> _toJsonMap(dynamic data) {
    // Enforce a predictable map response shape.
    if (data is Map<String, dynamic>) {
      return data;
    }
    throw Exception('Unexpected response format.');
  }
}
