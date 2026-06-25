import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/token_storage.dart';
import '../services/app_localizations.dart';
import '../services/tts_service.dart';

// Screen for remediation guidance per diagnosis.
class RemediationPage extends StatefulWidget {
  const RemediationPage({
    super.key,
    required this.diseaseId,
    required this.diseaseName,
    required this.severity,
    required this.isHealthy,
  });

  final String diseaseId;
  final String diseaseName;
  final String severity;
  final bool isHealthy;

  @override
  State<RemediationPage> createState() => _RemediationPageState();
}

class _RemediationPageState extends State<RemediationPage> {
  late final TtsService _ttsService;
  bool _ttsLanguageFallback = false;

  @override
  void initState() {
    super.initState();
    _ttsService = TtsService();
    _initializeTts();
  }

  Future<void> _initializeTts() async {
    final success = await _ttsService.initialize();
    if (success && _ttsService.fellBackToEnglish) {
      setState(() {
        _ttsLanguageFallback = true;
      });
      // Show fallback message after a short delay
      Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted && _ttsLanguageFallback) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                context.t(
                  'TTS not available in your language on this device. Reading in English.',
                ),
              ),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 5),
            ),
          );
          setState(() {
            _ttsLanguageFallback = false;
          });
        }
      });
    }
  }

  @override
  void dispose() {
    _ttsService.stop();
    _ttsService.dispose();
    super.dispose();
  }

  /// Helper method to wrap content with tap-to-speak functionality
  Widget _speakOnTap({required Widget child, required String? textToSpeak}) {
    // If text is null or empty, return child unwrapped
    if (textToSpeak == null || textToSpeak.trim().isEmpty) {
      return child;
    }

    return GestureDetector(
      onTap: () => _ttsService.speak(textToSpeak),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(child: child),
          const SizedBox(width: 6),
          const Icon(Icons.volume_up, size: 16, color: Colors.green),
        ],
      ),
    );
  }

  Future<_RemediationData> _loadData() async {
    // Load remediation JSON and apply preferred language.
    final raw = await rootBundle.loadString(
      'assets/remediation/remediation.json',
    );
    final decoded = jsonDecode(raw);

    String language = 'en';
    final profile = await const TokenStorage().readUserProfile();
    final preferred = profile?['preferred_language']?.toString();
    if (preferred != null && preferred.isNotEmpty) {
      language = preferred;
    }

    return _RemediationData(decoded, language);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text(context.t('Remediation guide')),
        actions: [
          IconButton(
            icon: const Icon(Icons.stop_circle_outlined),
            onPressed: () => _ttsService.stop(),
            tooltip: context.t('Stop reading'),
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
          child: FutureBuilder<_RemediationData>(
            future: _loadData(),
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }

              if (snapshot.hasError || !snapshot.hasData) {
                return Center(
                  child: Text(context.t('Remediation data unavailable.')),
                );
              }

              final data = snapshot.data!;
              final disease =
                  data.findDisease(widget.diseaseId) ??
                  (widget.isHealthy ? data.findHealthyFallback() : null);

              if (disease == null) {
                return Center(
                  child: Text(
                    context.t(
                      'No remediation found for {name}.',
                      args: {'name': widget.diseaseName},
                    ),
                    textAlign: TextAlign.center,
                  ),
                );
              }

              final localizedName =
                  data.localize(disease['name']) ?? widget.diseaseName;
              final description = data.localize(disease['description']) ?? '';
              final prevention = data.localizeList(disease['prevention_steps']);
              final severityGuidance = data.localizeSeverity(
                disease['severity_guidance'],
                widget.severity,
              );
              final treatments = data.resolveTreatments(disease);
              final noTreatmentNeeded =
                  disease['no_treatment_needed'] == true ||
                  (treatments == null && widget.isHealthy);
              final riskFactors = data.localizeList(
                disease['environmental_risk_factors'],
              );
              final affectedParts =
                  data.localize(disease['affected_parts']) ?? '';
              final communityTips = data.localizeList(
                disease['community_tips'],
              );
              final whenToSeekExpert =
                  data.localize(disease['when_to_seek_expert']) ?? '';
              final companionPlants = data.localizeList(
                disease['companion_plants'],
              );

              return ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _speakOnTap(
                            child: Text(
                              localizedName,
                              style: Theme.of(context).textTheme.headlineSmall,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            textToSpeak: 'Disease detected: $localizedName',
                          ),
                          if (description.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text(description),
                          ],
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 10,
                            runSpacing: 8,
                            children: [
                              _speakOnTap(
                                child: _InfoChip(
                                  label: widget.severity.toUpperCase(),
                                ),
                                textToSpeak:
                                    'Severity level: ${widget.severity}',
                              ),
                              if (noTreatmentNeeded)
                                _InfoChip(
                                  label: context.t('No treatment needed'),
                                ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (severityGuidance.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    _speakOnTap(
                      child: _SectionHeader(
                        title: context.t('Severity guidance'),
                        subtitle: severityGuidance,
                      ),
                      textToSpeak: 'Severity guidance: $severityGuidance',
                    ),
                  ],
                  if (affectedParts.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.local_hospital,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    context.t('Affected parts'),
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            _speakOnTap(
                              child: Text(affectedParts),
                              textToSpeak: 'Affected parts: $affectedParts',
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (riskFactors.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.warning_amber, color: Colors.orange),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    context.t('Environmental risk factors'),
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            ...riskFactors.map(
                              (factor) => _speakOnTap(
                                child: _BulletRow(text: factor),
                                textToSpeak: 'Risk factor: $factor',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (!noTreatmentNeeded && treatments != null) ...[
                    const SizedBox(height: 20),
                    _TreatmentSection(
                      title: context.t('Organic treatment'),
                      treatment: treatments['organic'] as Map<String, dynamic>?,
                      language: data.language,
                      ttsService: _ttsService,
                    ),
                    const SizedBox(height: 16),
                    _TreatmentSection(
                      title: context.t('Chemical treatment'),
                      treatment:
                          treatments['chemical'] as Map<String, dynamic>?,
                      language: data.language,
                      ttsService: _ttsService,
                    ),
                  ],
                  if (prevention.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    _SectionHeader(
                      title: context.t('Prevention tips'),
                      subtitle: context.t(
                        'Keep plants resilient with these steps.',
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...prevention.map(
                      (tip) => _speakOnTap(
                        child: _BulletRow(text: tip),
                        textToSpeak: 'Prevention tip: $tip',
                      ),
                    ),
                  ],
                  if (communityTips.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    Card(
                      color: Colors.green.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.people,
                                  color: Colors.green.shade700,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    context.t('Community tips'),
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Flexible(
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: Colors.green.shade700,
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        const Icon(
                                          Icons.verified,
                                          color: Colors.white,
                                          size: 16,
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          context.t('Verified'),
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 12,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              context.t('Tips from experienced farmers'),
                              style: Theme.of(context).textTheme.bodySmall,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 12),
                            ...communityTips.map(
                              (tip) => _speakOnTap(
                                child: _BulletRow(text: tip),
                                textToSpeak: 'Community tip: $tip',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (companionPlants.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.eco, color: Colors.green.shade600),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    context.t('Companion plants'),
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              context.t(
                                'Plant these nearby for natural protection',
                              ),
                              style: Theme.of(context).textTheme.bodySmall,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: companionPlants
                                  .map((plant) => _PlantChip(label: plant))
                                  .toList(),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (whenToSeekExpert.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Card(
                      color: Colors.orange.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  Icons.support_agent,
                                  color: Colors.orange.shade700,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    context.t('When to seek expert'),
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            _speakOnTap(
                              child: Text(whenToSeekExpert),
                              textToSpeak:
                                  'When to seek expert: $whenToSeekExpert',
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _RemediationData {
  _RemediationData(this.raw, this.language);

  final dynamic raw;
  final String language;

  Map<String, dynamic>? findDisease(String id) {
    if (raw is Map<String, dynamic>) {
      final map = raw as Map<String, dynamic>;
      if (map.containsKey('diseases')) {
        final diseases = map['diseases'] as List<dynamic>?;
        if (diseases != null) {
          for (final item in diseases) {
            if (item is Map<String, dynamic> && item['disease_id'] == id) {
              return item;
            }
          }
        }
      } else if (map[id] is Map<String, dynamic>) {
        return map[id] as Map<String, dynamic>;
      }
    }
    return null;
  }

  Map<String, dynamic>? findHealthyFallback() {
    return findDisease('Tomato___healthy') ?? findDisease('tomato_healthy');
  }

  Map<String, dynamic>? resolveTreatments(Map<String, dynamic> disease) {
    final treatments = disease['treatments'];
    if (treatments is Map<String, dynamic>) {
      return treatments;
    }
    final organic = disease['organic_treatment'] as Map<String, dynamic>?;
    final chemical = disease['chemical_treatment'] as Map<String, dynamic>?;
    if (organic == null && chemical == null) {
      return null;
    }
    return {'organic': organic, 'chemical': chemical};
  }

  String? localize(dynamic value) {
    // Fall back to English when the language entry is missing.
    if (value is Map<String, dynamic>) {
      final localized = value[language] ?? value['en'];
      return localized?.toString();
    }
    return value?.toString();
  }

  List<String> localizeList(dynamic value) {
    if (value is Map<String, dynamic>) {
      final localized = value[language] ?? value['en'];
      if (localized is List) {
        return localized.map((item) => item.toString()).toList();
      }
    }
    if (value is List) {
      return value.map((item) => item.toString()).toList();
    }
    return [];
  }

  String localizeSeverity(dynamic value, String severity) {
    if (value is Map<String, dynamic>) {
      final entry = value[severity];
      return localize(entry) ?? '';
    }
    return '';
  }
}

class _TreatmentSection extends StatelessWidget {
  const _TreatmentSection({
    required this.title,
    required this.treatment,
    required this.language,
    required this.ttsService,
  });

  final String title;
  final Map<String, dynamic>? treatment;
  final String language;
  final TtsService ttsService;

  String _localize(dynamic value) {
    if (value is Map<String, dynamic>) {
      final localized = value[language] ?? value['en'];
      return localized?.toString() ?? '';
    }
    return value?.toString() ?? '';
  }

  /// Helper method to wrap content with tap-to-speak functionality
  Widget _speakOnTap({required Widget child, required String? textToSpeak}) {
    // If text is null or empty, return child unwrapped
    if (textToSpeak == null || textToSpeak.trim().isEmpty) {
      return child;
    }

    return GestureDetector(
      onTap: () => ttsService.speak(textToSpeak),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(child: child),
          const SizedBox(width: 6),
          const Icon(Icons.volume_up, size: 16, color: Colors.green),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (treatment == null || treatment!.isEmpty) {
      return const SizedBox.shrink();
    }

    final steps = treatment!['steps'] as List<dynamic>? ?? [];
    final dosage = _localize(treatment!['dosage']);
    final frequency = _localize(treatment!['frequency']);
    final cost = treatment!['cost_estimate']?.toString() ?? '';
    final expectedResults = _localize(treatment!['expected_results']);

    final safetyWarnings = <String>[];
    for (final step in steps) {
      if (step is Map<String, dynamic>) {
        final warning = _localize(step['safety_warning']);
        if (warning.isNotEmpty) {
          safetyWarnings.add(warning);
        }
      }
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _speakOnTap(
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              textToSpeak: title,
            ),
            const SizedBox(height: 12),
            ...steps.map(
              (step) => _StepRow(
                step: step as Map<String, dynamic>,
                language: language,
                ttsService: ttsService,
              ),
            ),
            if (dosage.isNotEmpty ||
                frequency.isNotEmpty ||
                cost.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 10,
                runSpacing: 8,
                children: [
                  if (dosage.isNotEmpty)
                    _speakOnTap(
                      child: _InfoChip(
                        label: context.t(
                          'Dosage {value}',
                          args: {'value': dosage},
                        ),
                      ),
                      textToSpeak: 'Dosage: $dosage',
                    ),
                  if (frequency.isNotEmpty)
                    _InfoChip(
                      label: context.t(
                        'Frequency {value}',
                        args: {'value': frequency},
                      ),
                    ),
                  if (cost.isNotEmpty)
                    _speakOnTap(
                      child: _InfoChip(
                        label: context.t('Cost {value}', args: {'value': cost}),
                      ),
                      textToSpeak: 'Estimated cost: $cost',
                    ),
                ],
              ),
            ],
            if (expectedResults.isNotEmpty) ...[
              const SizedBox(height: 12),
              _speakOnTap(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.trending_up,
                        color: Colors.blue.shade700,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.t('Expected results'),
                              style: TextStyle(
                                fontWeight: FontWeight.w600,
                                color: Colors.blue.shade900,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              expectedResults,
                              style: TextStyle(color: Colors.blue.shade900),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                textToSpeak: 'Expected results: $expectedResults',
              ),
            ],
            if (safetyWarnings.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                context.t('Safety warnings'),
                style: Theme.of(context).textTheme.titleSmall,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 6),
              ...safetyWarnings.map(
                (warning) => _speakOnTap(
                  child: _BulletRow(text: warning),
                  textToSpeak: 'Safety warning: $warning',
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({
    required this.step,
    required this.language,
    required this.ttsService,
  });

  final Map<String, dynamic> step;
  final String language;
  final TtsService ttsService;

  String _localize(dynamic value) {
    if (value is Map<String, dynamic>) {
      final localized = value[language] ?? value['en'];
      return localized?.toString() ?? '';
    }
    return value?.toString() ?? '';
  }

  /// Helper method to wrap content with tap-to-speak functionality
  Widget _speakOnTap({required Widget child, required String? textToSpeak}) {
    // If text is null or empty, return child unwrapped
    if (textToSpeak == null || textToSpeak.trim().isEmpty) {
      return child;
    }

    return GestureDetector(
      onTap: () => ttsService.speak(textToSpeak),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(child: child),
          const SizedBox(width: 6),
          const Icon(Icons.volume_up, size: 16, color: Colors.green),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final stepNumber = step['step_number']?.toString() ?? '';
    final description = _localize(step['description']);
    final duration = _localize(step['duration']);

    return _speakOnTap(
      textToSpeak: 'Step $stepNumber: $description',
      child: Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child: Text(
                stepNumber,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(description),
                  if (duration.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        duration,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                ],
              ),
            ),
          ],
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
        Text(
          title,
          style: Theme.of(context).textTheme.titleLarge,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
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

class _BulletRow extends StatelessWidget {
  const _BulletRow({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 6),
            child: Icon(Icons.circle, size: 6),
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _PlantChip extends StatelessWidget {
  const _PlantChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: const Icon(Icons.local_florist, size: 16),
      label: Text(label),
      backgroundColor: Colors.green.shade100,
      labelStyle: TextStyle(
        color: Colors.green.shade800,
        fontWeight: FontWeight.w500,
      ),
    );
  }
}
