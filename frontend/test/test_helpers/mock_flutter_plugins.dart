import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const MethodChannel _ttsChannel = MethodChannel('flutter_tts');
const MethodChannel _secureStorageChannel = MethodChannel(
  'plugins.it_nomads.com/flutter_secure_storage',
);

void setupMockFlutterPlugins() {
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
        return null;
      case 'write':
      case 'delete':
      case 'deleteAll':
        return null;
      case 'containsKey':
        return false;
      case 'readAll':
        return <String, String>{};
      default:
        return null;
    }
  });
}

void tearDownMockFlutterPlugins() {
  _ttsChannel.setMockMethodCallHandler(null);
  _secureStorageChannel.setMockMethodCallHandler(null);
}
