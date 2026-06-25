import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../services/auth_api.dart';
import '../../services/passkey_auth_service.dart';
import '../../services/location_service.dart';
import '../../services/app_localizations.dart';

// Screen for new user registration.
class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  static const String routeName = '/register';

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _addressController = TextEditingController();
  final List<Map<String, String>> _countryCodes = const [
    {'code': '+91', 'label': 'India (+91)'},
    {'code': '+1', 'label': 'USA (+1)'},
    {'code': '+44', 'label': 'UK (+44)'},
    {'code': '+61', 'label': 'Australia (+61)'},
    {'code': '+65', 'label': 'Singapore (+65)'},
  ];
  String _selectedCountryCode = '+91';
  final List<Map<String, String>> _languages = const [
    {'code': 'en', 'label': 'English'},
    {'code': 'hi', 'label': 'हिन्दी'},
    {'code': 'ta', 'label': 'தமிழ்'},
    {'code': 'te', 'label': 'తెలుగు'},
    {'code': 'kn', 'label': 'ಕನ್ನಡ'},
    {'code': 'ml', 'label': 'മലയാളം'},
  ];
  String _selectedLanguage = 'en';

  final _api = AuthApi();
  final _passkeyAuth = PasskeyAuthService();
  final _locationService = const LocationService();

  bool _isLoading = false;
  String? _errorMessage;
  LocationData? _location;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Capture GPS once to enrich the new profile.
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final location = await _locationService.getCurrentLocation();
      _location = location;

      final email = _emailController.text.trim();
      final phone = '$_selectedCountryCode${_phoneController.text.trim()}';

      await _api.register(
        name: _nameController.text.trim(),
        email: email,
        phone: phone,
        password: _passwordController.text,
        preferredLanguage: _selectedLanguage,
        latitude: location.latitude,
        longitude: location.longitude,
        address: _addressController.text.trim(),
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.tRead('Registration complete.'))),
      );

      final shouldEnroll = await _askToEnrollPasskey();
      if (shouldEnroll == true) {
        final username = email.isNotEmpty ? email : phone;
        await _enrollPasskey(username);
      }

      Navigator.pop(context);
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

  Future<bool?> _askToEnrollPasskey() {
    return showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Set up passkey?'),
          content: const Text(
            'You can add a passkey now for passwordless sign-in next time.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Not now'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Set up'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _enrollPasskey(String username) async {
    try {
      await _passkeyAuth.registerPasskey(username: username);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passkey registered successfully.')),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Passkey setup skipped: ${_friendlyError(error)}'),
        ),
      );
    }
  }

  String _friendlyError(Object error) {
    if (error is DioException && error.response != null) {
      final data = error.response!.data;
      if (data is Map<String, dynamic>) {
        final detail = data['detail'];
        if (detail is List) {
          // Pydantic validation errors: [{msg: ..., loc: [...]}]
          return detail
              .map((e) => '${e['loc']?.last ?? ''}: ${e['msg']}')
              .join('\n');
        }
        if (detail is String) {
          return detail;
        }
      }
    }
    final message = error.toString();
    return message.replaceFirst('Exception: ', '');
  }

  @override
  Widget build(BuildContext context) {
    final locationText = _location == null
        ? context.t('Location will be captured automatically.')
        : context.t(
            'Location: {lat}, {lng}',
            args: {
              'lat': _location!.latitude.toStringAsFixed(5),
              'lng': _location!.longitude.toStringAsFixed(5),
            },
          );

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: Text(context.t('Create account title'))),
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
                            Icons.landscape,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.t('Join the community'),
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            Text(
                              context.t('GPS helps personalize your reports'),
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
                                controller: _nameController,
                                decoration: InputDecoration(
                                  labelText: context.t('Full name'),
                                ),
                                textInputAction: TextInputAction.next,
                                validator: (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return context.tRead('Name is required.');
                                  }
                                  if (value.trim().length < 2) {
                                    return context.tRead(
                                      'Name must be at least 2 characters.',
                                    );
                                  }
                                  return null;
                                },
                              ),
                              const SizedBox(height: 16),
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
                              Row(
                                children: [
                                  Expanded(
                                    flex: 3,
                                    child: DropdownButtonFormField<String>(
                                      value: _selectedCountryCode,
                                      decoration: InputDecoration(
                                        labelText: context.t('Code'),
                                        isDense: true,
                                        contentPadding: EdgeInsets.symmetric(
                                          horizontal: 12,
                                          vertical: 12,
                                        ),
                                      ),
                                      isExpanded: true,
                                      items: _countryCodes
                                          .map(
                                            (country) =>
                                                DropdownMenuItem<String>(
                                                  value: country['code'],
                                                  child: Text(
                                                    country['label'] ?? '',
                                                    overflow:
                                                        TextOverflow.ellipsis,
                                                  ),
                                                ),
                                          )
                                          .toList(),
                                      onChanged: (value) {
                                        if (value == null) {
                                          return;
                                        }
                                        setState(() {
                                          _selectedCountryCode = value;
                                        });
                                      },
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    flex: 5,
                                    child: TextFormField(
                                      controller: _phoneController,
                                      decoration: InputDecoration(
                                        labelText: context.t('Phone'),
                                      ),
                                      keyboardType: TextInputType.phone,
                                      textInputAction: TextInputAction.next,
                                      validator: (value) {
                                        if (value == null ||
                                            value.trim().isEmpty) {
                                          return context.tRead(
                                            'Phone is required.',
                                          );
                                        }
                                        return null;
                                      },
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _passwordController,
                                decoration: InputDecoration(
                                  labelText: context.t('Password'),
                                ),
                                obscureText: true,
                                textInputAction: TextInputAction.next,
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return context.tRead(
                                      'Password is required.',
                                    );
                                  }
                                  if (value.length < 8) {
                                    return context.tRead(
                                      'Password must be at least 8 characters.',
                                    );
                                  }
                                  return null;
                                },
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _addressController,
                                decoration: InputDecoration(
                                  labelText: context.t('Address'),
                                ),
                                textInputAction: TextInputAction.next,
                                validator: (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return context.tRead(
                                      'Address is required.',
                                    );
                                  }
                                  return null;
                                },
                              ),
                              const SizedBox(height: 16),
                              DropdownButtonFormField<String>(
                                value: _selectedLanguage,
                                decoration: InputDecoration(
                                  labelText: context.t('Preferred language'),
                                ),
                                items: _languages
                                    .map(
                                      (language) => DropdownMenuItem<String>(
                                        value: language['code'],
                                        child: Text(language['label'] ?? ''),
                                      ),
                                    )
                                    .toList(),
                                onChanged: (value) {
                                  if (value == null) {
                                    return;
                                  }
                                  setState(() {
                                    _selectedLanguage = value;
                                  });
                                },
                              ),
                              const SizedBox(height: 12),
                              Text(
                                locationText,
                                style: Theme.of(context).textTheme.bodySmall,
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
                                    : Text(context.t('Create account')),
                              ),
                            ],
                          ),
                        ),
                      ),
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
