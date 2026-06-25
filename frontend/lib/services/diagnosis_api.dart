import 'dart:io';

import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import 'dio_client.dart';

class DiagnosisApi {
  DiagnosisApi({Dio? dio}) : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<Map<String, dynamic>> createDiagnosis({
    required String accessToken,
    required String cropType,
    required File imageFile,
    String? language,
  }) async {
    // Upload image as multipart/form-data.
    final formData = FormData.fromMap({
      'crop_type': cropType,
      'image': await MultipartFile.fromFile(
        imageFile.path,
        filename: 'capture.jpg',
        contentType: MediaType('image', 'jpeg'),
      ),
    });

    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};
    if (language != null && language.isNotEmpty) {
      headers['Accept-Language'] = language;
    }

    final response = await _dio.post(
      '/diagnosis/',
      data: formData,
      options: Options(headers: headers),
    );

    if (response.data is Map<String, dynamic>) {
      return response.data as Map<String, dynamic>;
    }

    throw Exception('Unexpected diagnosis response format.');
  }

  Future<Map<String, dynamic>> getDiagnosis({
    required String accessToken,
    required String diagnosisId,
    String? language,
  }) async {
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};
    if (language != null && language.isNotEmpty) {
      headers['Accept-Language'] = language;
    }

    final response = await _dio.get(
      '/diagnosis/$diagnosisId',
      options: Options(headers: headers),
    );

    if (response.data is Map<String, dynamic>) {
      return response.data as Map<String, dynamic>;
    }

    throw Exception('Unexpected diagnosis response format.');
  }
}
