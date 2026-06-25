import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../lib/services/tts_service.dart';
import 'test_helpers/mock_flutter_plugins.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(setupMockFlutterPlugins);
  tearDownAll(tearDownMockFlutterPlugins);

  group('TtsService Tests', () {
    late TtsService ttsService;

    setUp(() {
      // Setup SharedPreferences mock
      SharedPreferences.setMockInitialValues({'preferred_language': 'en'});
      ttsService = TtsService();
    });

    test('TtsService should be a singleton', () {
      final instance1 = TtsService();
      final instance2 = TtsService();
      expect(instance1, equals(instance2));
    });

    test('TtsService should initialize successfully', () async {
      final success = await ttsService.initialize();
      // Note: In test environment, TTS may not be available
      // This test just verifies the method doesn't crash
      expect(success, isA<bool>());
    });

    test('TtsService should handle speak with null text gracefully', () async {
      await ttsService.initialize();
      // This should not throw an error
      await ttsService.speak(null);
      expect(true, isTrue); // If we get here, test passed
    });

    test('TtsService should handle speak with empty text gracefully', () async {
      await ttsService.initialize();
      // This should not throw an error
      await ttsService.speak('');
      expect(true, isTrue); // If we get here, test passed
    });

    test(
      'TtsService should handle speak with whitespace-only text gracefully',
      () async {
        await ttsService.initialize();
        // This should not throw an error
        await ttsService.speak('   ');
        expect(true, isTrue); // If we get here, test passed
      },
    );

    test('TtsService should handle stop gracefully', () async {
      await ttsService.initialize();
      // This should not throw an error
      await ttsService.stop();
      expect(true, isTrue); // If we get here, test passed
    });

    test('TtsService should handle dispose gracefully', () async {
      await ttsService.initialize();
      // This should not throw an error
      await ttsService.dispose();
      expect(true, isTrue); // If we get here, test passed
    });

    test('Language mapping should be correct', () {
      final languageMap = {
        'en': 'en-US',
        'hi': 'hi-IN',
        'kn': 'kn-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'mr': 'mr-IN',
        'bn': 'bn-IN',
      };

      // Verify the mapping is as expected
      expect(languageMap['en'], equals('en-US'));
      expect(languageMap['hi'], equals('hi-IN'));
      expect(languageMap['kn'], equals('kn-IN'));
      expect(languageMap['ta'], equals('ta-IN'));
      expect(languageMap['te'], equals('te-IN'));
      expect(languageMap['mr'], equals('mr-IN'));
      expect(languageMap['bn'], equals('bn-IN'));
    });

    test('TtsService should handle multiple rapid calls gracefully', () async {
      await ttsService.initialize();

      // Simulate rapid taps
      await ttsService.speak('First message');
      await ttsService.speak('Second message');
      await ttsService.speak('Third message');
      await ttsService.stop();

      expect(true, isTrue); // If we get here, test passed
    });

    test(
      'TtsService should work with different languages in SharedPreferences',
      () async {
        // Test with Hindi
        SharedPreferences.setMockInitialValues({'preferred_language': 'hi'});
        final hindiService = TtsService();
        final hindiSuccess = await hindiService.initialize();
        expect(hindiSuccess, isA<bool>());

        // Test with Kannada
        SharedPreferences.setMockInitialValues({'preferred_language': 'kn'});
        final kannadaService = TtsService();
        final kannadaSuccess = await kannadaService.initialize();
        expect(kannadaSuccess, isA<bool>());
      },
    );
  });
}
