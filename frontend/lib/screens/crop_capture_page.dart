import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:video_player/video_player.dart';
import 'package:video_thumbnail/video_thumbnail.dart';

import '../services/blur_detector.dart';
import '../services/diagnosis_api.dart';
import '../services/diagnosis_cache.dart';
import '../services/offline_model_service.dart';
import '../services/token_storage.dart';
import '../services/app_localizations.dart';
import 'diagnosis_result_page.dart';

// Screen for selecting crop and capturing media for diagnosis.
class CropCapturePage extends StatefulWidget {
  const CropCapturePage({super.key});

  static const String routeName = '/capture';

  @override
  State<CropCapturePage> createState() => _CropCapturePageState();
}

class _CropCapturePageState extends State<CropCapturePage> {
  final _picker = ImagePicker();
  final _diagnosisApi = DiagnosisApi();
  final _diagnosisCache = DiagnosisCacheService();
  final _tokenStorage = const TokenStorage();
  final _blurDetector = const BlurDetector();

  bool _isSubmitting = false;

  final List<_CropItem> _crops = const [
    _CropItem(code: 'apple', label: 'Apple'),
    _CropItem(code: 'corn', label: 'Corn'),
    _CropItem(code: 'pepper', label: 'Pepper'),
    _CropItem(code: 'potato', label: 'Potato'),
    _CropItem(code: 'strawberry', label: 'Strawberry'),
    _CropItem(code: 'tomato', label: 'Tomato'),
  ];

  // Prompt for media source and handle image/video selection.
  Future<void> _onCropSelected(_CropItem crop) async {
    final option = await showModalBottomSheet<_MediaOption>(
      context: context,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: Text(context.t('Gallery image')),
                onTap: () => Navigator.pop(
                  context,
                  const _MediaOption(
                    source: ImageSource.gallery,
                    isVideo: false,
                  ),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.video_library),
                title: Text(context.t('Gallery video')),
                onTap: () => Navigator.pop(
                  context,
                  const _MediaOption(
                    source: ImageSource.gallery,
                    isVideo: true,
                  ),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.photo_camera),
                title: Text(context.t('Camera image')),
                onTap: () => Navigator.pop(
                  context,
                  const _MediaOption(
                    source: ImageSource.camera,
                    isVideo: false,
                  ),
                ),
              ),
              ListTile(
                leading: const Icon(Icons.videocam),
                title: Text(context.t('Camera video')),
                onTap: () => Navigator.pop(
                  context,
                  const _MediaOption(source: ImageSource.camera, isVideo: true),
                ),
              ),
            ],
          ),
        );
      },
    );

    if (option == null) {
      return;
    }

    if (option.isVideo) {
      final video = await _picker.pickVideo(source: option.source);
      if (video == null) {
        return;
      }

      final frameFile = await _extractFrame(File(video.path));
      if (frameFile == null) {
        _showError(context.tRead('Unable to extract a frame from video.'));
        return;
      }

      await _processImage(crop, frameFile);
      return;
    }

    final image = await _picker.pickImage(source: option.source);
    if (image == null) {
      return;
    }
    final cropped = await _cropImage(File(image.path));
    if (cropped == null) {
      return;
    }

    await _processImage(crop, cropped);
  }

  Future<File?> _cropImage(File imageFile) async {
    final cropped = await ImageCropper().cropImage(
      sourcePath: imageFile.path,
      compressQuality: 95,
      uiSettings: [
        AndroidUiSettings(
          toolbarTitle: context.tRead('Crop image'),
          toolbarColor: const Color(0xFF1B5E20),
          toolbarWidgetColor: Colors.white,
          activeControlsWidgetColor: const Color(0xFF1B5E20),
          lockAspectRatio: false,
        ),
        IOSUiSettings(title: context.tRead('Crop image')),
      ],
    );

    if (cropped == null) {
      return null;
    }

    return File(cropped.path);
  }

  Future<File?> _extractFrame(File videoFile) async {
    // Pull a mid-frame thumbnail from a video capture.
    try {
      final controller = VideoPlayerController.file(videoFile);
      await controller.initialize();
      final duration = controller.value.duration;
      await controller.dispose();

      final timeMs = duration.inMilliseconds ~/ 2;
      final bytes = await VideoThumbnail.thumbnailData(
        video: videoFile.path,
        imageFormat: ImageFormat.PNG,
        timeMs: timeMs,
        quality: 90,
      );

      if (bytes == null) {
        return null;
      }

      final tempDir = await getTemporaryDirectory();
      final file = File(
        '${tempDir.path}/frame_${DateTime.now().millisecondsSinceEpoch}.png',
      );
      await file.writeAsBytes(bytes, flush: true);
      return file;
    } catch (_) {
      return null;
    }
  }

  Future<void> _processImage(_CropItem crop, File imageFile) async {
    // Run blur check, then submit and cache the diagnosis.
    try {
      final isBlurry = await _blurDetector.isBlurry(
        imageFile,
        threshold: 200.0,
      );
      if (isBlurry) {
        await showDialog<void>(
          context: context,
          builder: (context) {
            return AlertDialog(
              title: Text(context.t('Image is blurry')),
              content: Text(
                context.t('Please retake the image for a clearer result.'),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text(context.t('OK')),
                ),
              ],
            );
          },
        );
        return;
      }

      setState(() {
        _isSubmitting = true;
      });

      // Check network connectivity
      final connectivity = await Connectivity().checkConnectivity();
      final isOffline = connectivity.contains(ConnectivityResult.none);

      Map<String, dynamic> displayResult;

      if (isOffline) {
        // --- Offline: run on-device TFLite model ---
        final offlineService = OfflineModelService.instance;
        displayResult = await offlineService.predict(imageFile, crop.code);

        // Persist offline predictions separately so they appear in home history.
        final localDiagnosisId =
            'offline_${DateTime.now().millisecondsSinceEpoch}';
        displayResult = {
          ...displayResult,
          '_id': localDiagnosisId,
          'diagnosis_id': localDiagnosisId,
          'crop_type': crop.code,
          'created_at': DateTime.now().toIso8601String(),
          'is_offline': true,
        };

        await _tokenStorage.saveDiagnosisResult(
          diagnosisId: localDiagnosisId,
          result: displayResult,
        );

        final existingOfflineHistory =
            await _tokenStorage.readOfflineHistory() ??
            <Map<String, dynamic>>[];
        final offlineHistoryItem = {
          '_id': localDiagnosisId,
          'diagnosis_id': localDiagnosisId,
          'crop_type': crop.code,
          'disease_name':
              displayResult['disease_name']?.toString() ?? 'Unknown disease',
          'severity': displayResult['severity']?.toString() ?? 'unknown',
          'created_at':
              displayResult['created_at']?.toString() ??
              DateTime.now().toIso8601String(),
          'is_offline': true,
        };
        await _tokenStorage.saveOfflineHistory([
          offlineHistoryItem,
          ...existingOfflineHistory,
        ]);
      } else {
        // --- Online: use backend API ---
        final accessToken = await _tokenStorage.readAccessToken();
        if (accessToken == null || accessToken.isEmpty) {
          _showError(
            context.tRead('Missing access token. Please log in again.'),
          );
          return;
        }

        final profile = await _tokenStorage.readUserProfile();
        final language = profile?['preferred_language']?.toString();

        final result = await _diagnosisApi.createDiagnosis(
          accessToken: accessToken,
          cropType: crop.code,
          imageFile: imageFile,
          language: language,
        );
        displayResult = result;
        final diagnosisId = _extractDiagnosisId(result);
        if (diagnosisId != null && diagnosisId.isNotEmpty) {
          displayResult = await _diagnosisCache.cacheDiagnosisImages(
            diagnosisId: diagnosisId,
            result: result,
          );
          await _tokenStorage.saveDiagnosisResult(
            diagnosisId: diagnosisId,
            result: displayResult,
          );
        }
      }

      if (!mounted) {
        return;
      }

      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) =>
              DiagnosisResultPage(cropLabel: crop.label, result: displayResult),
        ),
      );
    } catch (error) {
      _showError(error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  void _showError(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  String? _extractDiagnosisId(Map<String, dynamic> result) {
    // Accept id from multiple response keys.
    final id = result['_id']?.toString();
    if (id != null && id.isNotEmpty) {
      return id;
    }
    final alt = result['id']?.toString();
    if (alt != null && alt.isNotEmpty) {
      return alt;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: Text(context.t('Choose crop'))),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFF5F1EA), Color(0xFFE7F0E8)],
          ),
        ),
        child: Stack(
          children: [
            SafeArea(
              child: GridView.builder(
                padding: const EdgeInsets.all(20),
                itemCount: _crops.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 0.9,
                ),
                itemBuilder: (context, index) {
                  final crop = _crops[index];
                  return InkWell(
                    onTap: () => _onCropSelected(crop),
                    borderRadius: BorderRadius.circular(18),
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Theme.of(
                              context,
                            ).colorScheme.surface.withOpacity(0.9),
                            Theme.of(context)
                                .colorScheme
                                .surfaceContainerHighest
                                .withOpacity(0.95),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Theme.of(
                            context,
                          ).colorScheme.outline.withOpacity(0.2),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.06),
                            blurRadius: 14,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Expanded(
                            child: Image.asset(
                              crop.assetPath,
                              fit: BoxFit.contain,
                              errorBuilder: (context, error, stackTrace) {
                                return const Icon(Icons.eco, size: 48);
                              },
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            crop.label,
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            if (_isSubmitting)
              Container(
                color: Colors.black54,
                child: const Center(child: CircularProgressIndicator()),
              ),
          ],
        ),
      ),
    );
  }
}

class _CropItem {
  const _CropItem({required this.code, required this.label});

  final String code;
  final String label;

  String get assetPath => 'assets/images/crops/$code.png';
}

class _MediaOption {
  const _MediaOption({required this.source, required this.isVideo});

  final ImageSource source;
  final bool isVideo;
}
