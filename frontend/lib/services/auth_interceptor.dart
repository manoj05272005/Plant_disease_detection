import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import 'auth_api.dart';
import 'token_storage.dart';

/// Dio interceptor that automatically refreshes expired access tokens.
///
/// Uses [QueuedInterceptorsWrapper] so that if multiple parallel requests
/// fail with 401, only a single refresh is triggered and the rest are
/// retried with the new token.
class AuthInterceptor extends QueuedInterceptorsWrapper {
  AuthInterceptor({
    required TokenStorage tokenStorage,
    required GlobalKey<NavigatorState> navigatorKey,
  }) : _tokenStorage = tokenStorage,
       _navigatorKey = navigatorKey;

  final TokenStorage _tokenStorage;
  final GlobalKey<NavigatorState> _navigatorKey;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    // Extract the token that was used in the failed request.
    final failedAuth =
        err.requestOptions.headers['Authorization']?.toString() ?? '';
    final failedToken = failedAuth.startsWith('Bearer ')
        ? failedAuth.substring(7)
        : '';

    // Read the latest stored token. If it differs from the one that
    // failed, another queued request already refreshed it — simply retry.
    final currentToken = await _tokenStorage.readAccessToken();
    if (currentToken != null &&
        currentToken.isNotEmpty &&
        currentToken != failedToken) {
      err.requestOptions.headers['Authorization'] = 'Bearer $currentToken';
      try {
        final response = await _retryRequest(err.requestOptions);
        return handler.resolve(response);
      } catch (retryError) {
        return handler.reject(
          DioException(requestOptions: err.requestOptions, error: retryError),
        );
      }
    }

    // Attempt a token refresh.
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      await _forceLogout();
      return handler.reject(err);
    }

    try {
      // Use a standalone AuthApi (its own Dio) to avoid interceptor loops.
      final result = await AuthApi().refreshToken(refreshToken: refreshToken);

      final newAccessToken = result['access_token']?.toString();
      final newRefreshToken = result['refresh_token']?.toString();
      final tokenType = result['token_type']?.toString();

      if (newAccessToken == null || newRefreshToken == null) {
        await _forceLogout();
        return handler.reject(err);
      }

      await _tokenStorage.saveTokens(
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
        tokenType: tokenType,
      );

      // Retry the original request with the fresh token.
      err.requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
      final response = await _retryRequest(err.requestOptions);
      return handler.resolve(response);
    } catch (_) {
      // Refresh failed — session is truly expired.
      await _forceLogout();
      return handler.reject(err);
    }
  }

  /// Retry a request using a plain [Dio] (no interceptors) so we
  /// don't trigger this handler again.
  Future<Response<dynamic>> _retryRequest(RequestOptions opts) {
    final retryDio = Dio();
    return retryDio.fetch(opts);
  }

  /// Clear tokens and redirect to the login screen.
  Future<void> _forceLogout() async {
    await _tokenStorage.clearTokens();
    final nav = _navigatorKey.currentState;
    if (nav != null) {
      nav.pushNamedAndRemoveUntil('/login', (_) => false);
    }
  }
}
