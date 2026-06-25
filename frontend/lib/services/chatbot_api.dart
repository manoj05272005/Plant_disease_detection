import 'package:dio/dio.dart';

import 'api_config.dart';

class ChatbotApi {
  ChatbotApi({Dio? dio}) : _dio = dio ?? Dio(_defaultOptions());

  final Dio _dio;

  static BaseOptions _defaultOptions() {
    return BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Accept': 'application/json'},
    );
  }

  /// Send a message to the AI chatbot and get a response
  Future<Map<String, dynamic>> sendMessage({
    required String accessToken,
    required String message,
    String? language,
  }) async {
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};
    if (language != null && language.isNotEmpty) {
      headers['Accept-Language'] = language;
    }

    final requestData = {
      'message': message,
      'language': language ?? 'en',
    };

    final response = await _dio.post(
      '/chatbot/message',
      data: requestData,
      options: Options(headers: headers),
    );

    if (response.data is Map<String, dynamic>) {
      return response.data as Map<String, dynamic>;
    }

    throw Exception('Unexpected chatbot response format.');
  }

  /// Get conversation history with the chatbot
  Future<List<Map<String, dynamic>>> getChatHistory({
    required String accessToken,
    int limit = 20,
  }) async {
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};

    final response = await _dio.get(
      '/chatbot/history',
      queryParameters: {'limit': limit},
      options: Options(headers: headers),
    );

    if (response.data is List) {
      return (response.data as List).cast<Map<String, dynamic>>();
    }

    throw Exception('Unexpected chat history response format.');
  }

  /// Clear conversation history
  Future<void> clearChatHistory({
    required String accessToken,
  }) async {
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};

    await _dio.delete(
      '/chatbot/history',
      options: Options(headers: headers),
    );
  }

  /// Get supported intents and features
  Future<Map<String, dynamic>> getSupportedFeatures({
    required String accessToken,
  }) async {
    final headers = <String, dynamic>{'Authorization': 'Bearer $accessToken'};

    final response = await _dio.get(
      '/chatbot/intents',
      options: Options(headers: headers),
    );

    if (response.data is Map<String, dynamic>) {
      return response.data as Map<String, dynamic>;
    }

    throw Exception('Unexpected intents response format.');
  }
}