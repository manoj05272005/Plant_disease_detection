import 'package:flutter_tts/flutter_tts.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Singleton service for Text-to-Speech functionality.
/// Provides offline speech synthesis using the device's built-in TTS engine.
class TtsService {
  // Private constructor for singleton pattern
  TtsService._internal();

  // Singleton instance
  static final TtsService _instance = TtsService._internal();

  // Factory constructor returns the singleton instance
  factory TtsService() => _instance;

  // FlutterTts instance
  final FlutterTts _flutterTts = FlutterTts();

  // Track speaking state
  bool _isSpeaking = false;
  bool get isSpeaking => _isSpeaking;

  // Track initialization state
  bool _isInitialized = false;
  bool get isInitialized => _isInitialized;

  // Track if fallback to English occurred
  bool _fellBackToEnglish = false;
  bool get fellBackToEnglish => _fellBackToEnglish;

  // Preferred language from user profile
  String _preferredLanguage = 'en';

  /// Map app language codes to BCP-47 locale codes
  final Map<String, String> _languageMap = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'kn': 'kn-IN',
    'ml': 'ml-IN',
  };

  /// Initialize the TTS service
  /// Returns true if initialization succeeded, false otherwise
  Future<bool> initialize() async {
    if (_isInitialized) {
      return true;
    }

    try {
      // Read user's preferred language from SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      _preferredLanguage = prefs.getString('preferred_language') ?? 'en';

      // Map to BCP-47 locale
      final locale = _languageMap[_preferredLanguage] ?? 'en-US';

      // Get available languages on the device
      final languages = await _flutterTts.getLanguages;
      final availableLanguages = languages.cast<String>();

      // Check if preferred language is available
      bool isPreferredAvailable = false;
      for (final lang in availableLanguages) {
        if (lang.toLowerCase().startsWith(
          locale.toLowerCase().substring(0, 2),
        )) {
          isPreferredAvailable = true;
          break;
        }
      }

      // Set language (fallback to English if not available)
      if (isPreferredAvailable) {
        await _flutterTts.setLanguage(locale);
        _fellBackToEnglish = false;
      } else {
        await _flutterTts.setLanguage('en-US');
        _fellBackToEnglish = _preferredLanguage != 'en';
      }

      // Configure TTS settings
      await _flutterTts.setSpeechRate(0.5);
      await _flutterTts.setVolume(1.0);
      await _flutterTts.setPitch(1.0);

      // Set up handlers to track speaking state
      _flutterTts.setStartHandler(() {
        _isSpeaking = true;
      });

      _flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
      });

      _flutterTts.setCancelHandler(() {
        _isSpeaking = false;
      });

      _flutterTts.setErrorHandler((msg) {
        _isSpeaking = false;
        // Silently handle error - don't crash the app
        print('TTS Error: $msg');
      });

      _isInitialized = true;
      return true;
    } catch (e) {
      // Silently fail - TTS is a nice-to-have feature
      print('TTS initialization failed: $e');
      _isInitialized = false;
      return false;
    }
  }

  /// Speak the given text
  /// Stops any currently playing speech before starting new one
  Future<void> speak(String? text) async {
    if (!_isInitialized) {
      return;
    }

    // Skip if text is null, empty, or whitespace only
    if (text == null || text.trim().isEmpty) {
      return;
    }

    try {
      // Stop current speech if playing
      if (_isSpeaking) {
        await stop();
      }

      // Speak the new text
      await _flutterTts.speak(text);
    } catch (e) {
      // Silently handle error
      print('TTS speak error: $e');
      _isSpeaking = false;
    }
  }

  /// Stop any currently playing speech
  Future<void> stop() async {
    if (!_isInitialized) {
      return;
    }

    try {
      await _flutterTts.stop();
      _isSpeaking = false;
    } catch (e) {
      // Silently handle error
      print('TTS stop error: $e');
      _isSpeaking = false;
    }
  }

  /// Dispose of the TTS service
  /// Stops any playing speech and cleans up resources
  Future<void> dispose() async {
    if (!_isInitialized) {
      return;
    }

    try {
      await stop();
      _isInitialized = false;
    } catch (e) {
      // Silently handle error
      print('TTS dispose error: $e');
    }
  }
}
