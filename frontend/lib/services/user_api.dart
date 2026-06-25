import 'package:dio/dio.dart';

import 'dio_client.dart';

class UserApi {
  UserApi({Dio? dio}) : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<Map<String, dynamic>> getProfile({required String accessToken}) async {
    final response = await _dio.get(
      '/user/profile',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );

    return _toJsonMap(response.data);
  }

  Future<Map<String, dynamic>> updateProfile({
    required String accessToken,
    String? name,
    String? preferredLanguage,
    double? latitude,
    double? longitude,
  }) async {
    // Send only the fields that are provided.
    final data = <String, dynamic>{};

    if (name != null && name.trim().isNotEmpty) {
      data['name'] = name.trim();
    }

    if (preferredLanguage != null && preferredLanguage.trim().isNotEmpty) {
      data['preferred_language'] = preferredLanguage.trim();
    }

    if (latitude != null && longitude != null) {
      data['location'] = {'latitude': latitude, 'longitude': longitude};
    }

    final response = await _dio.patch(
      '/user/profile',
      data: data,
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );

    return _toJsonMap(response.data);
  }

  Map<String, dynamic> _toJsonMap(dynamic data) {
    if (data is Map<String, dynamic>) {
      return data;
    }
    throw Exception('Unexpected response format.');
  }
}
