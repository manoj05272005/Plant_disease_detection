import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const MethodChannel _ttsChannel = MethodChannel('flutter_tts');
const MethodChannel _secureStorageChannel = MethodChannel(
  'plugins.it_nomads.com/flutter_secure_storage',
);
const MethodChannel _connectivityChannel = MethodChannel(
  'dev.fluttercommunity.plus/connectivity',
);

final Map<String, String?> _secureStorageState = <String, String?>{};
List<String> _connectivityResults = <String>['none'];

void seedIntegrationSecureStorage(Map<String, String?> values) {
  _secureStorageState
    ..clear()
    ..addAll(values);
}

void clearIntegrationSecureStorage() {
  _secureStorageState.clear();
}

void setIntegrationConnectivityResults(List<String> results) {
  if (results.isEmpty) {
    _connectivityResults = <String>['none'];
    return;
  }
  _connectivityResults = List<String>.from(results);
}

void setupIntegrationTestPluginMocks() {
  clearIntegrationSecureStorage();
  setIntegrationConnectivityResults(<String>['none']);

  _ttsChannel.setMockMethodCallHandler((call) async {
    switch (call.method) {
      case 'getLanguages':
        return <String>['en-US', 'hi-IN', 'ta-IN', 'te-IN', 'kn-IN', 'ml-IN'];
      case 'setLanguage':
      case 'setSpeechRate':
      case 'setVolume':
      case 'setPitch':
      case 'speak':
      case 'stop':
      case 'awaitSpeakCompletion':
      case 'setStartHandler':
      case 'setCompletionHandler':
      case 'setCancelHandler':
      case 'setErrorHandler':
        return 1;
      default:
        return 1;
    }
  });

  _secureStorageChannel.setMockMethodCallHandler((call) async {
    switch (call.method) {
      case 'read':
        final key = call.arguments['key']?.toString();
        return key == null ? null : _secureStorageState[key];
      case 'write':
        final key = call.arguments['key']?.toString();
        if (key != null) {
          _secureStorageState[key] = call.arguments['value']?.toString();
        }
        return null;
      case 'delete':
        final key = call.arguments['key']?.toString();
        if (key != null) {
          _secureStorageState.remove(key);
        }
        return null;
      case 'deleteAll':
        _secureStorageState.clear();
        return null;
      case 'containsKey':
        final key = call.arguments['key']?.toString();
        return key != null && _secureStorageState.containsKey(key);
      case 'readAll':
        return _secureStorageState.map((key, value) {
          return MapEntry(key, value ?? '');
        });
      default:
        return null;
    }
  });

  _connectivityChannel.setMockMethodCallHandler((call) async {
    switch (call.method) {
      case 'check':
      case 'checkConnectivity':
        return _connectivityResults;
      default:
        return _connectivityResults;
    }
  });
}

void tearDownIntegrationTestPluginMocks() {
  clearIntegrationSecureStorage();
  _ttsChannel.setMockMethodCallHandler(null);
  _secureStorageChannel.setMockMethodCallHandler(null);
  _connectivityChannel.setMockMethodCallHandler(null);
}
