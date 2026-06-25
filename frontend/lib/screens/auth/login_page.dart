import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../services/auth_api.dart';
import '../../services/passkey_auth_service.dart';
import '../../services/token_storage.dart';
import '../../services/app_localizations.dart';
import 'forgot_password_page.dart';
import 'register_page.dart';
import '../home_page.dart';

// Screen for user sign-in.
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  static const String routeName = '/login';

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _api = AuthApi();
  final _passkeyAuth = PasskeyAuthService();
  final _tokenStorage = const TokenStorage();

  bool _isLoading = false;
  bool _isPasskeyLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Validate credentials and exchange for tokens.
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _api.login(
        username: _emailController.text.trim(),
        password: _passwordController.text,
      );

      final accessToken = result['access_token']?.toString();
      final refreshToken = result['refresh_token']?.toString();
      final tokenType = result['token_type']?.toString();

      if (accessToken == null || refreshToken == null) {
        throw Exception('Missing tokens in response.');
      }

      await _tokenStorage.saveTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        tokenType: tokenType,
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.tRead('Login successful.'))),
      );
      Navigator.pushReplacementNamed(context, HomePage.routeName);
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
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map<String, dynamic> && data.containsKey('detail')) {
        return data['detail'].toString();
      }
      if (error.response?.statusCode == 401) {
        return 'Incorrect email or password.';
      }
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout) {
        return 'Connection timed out. Please try again.';
      }
      if (error.type == DioExceptionType.connectionError) {
        return 'Unable to connect to server. Check your internet connection.';
      }
      return 'Something went wrong. Please try again.';
    }
    final message = error.toString();
    return message.replaceFirst('Exception: ', '');
  }

  Future<void> _submitPasskeyLogin() async {
    final username = _emailController.text.trim();
    if (username.isEmpty) {
      setState(() {
        _errorMessage = 'Enter your email or phone to use passkey login.';
      });
      return;
    }

    setState(() {
      _isPasskeyLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _passkeyAuth.loginWithPasskey(username: username);
      final accessToken = result['access_token']?.toString();
      final refreshToken = result['refresh_token']?.toString();
      final tokenType = result['token_type']?.toString();

      if (accessToken == null || refreshToken == null) {
        throw Exception('Missing tokens in passkey response.');
      }

      await _tokenStorage.saveTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        tokenType: tokenType,
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passkey login successful.')),
      );
      Navigator.pushReplacementNamed(context, HomePage.routeName);
    } catch (error) {
      setState(() {
        _errorMessage = _friendlyError(error);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isPasskeyLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: Text(context.t('Sign in'))),
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
                        Image.asset('assets/logo.png', width: 48, height: 48),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.t('AgroScan'),
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            Text(
                              context.t('Sign in to continue'),
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
                                controller: _emailController,
                                decoration: InputDecoration(
                                  labelText: context.t('Email'),
                                ),
                                keyboardType: TextInputType.emailAddress,
                                textInputAction: TextInputAction.next,
                                validator: (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return context.tRead('Email is required.');
                                  }
                                  return null;
                                },
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _passwordController,
                                decoration: InputDecoration(
                                  labelText: context.t('Password'),
                                ),
                                obscureText: true,
                                textInputAction: TextInputAction.done,
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return context.tRead(
                                      'Password is required.',
                                    );
                                  }
                                  if (value.length < 6) {
                                    return context.tRead(
                                      'Password must be at least 6 characters.',
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
                                    : Text(context.t('Login')),
                              ),
                              const SizedBox(height: 8),
                              OutlinedButton.icon(
                                onPressed: (_isLoading || _isPasskeyLoading)
                                    ? null
                                    : _submitPasskeyLogin,
                                icon: _isPasskeyLoading
                                    ? const SizedBox(
                                        height: 16,
                                        width: 16,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : const Icon(Icons.key),
                                label: const Text('Use Passkey'),
                              ),
                              const SizedBox(height: 8),
                              TextButton(
                                onPressed: () {
                                  Navigator.pushNamed(
                                    context,
                                    ForgotPasswordPage.routeName,
                                  );
                                },
                                child: Text(context.t('Forgot password?')),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(context.t('New here?')),
                        TextButton(
                          onPressed: () {
                            Navigator.pushNamed(
                              context,
                              RegisterPage.routeName,
                            );
                          },
                          child: Text(context.t('Create account')),
                        ),
                      ],
                    ),
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
