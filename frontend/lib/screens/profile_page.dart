import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/location_service.dart';
import '../services/passkey_auth_service.dart';
import '../services/token_storage.dart';
import '../services/user_api.dart';
import '../services/app_localizations.dart';

// Screen for viewing and updating user profile settings.
class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  static const String routeName = '/profile';

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _locationService = const LocationService();
  final _tokenStorage = const TokenStorage();
  final _userApi = UserApi();
  final _passkeyAuth = PasskeyAuthService();

  final List<Map<String, String>> _languages = const [
    {'code': 'en', 'label': 'English'},
    {'code': 'hi', 'label': 'हिन्दी'},
    {'code': 'ta', 'label': 'தமிழ்'},
    {'code': 'te', 'label': 'తెలుగు'},
    {'code': 'kn', 'label': 'ಕನ್ನಡ'},
    {'code': 'ml', 'label': 'മലയാളം'},
  ];

  bool _isLoading = false;
  bool _isPasskeyLoading = false;
  bool _isUpdatingLocation = false;
  String? _errorMessage;
  String _selectedLanguage = 'en';

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    // Load cached profile first, then refresh from server.
    final cached = await _tokenStorage.readUserProfile();
    if (cached != null) {
      _applyProfile(cached);
    }

    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      return;
    }

    try {
      final profile = await _userApi.getProfile(accessToken: accessToken);
      await _tokenStorage.saveUserProfile(profile);
      if (!mounted) {
        return;
      }
      _applyProfile(profile);
    } catch (_) {
      // Keep cached data if request fails.
    }
  }

  void _applyProfile(Map<String, dynamic> profile) {
    _nameController.text = profile['name']?.toString() ?? '';
    _emailController.text = profile['email']?.toString() ?? '';
    _phoneController.text = profile['phone']?.toString() ?? '';

    final preferredLanguage = profile['preferred_language']?.toString();
    if (preferredLanguage != null && preferredLanguage.isNotEmpty) {
      _selectedLanguage = preferredLanguage;
    }

    final location = profile['location'];
    if (location is Map<String, dynamic>) {
      // keep location cached via profile, no user input required
    }

    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _updateProfile() async {
    // Update profile with latest GPS location.
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      setState(() {
        _errorMessage = context.tRead('Missing access token.');
      });
      return;
    }

    setState(() {
      _isUpdatingLocation = true;
    });

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final location = await _locationService.getCurrentLocation();
      final profile = await _userApi.updateProfile(
        accessToken: accessToken,
        name: _nameController.text.trim(),
        preferredLanguage: _selectedLanguage,
        latitude: location.latitude,
        longitude: location.longitude,
      );

      await _tokenStorage.saveUserProfile(profile);

      if (!mounted) {
        return;
      }

      _applyProfile(profile);
      context.read<AppLanguage>().setLanguage(_selectedLanguage);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.tRead('Profile updated.'))),
      );
    } catch (error) {
      setState(() {
        _errorMessage = error.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _isUpdatingLocation = false;
        });
      }
    }
  }

  Future<void> _addPasskey() async {
    final username = _emailController.text.trim().isNotEmpty
        ? _emailController.text.trim()
        : _phoneController.text.trim();

    if (username.isEmpty) {
      setState(() {
        _errorMessage = 'Email or phone is required to register a passkey.';
      });
      return;
    }

    setState(() {
      _isPasskeyLoading = true;
      _errorMessage = null;
    });

    try {
      await _passkeyAuth.registerPasskey(username: username);

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passkey registered successfully.')),
      );
    } catch (error) {
      setState(() {
        _errorMessage = error.toString().replaceFirst('Exception: ', '');
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
      appBar: AppBar(title: Text(context.t('Profile'))),
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
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Form(
                      key: _formKey,
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
                                  Icons.person,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Text(
                                context.t('Personal details'),
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _nameController,
                            decoration: InputDecoration(
                              labelText: context.t('Name'),
                            ),
                            textInputAction: TextInputAction.next,
                            validator: (value) {
                              if (value == null || value.trim().isEmpty) {
                                return context.t('Name is required.');
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
                            readOnly: true,
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _phoneController,
                            decoration: InputDecoration(
                              labelText: context.t('Phone'),
                            ),
                            readOnly: true,
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
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  context.t(
                                    'Location will be updated using GPS when you save.',
                                  ),
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ),
                              if (_isUpdatingLocation)
                                const SizedBox(
                                  height: 18,
                                  width: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                ),
                            ],
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
                            onPressed: (_isLoading || _isPasskeyLoading)
                                ? null
                                : _updateProfile,
                            child: _isLoading
                                ? const SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Text(context.t('Update profile')),
                          ),
                          const SizedBox(height: 8),
                          OutlinedButton.icon(
                            onPressed: (_isLoading || _isPasskeyLoading)
                                ? null
                                : _addPasskey,
                            icon: _isPasskeyLoading
                                ? const SizedBox(
                                    height: 16,
                                    width: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.key),
                            label: const Text('Add Passkey'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
