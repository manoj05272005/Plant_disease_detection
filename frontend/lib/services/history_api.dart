import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

import 'dio_client.dart';

class HistoryApi {
  HistoryApi({Dio? dio}) : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<List<Map<String, dynamic>>> getHistory({
    required String accessToken,
    int skip = 0,
    int limit = 20,
  }) async {
    final response = await _dio.get(
      '/history/',
      queryParameters: {'skip': skip, 'limit': limit},
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );

    final data = response.data;
    if (data is Map<String, dynamic>) {
      final items = data['items'];
      if (items is List) {
        return items.whereType<Map<String, dynamic>>().toList();
      }
    }

    throw Exception('Unexpected history response format.');
  }

  Future<Map<String, dynamic>> getAnalytics({
    required String accessToken,
  }) async {
    final response = await _dio.get(
      '/history/analytics',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );

    if (response.data is Map<String, dynamic>) {
      return response.data as Map<String, dynamic>;
    }

    throw Exception('Unexpected analytics response format.');
  }

  Future<void> deleteHistory({
    required String accessToken,
    required String historyId,
  }) async {
    await _dio.delete(
      '/history/$historyId',
      options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
    );
  }

  Future<String> downloadReport({
    required String accessToken,
    required String diagnosisId,
  }) async {
    // Save report to Downloads when available.
    final response = await _dio.get<List<int>>(
      '/history/report/$diagnosisId',
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
        responseType: ResponseType.bytes,
      ),
    );

    final bytes = response.data;
    if (bytes == null) {
      throw Exception('Failed to download report.');
    }

    final directory = await _resolveDownloadDirectory();
    final file = File('${directory.path}/diagnosis_report_$diagnosisId.pdf');
    await file.writeAsBytes(bytes, flush: true);

    return file.path;
  }

  Future<Directory> _resolveDownloadDirectory() async {
    if (Platform.isAndroid) {
      final downloadDir = Directory('/storage/emulated/0/Download');
      if (await downloadDir.exists()) {
        return downloadDir;
      }
    }

    final fallback = await getApplicationDocumentsDirectory();
    return fallback;
  }
}
