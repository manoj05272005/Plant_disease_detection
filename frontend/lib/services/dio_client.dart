import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import 'api_config.dart';
import 'auth_interceptor.dart';
import 'token_storage.dart';

/// Singleton [Dio] client with automatic token-refresh via [AuthInterceptor].
///
/// Call [DioClient.init] once (in `main()` or `MaterialApp` setup) to supply
/// the navigator key used for forced logout on session expiry.
class DioClient {
  DioClient._();

  static Dio? _instance;
  static GlobalKey<NavigatorState>? _navigatorKey;

  /// Initialise with the app-wide [NavigatorState] key.
  /// Must be called before any API service accesses [instance].
  static void init(GlobalKey<NavigatorState> navigatorKey) {
    _navigatorKey = navigatorKey;
    _instance = null; // Recreate on next access.
  }

  /// The shared [Dio] instance with auth interceptor attached.
  static Dio get instance {
    assert(
      _navigatorKey != null,
      'DioClient.init() must be called before accessing DioClient.instance',
    );
    _instance ??= _create();
    return _instance!;
  }

  static Dio _create() {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Accept': 'application/json'},
      ),
    );

    dio.interceptors.add(
      AuthInterceptor(
        tokenStorage: const TokenStorage(),
        navigatorKey: _navigatorKey!,
      ),
    );

    return dio;
  }
}
