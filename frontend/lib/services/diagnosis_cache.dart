import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

import 'api_config.dart';

class DiagnosisCacheService {
  DiagnosisCacheService({Dio? dio}) : _dio = dio ?? Dio();

  final Dio _dio;

  Future<Map<String, dynamic>> cacheDiagnosisImages({
    required String diagnosisId,
    required Map<String, dynamic> result,
  }) async {
    final updated = Map<String, dynamic>.from(result);
    final imageUrl = _resolveUrl(result['image_url']?.toString());
    final heatmapUrl = _resolveUrl(result['heatmap_url']?.toString());

    if (imageUrl.isEmpty && heatmapUrl.isEmpty) {
      return updated;
    }

    try {
      final cacheDir = await _ensureCacheDir(diagnosisId);
      if (imageUrl.isNotEmpty) {
        final path = await _downloadIfNeeded(
          url: imageUrl,
          directory: cacheDir,
          prefix: 'image',
        );
        if (path != null) {
          updated['local_image_path'] = path;
        }
      }

      if (heatmapUrl.isNotEmpty) {
        final path = await _downloadIfNeeded(
          url: heatmapUrl,
          directory: cacheDir,
          prefix: 'heatmap',
        );
        if (path != null) {
          updated['local_heatmap_path'] = path;
        }
      }
    } catch (_) {
      // Ignore cache failures and keep network URLs.
    }

    return updated;
  }

  String _resolveUrl(String? path) {
    if (path == null || path.isEmpty) {
      return '';
    }
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.startsWith('/')) {
      return '${ApiConfig.baseHost}$path';
    }
    return '${ApiConfig.baseHost}/$path';
  }

  Future<Directory> _ensureCacheDir(String diagnosisId) async {
    final baseDir = await getApplicationDocumentsDirectory();
    final cacheDir = Directory('${baseDir.path}/diagnosis_cache/$diagnosisId');
    if (await cacheDir.exists()) {
      return cacheDir;
    }
    return cacheDir.create(recursive: true);
  }

  Future<String?> _downloadIfNeeded({
    required String url,
    required Directory directory,
    required String prefix,
  }) async {
    final extension = _resolveExtension(url);
    final file = File('${directory.path}/$prefix$extension');
    if (await file.exists()) {
      return file.path;
    }

    final response = await _dio.get<List<int>>(
      url,
      options: Options(responseType: ResponseType.bytes),
    );

    final bytes = response.data;
    if (bytes == null) {
      return null;
    }

    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  String _resolveExtension(String url) {
    final path = Uri.parse(url).path;
    final dotIndex = path.lastIndexOf('.');
    if (dotIndex == -1 || dotIndex == path.length - 1) {
      return '.jpg';
    }
    final ext = path.substring(dotIndex);
    if (ext.length > 5) {
      return '.jpg';
    }
    return ext;
  }
}
