import 'package:dio/dio.dart';

import 'dio_client.dart';

class NotificationApi {
  NotificationApi({Dio? dio}) : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<List<Map<String, dynamic>>> getNotifications({
    required String accessToken,
    String? language,
    int limit = 50,
    bool unreadOnly = false,
  }) async {
    // Optionally filter to unread notifications only.
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};
    if (language != null && language.isNotEmpty) {
      headers['Accept-Language'] = language;
    }

    final response = await _dio.get(
      '/notifications/',
      queryParameters: {'limit': limit, 'unread_only': unreadOnly},
      options: Options(headers: headers),
    );

    final data = response.data;
    if (data is List) {
      return data.whereType<Map<String, dynamic>>().toList();
    }

    throw Exception('Unexpected notifications response format.');
  }

  Future<void> markAllRead({required String accessToken}) async {
    await _dio.post(
      '/notifications/mark-all-read',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
  }
}
