import 'package:dio/dio.dart';

import 'api_config.dart';

class WeatherInfo {
  final String locationName;
  final String conditionText;
  final String conditionIconUrl;
  final double tempC;
  final double feelsLikeC;
  final int humidity;
  final double windKph;

  const WeatherInfo({
    required this.locationName,
    required this.conditionText,
    required this.conditionIconUrl,
    required this.tempC,
    required this.feelsLikeC,
    required this.humidity,
    required this.windKph,
  });

  factory WeatherInfo.fromJson(Map<String, dynamic> json) {
    final location = json['location'] as Map<String, dynamic>?;
    final current = json['current'] as Map<String, dynamic>?;
    final condition = current?['condition'] as Map<String, dynamic>?;

    return WeatherInfo(
      locationName: location?['name']?.toString() ?? 'Unknown',
      conditionText: condition?['text']?.toString() ?? 'Unknown',
      conditionIconUrl: _normalizeIcon(condition?['icon']?.toString()),
      tempC: _asDouble(current?['temp_c']),
      feelsLikeC: _asDouble(current?['feelslike_c']),
      humidity: (current?['humidity'] as num?)?.toInt() ?? 0,
      windKph: _asDouble(current?['wind_kph']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'location': {'name': locationName},
      'current': {
        'temp_c': tempC,
        'feelslike_c': feelsLikeC,
        'humidity': humidity,
        'wind_kph': windKph,
        'condition': {
          'text': conditionText,
          'icon': conditionIconUrl,
        },
      },
    };
  }

  static String _normalizeIcon(String? icon) {
    if (icon == null || icon.isEmpty) {
      return '';
    }
    if (icon.startsWith('//')) {
      return 'https:$icon';
    }
    return icon;
  }

  static double _asDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }
    return 0.0;
  }
}

class WeatherApi {
  WeatherApi({Dio? dio}) : _dio = dio ?? Dio(_defaultOptions());

  final Dio _dio;

  static BaseOptions _defaultOptions() {
    return BaseOptions(
      baseUrl: ApiConfig.weatherApiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Accept': 'application/json'},
    );
  }

  Future<WeatherInfo> getCurrentWeather({
    required double latitude,
    required double longitude,
  }) async {
    // Fetch current conditions for a lat/lng pair.
    final response = await _dio.get(
      '/current.json',
      queryParameters: {
        'key': ApiConfig.weatherApiKey,
        'q': '$latitude,$longitude',
      },
    );

    if (response.data is Map<String, dynamic>) {
      return WeatherInfo.fromJson(response.data as Map<String, dynamic>);
    }

    throw Exception('Unexpected weather response format.');
  }
}
