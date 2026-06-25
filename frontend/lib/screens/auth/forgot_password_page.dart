import 'package:flutter/material.dart';

import '../../services/auth_api.dart';
import '../../services/app_localizations.dart';

// Screen for requesting and completing password reset.
class ForgotPasswordPage extends StatefulWidget {
  const ForgotPasswordPage({super.key});

  static const String routeName = '/forgot-password';

  @override
  State<ForgotPasswordPage> createState() => _ForgotPasswordPageState();
}

class _ForgotPasswordPageState extends State<ForgotPasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _resetFormKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _api = AuthApi();

  bool _isLoading = false;
  bool _showResetForm = false;
  String? _resetToken;
  String? _message;
  String? _errorMessage;

  @override
  void dispose() {
    _usernameController.dispose();
    _otpController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Step 1: request reset token/OTP.
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _message = null;
    });

    try {
      final result = await _api.forgotPassword(
        username: _usernameController.text.trim(),
      );

      final message =
          result['message']?.toString() ??
          context.tRead('If the account exists, a reset code will be sent.');

      if (!mounted) {
        return;
      }

      setState(() {
        _message = message;
        _resetToken = result['reset_token']?.toString();
        _showResetForm = true;
        // If the server returned the OTP directly (email service
        // unavailable), pre-fill it so the user can proceed.
        final otp = result['otp']?.toString();
        if (otp != null && otp.isNotEmpty) {
          _otpController.text = otp;
        }
      });
    } catch (error) {
      setState(() {
        _errorMessage = _friendlyError(error);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _submitReset() async {
    // Step 2: verify OTP and set new password.
    if (!_resetFormKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      if (_resetToken == null || _resetToken!.isEmpty) {
        throw Exception('Reset token is missing.');
      }

      final result = await _api.resetPassword(
        token: _resetToken!,
        otp: _otpController.text.trim(),
        newPassword: _newPasswordController.text,
      );

      final message =
          result['message']?.toString() ??
          context.tRead('Password reset successful. You can log in now.');

      if (!mounted) {
        return;
      }

      setState(() {
        _message = message;
      });
    } catch (error) {
      setState(() {
        _errorMessage = _friendlyError(error);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  String _friendlyError(Object error) {
    // Try to extract a human-readable message from DioException.
    if (error is Exception) {
      final raw = error.toString();
      // DioException contains the server "detail" in its message.
      // Try to pull it out; otherwise return a generic message.
      final detailMatch = RegExp(r'"detail"\s*:\s*"([^"]+)"').firstMatch(raw);
      if (detailMatch != null) {
        return detailMatch.group(1)!;
      }
    }
    return context.tRead('Something went wrong. Please try again.');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: Text(context.t('Reset password'))),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFF5F1EA), Color(0xFFE7F0E8)],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          radius: 24,
                          backgroundColor: Theme.of(
                            context,
                          ).colorScheme.primary.withOpacity(0.12),
                          child: Icon(
                            Icons.lock_reset,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.t('Forgot your password?'),
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            Text(
                              context.t('We will send a reset code'),
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Form(
                          key: _formKey,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              TextFormField(
                                controller: _usernameController,
                                decoration: InputDecoration(
                                  labelText: context.t('Email or phone'),
                                ),
                                textInputAction: TextInputAction.done,
                                validator: (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return context.t(
                                      'Email or phone is required.',
                                    );
                                  }
                                  return null;
                                },
                              ),
                              const SizedBox(height: 12),
                              if (_errorMessage != null)
                                Text(
                                  _errorMessage!,
                                  style: TextStyle(
                                    color: Theme.of(context).colorScheme.error,
                                  ),
                                ),
                              if (_message != null)
                                Text(
                                  _message!,
                                  style: TextStyle(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.primary,
                                  ),
                                ),
                              const SizedBox(height: 12),
                              ElevatedButton(
                                onPressed: _isLoading ? null : _submit,
                                child: _isLoading
                                    ? const SizedBox(
                                        height: 18,
                                        width: 18,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : Text(context.t('Send reset code')),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    if (_showResetForm) ...[
                      const SizedBox(height: 20),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Form(
                            key: _resetFormKey,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Text(
                                  context.t(
                                    'Enter the OTP sent to your email.',
                                  ),
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _otpController,
                                  decoration: InputDecoration(
                                    labelText: context.t('OTP'),
                                  ),
                                  keyboardType: TextInputType.number,
                                  textInputAction: TextInputAction.next,
                                  validator: (value) {
                                    if (value == null || value.trim().isEmpty) {
                                      return context.t('OTP is required.');
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 12),
                                TextFormField(
                                  controller: _newPasswordController,
                                  decoration: InputDecoration(
                                    labelText: context.t('New password'),
                                  ),
                                  obscureText: true,
                                  textInputAction: TextInputAction.done,
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return context.t(
                                        'New password is required.',
                                      );
                                    }
                                    if (value.length < 8) {
                                      return context.t(
                                        'Password must be at least 6 characters.',
                                      );
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 12),
                                ElevatedButton(
                                  onPressed: _isLoading ? null : _submitReset,
                                  child: _isLoading
                                      ? const SizedBox(
                                          height: 18,
                                          width: 18,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : Text(
                                          context.t('Reset password button'),
                                        ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
