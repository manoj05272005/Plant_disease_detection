import 'auth_api.dart';
import 'api_config.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:passkeys/authenticator.dart';
import 'package:passkeys/types.dart';

class PasskeyAuthService {
  PasskeyAuthService({AuthApi? authApi, PasskeyAuthenticator? authenticator})
    : _authApi = authApi ?? AuthApi(),
      _authenticator = authenticator ?? PasskeyAuthenticator();

  final AuthApi _authApi;
  final PasskeyAuthenticator _authenticator;

  String get _expectedRpId =>
      ApiConfig.expectedPasskeyRpId.trim().toLowerCase();

  Future<Map<String, dynamic>> registerPasskey({
    required String username,
  }) async {
    try {
      final options = await _authApi.beginPasskeyRegistration(
        username: username,
      );

      _warnIfExpectedRpLooksInvalid();
      _validateRegistrationRpId(options);

      final request = RegisterRequestType.fromJson(options);
      final credential = await _authenticator.register(request);

      return _authApi.finishPasskeyRegistration(
        username: username,
        credential: credential.toJson(),
      );
    } catch (error) {
      throw _friendlyPasskeyError(error);
    }
  }

  Future<Map<String, dynamic>> loginWithPasskey({
    required String username,
  }) async {
    try {
      final options = await _authApi.beginPasskeyLogin(username: username);

      _warnIfExpectedRpLooksInvalid();
      _validateLoginRpId(options);

      final request = AuthenticateRequestType.fromJson(options);
      final credential = await _authenticator.authenticate(request);

      return _authApi.finishPasskeyLogin(
        username: username,
        credential: credential.toJson(),
      );
    } catch (error) {
      throw _friendlyPasskeyError(error);
    }
  }

  Exception _friendlyPasskeyError(Object error) {
    final lower = error.toString().toLowerCase();
    final isRpIdValidationError =
        lower.contains('rp id cannot be validated') ||
        lower.contains('rp id is not valid') ||
        lower.contains('rp id mismatch') ||
        lower.contains('type_data_error') ||
        lower.contains('type_create_public_key_credential_dom_exception');

    if (error is PlatformException && isRpIdValidationError) {
      return Exception(
        'Android passkey setup failed because RP ID is not valid for this app. '
        'Use a real HTTPS domain (not localhost/IP) for WEBAUTHN_RP_ID and '
        'configure /.well-known/assetlinks.json for your Android package.',
      );
    }

    if (isRpIdValidationError) {
      return Exception(
        'Passkey RP ID validation failed. Configure a real HTTPS domain RP ID '
        '(not localhost/IP) and Android Digital Asset Links.',
      );
    }

    if (error is Exception) {
      return error;
    }

    return Exception(error.toString());
  }

  void _validateRegistrationRpId(Map<String, dynamic> options) {
    final rp = options['rp'];
    if (rp is! Map<String, dynamic>) {
      throw Exception(
        'Passkey registration options are missing rp.id from backend.',
      );
    }

    final rpIdValue = rp['id'];
    if (rpIdValue is! String || rpIdValue.trim().isEmpty) {
      throw Exception('Passkey registration rp.id is missing or empty.');
    }

    final rpId = rpIdValue.trim().toLowerCase();
    _ensureRpIdMatchesExpected(rpId, flow: 'registration');
  }

  void _validateLoginRpId(Map<String, dynamic> options) {
    final rpIdValue = options['rpId'];
    if (rpIdValue is! String || rpIdValue.trim().isEmpty) {
      throw Exception('Passkey login rpId is missing or empty.');
    }

    final rpId = rpIdValue.trim().toLowerCase();
    _ensureRpIdMatchesExpected(rpId, flow: 'login');
  }

  void _ensureRpIdMatchesExpected(String rpId, {required String flow}) {
    if (_isLocalOrIp(rpId)) {
      throw Exception(
        'Backend WebAuthn RP ID is "$rpId" for $flow. '
        'Use a real HTTPS domain and configure /.well-known/assetlinks.json.',
      );
    }

    if (!_isRpRelatedToExpected(rpId, _expectedRpId)) {
      throw Exception(
        'Backend WebAuthn RP ID "$rpId" does not match app domain "$_expectedRpId" for $flow.',
      );
    }
  }

  bool _isRpRelatedToExpected(String rpId, String expected) {
    if (rpId == expected) {
      return true;
    }
    return expected.endsWith('.$rpId');
  }

  bool _isLocalOrIp(String value) {
    final lower = value.toLowerCase();
    if (lower == 'localhost') {
      return true;
    }
    final ipv4Regex = RegExp(r'^\d{1,3}(\.\d{1,3}){3}$');
    if (ipv4Regex.hasMatch(lower)) {
      return true;
    }
    // Heuristic for IPv6 literal forms used in config values.
    return lower.contains(':');
  }

  bool _looksLikeRealDomain(String value) {
    return value.contains('.') && !_isLocalOrIp(value);
  }

  void _warnIfExpectedRpLooksInvalid() {
    if (_looksLikeRealDomain(_expectedRpId)) {
      return;
    }

    debugPrint(
      'Passkey warning: ApiConfig.expectedPasskeyRpId is "$_expectedRpId". '
      'Android passkeys require a real HTTPS domain RP ID.',
    );
  }
}
