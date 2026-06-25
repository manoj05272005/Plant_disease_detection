import 'package:flutter/material.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:provider/provider.dart';

import '../services/location_service.dart';
import '../services/history_api.dart';
import '../services/auth_api.dart';
import '../services/token_storage.dart';
import '../services/user_api.dart';
import '../services/weather_api.dart';
import '../services/diagnosis_api.dart';
import '../services/notification_api.dart';
import '../services/app_localizations.dart';
import '../services/diagnosis_cache.dart';
import 'auth/login_page.dart';
import 'crop_capture_page.dart';
import 'diagnosis_result_page.dart';
import 'profile_page.dart';
import 'chatbot_page.dart';

// Dashboard screen for weather, history, and actions.
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  static const String routeName = '/home';

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _tokenStorage = const TokenStorage();
  final _userApi = UserApi();
  final _locationService = const LocationService();
  final _weatherApi = WeatherApi();
  final _historyApi = HistoryApi();
  final _diagnosisApi = DiagnosisApi();
  final _diagnosisCache = DiagnosisCacheService();
  final _authApi = AuthApi();
  final _notificationApi = NotificationApi();
  Map<String, dynamic>? _profile;
  bool _isRefreshingProfile = false;
  WeatherInfo? _weatherInfo;
  String? _weatherError;
  bool _isLoadingWeather = false;
  Map<String, dynamic>? _historyAnalytics;
  List<Map<String, dynamic>> _historyItems = [];
  List<Map<String, dynamic>> _offlineHistoryItems = [];
  bool _isLoadingHistory = false;
  bool _isOnline = false;
  String? _selectedCropFilter;

  Future<void> _logout() async {
    await _tokenStorage.clearTokens();

    if (!mounted) {
      return;
    }

    Navigator.pushNamedAndRemoveUntil(
      context,
      LoginPage.routeName,
      (route) => false,
    );
  }

  Future<void> _refreshProfile() async {
    if (_isRefreshingProfile) {
      return;
    }

    setState(() {
      _isRefreshingProfile = true;
    });

    try {
      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken == null || accessToken.isEmpty) {
        return;
      }

      final profile = await _userApi.getProfile(accessToken: accessToken);
      await _tokenStorage.saveUserProfile(profile);
      if (!mounted) {
        return;
      }
      context.read<AppLanguage>().setLanguage(
        profile['preferred_language']?.toString(),
      );
      setState(() {
        _profile = profile;
      });
    } catch (_) {
      // Keep cached profile if refresh fails.
    } finally {
      if (mounted) {
        setState(() {
          _isRefreshingProfile = false;
        });
      }
    }
  }

  Future<void> _loadCachedProfile() async {
    final cached = await _tokenStorage.readUserProfile();
    if (cached != null && mounted) {
      context.read<AppLanguage>().setLanguage(
        cached['preferred_language']?.toString(),
      );
      setState(() {
        _profile = cached;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    // Load cached content, then refresh from network.
    _initializeData();
    _updateConnectivity();
  }

  Future<void> _initializeData() async {
    // Prime tokens before hitting authenticated endpoints.
    await _refreshTokenIfWifi();
    _loadCachedProfile();
    _refreshProfile();
    _loadCachedWeather();
    _loadWeather();
    _loadCachedHistory();
    _loadCachedOfflineHistory();
    _loadCachedAnalytics();
    _loadHistory();
    _loadAnalytics();
  }

  Future<void> _updateConnectivity() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (!mounted) {
      return;
    }
    setState(() {
      _isOnline =
          connectivity.contains(ConnectivityResult.wifi) ||
          connectivity.contains(ConnectivityResult.mobile);
    });
  }

  Future<void> _refreshTokenIfWifi() async {
    // Avoid refresh on mobile data to reduce usage.
    final connectivity = await Connectivity().checkConnectivity();
    if (!connectivity.contains(ConnectivityResult.wifi)) {
      return;
    }

    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return;
    }

    try {
      final result = await _authApi.refreshToken(refreshToken: refreshToken);

      final accessToken = result['access_token']?.toString();
      final newRefreshToken = result['refresh_token']?.toString();
      final tokenType = result['token_type']?.toString();

      if (accessToken == null || newRefreshToken == null) {
        return;
      }

      await _tokenStorage.saveTokens(
        accessToken: accessToken,
        refreshToken: newRefreshToken,
        tokenType: tokenType,
      );
    } catch (_) {
      // Ignore refresh errors and keep existing tokens.
    }
  }

  Future<void> _loadCachedHistory() async {
    // Render cache first for faster UI.
    final cached = await _tokenStorage.readHistory();
    if (cached != null && mounted) {
      setState(() {
        _historyItems = cached;
      });
    }
  }

  Future<void> _loadCachedOfflineHistory() async {
    final cached = await _tokenStorage.readOfflineHistory();
    if (cached != null && mounted) {
      setState(() {
        _offlineHistoryItems = cached;
      });
    }
  }

  Future<void> _loadCachedAnalytics() async {
    final cached = await _tokenStorage.readHistoryAnalytics();
    if (cached != null && mounted) {
      setState(() {
        _historyAnalytics = cached;
      });
    }
  }

  Future<void> _loadCachedWeather() async {
    final cached = await _tokenStorage.readWeather();
    if (cached != null && mounted) {
      setState(() {
        _weatherInfo = WeatherInfo.fromJson(cached);
      });
    }
  }

  Future<void> _loadHistory() async {
    if (_isLoadingHistory) {
      return;
    }

    setState(() {
      _isLoadingHistory = true;
    });

    try {
      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken == null || accessToken.isEmpty) {
        return;
      }

      final history = await _historyApi.getHistory(accessToken: accessToken);

      await _tokenStorage.saveHistory(history);

      if (!mounted) {
        return;
      }

      setState(() {
        _historyItems = history;
      });
    } catch (_) {
      // Keep cached history if request fails.
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingHistory = false;
        });
      }
    }
  }

  Future<void> _loadAnalytics() async {
    try {
      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken == null || accessToken.isEmpty) {
        return;
      }

      final analytics = await _historyApi.getAnalytics(
        accessToken: accessToken,
      );

      await _tokenStorage.saveHistoryAnalytics(analytics);

      if (!mounted) {
        return;
      }

      setState(() {
        _historyAnalytics = analytics;
      });
    } catch (_) {
      // Keep cached analytics if request fails.
    }
  }

  Future<void> _openHistoryDiagnosis(Map<String, dynamic> item) async {
    // Try live fetch, fall back to cached diagnosis.
    final diagnosisId = _resolveHistoryDiagnosisId(item);
    if (diagnosisId.isEmpty) {
      return;
    }

    final isOfflineItem = item['is_offline'] == true;
    if (isOfflineItem) {
      await _openCachedDiagnosis(diagnosisId, item);
      return;
    }

    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      await _openCachedDiagnosis(diagnosisId, item);
      return;
    }

    try {
      final profile = await _tokenStorage.readUserProfile();
      final language = profile?['preferred_language']?.toString();
      final diagnosis = await _diagnosisApi.getDiagnosis(
        accessToken: accessToken,
        diagnosisId: diagnosisId,
        language: language,
      );
      final cachedDiagnosis = await _diagnosisCache.cacheDiagnosisImages(
        diagnosisId: diagnosisId,
        result: diagnosis,
      );

      await _tokenStorage.saveDiagnosisResult(
        diagnosisId: diagnosisId,
        result: cachedDiagnosis,
      );

      if (!mounted) {
        return;
      }

      final cropLabel = item['crop_type']?.toString() ?? 'Crop';
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => DiagnosisResultPage(
            cropLabel: cropLabel,
            result: cachedDiagnosis,
          ),
        ),
      );
    } catch (error) {
      final opened = await _openCachedDiagnosis(diagnosisId, item);
      if (!opened && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', '')),
          ),
        );
      }
    }
  }

  String _resolveHistoryDiagnosisId(Map<String, dynamic> item) {
    final diagnosisId = item['diagnosis_id']?.toString();
    if (diagnosisId != null && diagnosisId.isNotEmpty) {
      return diagnosisId;
    }
    final id = item['_id']?.toString();
    if (id != null && id.isNotEmpty) {
      return id;
    }
    return '';
  }

  Future<bool> _openCachedDiagnosis(
    String diagnosisId,
    Map<String, dynamic> item,
  ) async {
    final cached = await _tokenStorage.readDiagnosisResult(diagnosisId);
    if (cached == null || !mounted) {
      return false;
    }

    final cropLabel = item['crop_type']?.toString() ?? 'Crop';
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) =>
            DiagnosisResultPage(cropLabel: cropLabel, result: cached),
      ),
    );
    return true;
  }

  Future<void> _deleteHistoryItem(String historyId) async {
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      return;
    }

    try {
      await _historyApi.deleteHistory(
        accessToken: accessToken,
        historyId: historyId,
      );

      final updated = _historyItems
          .where((item) => item['_id']?.toString() != historyId)
          .toList();
      await _tokenStorage.saveHistory(updated);

      if (!mounted) {
        return;
      }

      setState(() {
        _historyItems = updated;
      });

      _loadAnalytics();
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error.toString().replaceFirst('Exception: ', '')),
        ),
      );
    }
  }

  Future<void> _downloadReport(String diagnosisId) async {
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      return;
    }

    try {
      final path = await _historyApi.downloadReport(
        accessToken: accessToken,
        diagnosisId: diagnosisId,
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            context.tRead('Report saved: {path}', args: {'path': path}),
          ),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error.toString().replaceFirst('Exception: ', '')),
        ),
      );
    }
  }

  Future<void> _deleteOfflineHistoryItem(String historyId) async {
    if (historyId.isEmpty) {
      return;
    }

    final updated = _offlineHistoryItems.where((item) {
      final currentId = item['_id']?.toString();
      final currentDiagnosisId = item['diagnosis_id']?.toString();
      return currentId != historyId && currentDiagnosisId != historyId;
    }).toList();

    final removedDiagnosisIds = _offlineHistoryItems
        .where((item) {
          final currentId = item['_id']?.toString();
          final currentDiagnosisId = item['diagnosis_id']?.toString();
          return currentId == historyId || currentDiagnosisId == historyId;
        })
        .map(_resolveHistoryDiagnosisId)
        .where((id) => id.isNotEmpty)
        .toSet();

    await _tokenStorage.saveOfflineHistory(updated);
    for (final diagnosisId in removedDiagnosisIds) {
      await _tokenStorage.removeDiagnosisResult(diagnosisId);
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _offlineHistoryItems = updated;
    });
  }

  Future<void> _loadWeather() async {
    if (_isLoadingWeather) {
      return;
    }

    // Don't fetch if offline - just use cached weather
    if (!_isOnline) {
      return;
    }

    setState(() {
      _isLoadingWeather = true;
      _weatherError = null;
    });

    try {
      final location = await _locationService.getCurrentLocation();
      final weather = await _weatherApi.getCurrentWeather(
        latitude: location.latitude,
        longitude: location.longitude,
      );

      await _tokenStorage.saveWeather(weather.toJson());

      if (!mounted) {
        return;
      }

      setState(() {
        _weatherInfo = weather;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      // Only show error if we don't have cached weather to display
      if (_weatherInfo == null) {
        setState(() {
          _weatherError = error.toString().replaceFirst('Exception: ', '');
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingWeather = false;
        });
      }
    }
  }

  Future<void> _showNotifications() async {
    // Show notifications in a bottom sheet.
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(context.tRead('Please log in to view notifications.')),
        ),
      );
      return;
    }

    if (!mounted) {
      return;
    }

    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) {
        return _NotificationsSheet(
          accessToken: accessToken,
          notificationApi: _notificationApi,
          tokenStorage: _tokenStorage,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final profileMenuLabel = context.t('Profile menu');
    final logoutLabel = context.t('Logout');
    final cropOptions =
        [..._offlineHistoryItems, ..._historyItems]
            .map((item) => item['crop_type']?.toString() ?? '')
            .where((value) => value.isNotEmpty)
            .toSet()
            .toList()
          ..sort();
    final allHistoryItems = [..._offlineHistoryItems, ..._historyItems]
      ..sort((a, b) {
        final aDate = DateTime.tryParse(a['created_at']?.toString() ?? '');
        final bDate = DateTime.tryParse(b['created_at']?.toString() ?? '');
        if (aDate == null && bDate == null) {
          return 0;
        }
        if (aDate == null) {
          return 1;
        }
        if (bDate == null) {
          return -1;
        }
        return bDate.compareTo(aDate);
      });
    final filteredHistory = _selectedCropFilter == null
        ? allHistoryItems
        : allHistoryItems
              .where(
                (item) => item['crop_type']?.toString() == _selectedCropFilter,
              )
              .toList();
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Image.asset('assets/logo.png', width: 28, height: 28),
            const SizedBox(width: 10),
            Flexible(
              child: Text(
                context.t('AgroScan'),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _initializeData,
            icon: const Icon(Icons.refresh),
            tooltip: context.t('Refresh'),
          ),
          IconButton(
            onPressed: _showNotifications,
            icon: const Icon(Icons.notifications_outlined),
            tooltip: context.t('Notifications'),
          ),
          Icon(
            _isOnline ? Icons.wifi : Icons.wifi_off,
            color: _isOnline ? scheme.primary : scheme.error,
          ),
          const SizedBox(width: 8),
          PopupMenuButton<String>(
            icon: const Icon(Icons.account_circle),
            onSelected: (value) {
              if (value == 'profile') {
                Navigator.pushNamed(context, ProfilePage.routeName);
              } else if (value == 'logout') {
                _logout();
              }
            },
            itemBuilder: (context) => [
              PopupMenuItem(value: 'profile', child: Text(profileMenuLabel)),
              PopupMenuItem(value: 'logout', child: Text(logoutLabel)),
            ],
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFF5F1EA), Color(0xFFE7F0E8)],
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: scheme.primary.withOpacity(0.12),
                        child: Icon(Icons.eco, color: scheme.primary, size: 28),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.t(
                                'Welcome, {name}',
                                args: {
                                  'name':
                                      _profile?['name']?.toString() ?? 'Farmer',
                                },
                              ),
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _profile?['email']?.toString() ?? '-',
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                      Chip(
                        label: Text(
                          _isOnline
                              ? context.t('Online')
                              : context.t('Offline'),
                        ),
                        backgroundColor: _isOnline
                            ? scheme.primary.withOpacity(0.12)
                            : null,
                        labelStyle: TextStyle(
                          color: _isOnline ? scheme.primary : scheme.error,
                          fontWeight: FontWeight.w600,
                        ),
                        side: BorderSide(
                          color: _isOnline ? scheme.primary : scheme.error,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (_isRefreshingProfile)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: LinearProgressIndicator(),
                ),
              const SizedBox(height: 20),
              _SectionHeader(
                title: context.t('Current weather'),
                subtitle: context.t('Live conditions near your farm'),
              ),
              const SizedBox(height: 12),
              if (_weatherInfo != null)
                Stack(
                  children: [
                    _WeatherCard(weather: _weatherInfo!),
                    if (_isLoadingWeather)
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                        ),
                      ),
                  ],
                )
              else if (_isLoadingWeather)
                const Center(child: CircularProgressIndicator())
              else
                Text(context.t('Weather data unavailable.')),
              const SizedBox(height: 24),
              _SectionHeader(
                title: context.t('History analytics'),
                subtitle: context.t('Trends from your recent scans'),
              ),
              const SizedBox(height: 12),
              _AnalyticsCard(analytics: _historyAnalytics),
              const SizedBox(height: 24),
              _SectionHeader(
                title: context.t('History records'),
                subtitle: context.t('Download or remove past reports'),
              ),
              const SizedBox(height: 8),
              if (cropOptions.isNotEmpty)
                DropdownButtonFormField<String>(
                  value: _selectedCropFilter,
                  decoration: InputDecoration(
                    labelText: context.t('Filter by crop'),
                  ),
                  items: [
                    DropdownMenuItem<String>(
                      value: null,
                      child: Text(context.t('All crops')),
                    ),
                    ...cropOptions.map(
                      (crop) => DropdownMenuItem<String>(
                        value: crop,
                        child: Text(crop),
                      ),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selectedCropFilter = value;
                    });
                  },
                ),
              const SizedBox(height: 12),
              if (_isLoadingHistory)
                const Center(child: CircularProgressIndicator())
              else if (filteredHistory.isEmpty)
                Text(context.t('No history yet.'))
              else
                ...filteredHistory.map((item) {
                  final isOfflineItem = item['is_offline'] == true;
                  final historyId = _resolveHistoryDiagnosisId(item);
                  final diagnosisId = _resolveHistoryDiagnosisId(item);
                  return _HistoryCard(
                    item: item,
                    onOpen: () => _openHistoryDiagnosis(item),
                    onDelete: () => isOfflineItem
                        ? _deleteOfflineHistoryItem(historyId)
                        : _deleteHistoryItem(historyId),
                    onDownload: isOfflineItem
                        ? null
                        : () => _downloadReport(diagnosisId),
                    actionsEnabled: isOfflineItem ? true : _isOnline,
                  );
                }),
            ],
          ),
        ),
      ),
      floatingActionButton: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton(
            heroTag: "chatbot",
            onPressed: () {
              Navigator.pushNamed(context, ChatbotPage.routeName);
            },
            backgroundColor: Theme.of(context).colorScheme.secondary,
            child: const Icon(Icons.smart_toy),
            tooltip: context.t('AI Assistant'),
          ),
          const SizedBox(width: 16),
          FloatingActionButton.extended(
            heroTag: "camera",
            onPressed: () {
              Navigator.pushNamed(context, CropCapturePage.routeName);
            },
            icon: const Icon(Icons.camera_alt),
            label: Text(context.t('Scan crop')),
          ),
        ],
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: const BottomAppBar(
        shape: CircularNotchedRectangle(),
        child: SizedBox(height: 48),
      ),
    );
  }
}

class _WeatherCard extends StatelessWidget {
  const _WeatherCard({required this.weather});

  final WeatherInfo weather;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: scheme.outline.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      weather.locationName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      weather.conditionText,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (weather.conditionIconUrl.isNotEmpty)
                    Image.network(
                      weather.conditionIconUrl,
                      width: 44,
                      height: 44,
                      errorBuilder: (context, error, stackTrace) {
                        return const SizedBox(
                          width: 44,
                          height: 44,
                          child: Icon(Icons.cloud),
                        );
                      },
                    ),
                  Text(
                    '${weather.tempC.toStringAsFixed(1)} C',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _InfoChip(
                label: context.t(
                  'Feels {value} C',
                  args: {'value': weather.feelsLikeC.toStringAsFixed(1)},
                ),
              ),
              _InfoChip(
                label: context.t(
                  'Humidity {value}%',
                  args: {'value': weather.humidity.toString()},
                ),
              ),
              _InfoChip(
                label: context.t(
                  'Wind {value} kph',
                  args: {'value': weather.windKph.toStringAsFixed(1)},
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _AnalyticsCard extends StatelessWidget {
  const _AnalyticsCard({required this.analytics});

  final Map<String, dynamic>? analytics;

  @override
  Widget build(BuildContext context) {
    if (analytics == null) {
      return Text(context.t('Analytics data unavailable.'));
    }

    final total = analytics?['total_diagnoses']?.toString() ?? '0';
    final severity =
        analytics?['severity_distribution'] as Map<String, dynamic>?;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              context.t('Total diagnoses'),
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 6),
            Text(total, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 12),
            if (severity != null)
              Wrap(
                spacing: 10,
                runSpacing: 8,
                children: [
                  _InfoChip(
                    label: '${context.t('Low')} ${severity['low'] ?? 0}',
                  ),
                  _InfoChip(
                    label: '${context.t('Medium')} ${severity['medium'] ?? 0}',
                  ),
                  _InfoChip(
                    label: '${context.t('High')} ${severity['high'] ?? 0}',
                  ),
                  _InfoChip(
                    label:
                        '${context.t('Healthy')} ${severity['healthy'] ?? 0}',
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({
    required this.item,
    required this.onOpen,
    required this.onDelete,
    this.onDownload,
    required this.actionsEnabled,
  });

  final Map<String, dynamic> item;
  final VoidCallback onOpen;
  final VoidCallback onDelete;
  final VoidCallback? onDownload;
  final bool actionsEnabled;

  @override
  Widget build(BuildContext context) {
    final cropType = item['crop_type']?.toString() ?? '';
    final diseaseName = item['disease_name']?.toString() ?? '';
    final severity = item['severity']?.toString() ?? 'unknown';
    final createdAt = item['created_at']?.toString() ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onOpen,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      diseaseName.isEmpty
                          ? context.t('Unknown disease')
                          : diseaseName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  _InfoChip(label: severity.toUpperCase()),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                context.t(
                  'Crop: {crop}',
                  args: {
                    'crop': cropType.isEmpty
                        ? context.t('Unknown crop')
                        : cropType,
                  },
                ),
              ),
              if (createdAt.isNotEmpty)
                Text(context.t('Date: {date}', args: {'date': createdAt})),
              const SizedBox(height: 12),
              Row(
                children: [
                  if (onDownload != null) ...[
                    OutlinedButton.icon(
                      onPressed: actionsEnabled ? onDownload : null,
                      icon: const Icon(Icons.download),
                      label: Text(context.t('Report')),
                    ),
                    const SizedBox(width: 12),
                  ],
                  TextButton.icon(
                    onPressed: actionsEnabled ? onDelete : null,
                    icon: const Icon(Icons.delete),
                    label: Text(context.t('Delete')),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 4),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Chip(
      label: Text(label),
      backgroundColor: scheme.primary.withOpacity(0.08),
      labelStyle: TextStyle(color: scheme.primary, fontWeight: FontWeight.w600),
      side: BorderSide(color: scheme.primary.withOpacity(0.4)),
    );
  }
}

class _NotificationsSheet extends StatelessWidget {
  const _NotificationsSheet({
    required this.accessToken,
    required this.notificationApi,
    required this.tokenStorage,
  });

  final String accessToken;
  final NotificationApi notificationApi;
  final TokenStorage tokenStorage;

  Future<List<Map<String, dynamic>>> _loadNotifications() async {
    // Mark all as read, but keep showing even if it fails.
    final profile = await tokenStorage.readUserProfile();
    final language = profile?['preferred_language']?.toString();
    try {
      await notificationApi.markAllRead(accessToken: accessToken);
    } catch (_) {
      // Keep showing notifications even if mark-all-read fails.
    }
    return notificationApi.getNotifications(
      accessToken: accessToken,
      language: language,
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        ),
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _loadNotifications(),
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const SizedBox(
                height: 220,
                child: Center(child: CircularProgressIndicator()),
              );
            }

            if (snapshot.hasError || !snapshot.hasData) {
              return SizedBox(
                height: 220,
                child: Center(
                  child: Text(context.t('Notifications unavailable.')),
                ),
              );
            }

            final notifications = snapshot.data!;
            if (notifications.isEmpty) {
              return SizedBox(
                height: 220,
                child: Center(child: Text(context.t('No notifications yet.'))),
              );
            }

            return SizedBox(
              height: MediaQuery.of(context).size.height * 0.65,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    context.t('Notifications'),
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: ListView.separated(
                      itemCount: notifications.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        final item = notifications[index];
                        return _NotificationTile(item: item);
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final title = item['title']?.toString() ?? 'Notification';
    final fallbackTitle = context.t('Notification');
    final message = item['message']?.toString() ?? '';
    final createdAt = _formatTimestamp(item['created_at']);
    final isRead = item['is_read'] == true;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    title.isEmpty ? fallbackTitle : title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                if (!isRead) _InfoChip(label: context.t('NEW')),
              ],
            ),
            if (message.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(message),
            ],
            if (createdAt.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(createdAt, style: Theme.of(context).textTheme.bodySmall),
            ],
          ],
        ),
      ),
    );
  }

  static String _formatTimestamp(dynamic value) {
    // Normalize server timestamps to local time.
    if (value == null) {
      return '';
    }

    final raw = value.toString();
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) {
      return raw;
    }

    final local = parsed.toLocal();
    final year = local.year.toString().padLeft(4, '0');
    final month = local.month.toString().padLeft(2, '0');
    final day = local.day.toString().padLeft(2, '0');
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    return '$year-$month-$day $hour:$minute';
  }
}
