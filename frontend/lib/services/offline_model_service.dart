import 'dart:io';
import 'dart:math';

import 'package:flutter/services.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

/// On-device plant disease inference using TFLite.
///
/// Mirrors the backend's prediction logic including US13
/// confidence / entropy / margin uncertainty checks.
class OfflineModelService {
  OfflineModelService._();

  static final OfflineModelService instance = OfflineModelService._();

  Interpreter? _interpreter;
  List<String> _labels = [];
  bool _ready = false;

  bool get isReady => _ready;

  // Same thresholds as backend config
  static const double confidenceThreshold = 0.85;
  static const double entropyThreshold = 2.0;
  static const double marginThreshold = 0.10;
  static const int inputSize = 224;
  static const int _heatmapGridSize = 224;
  static const double _leafMaskThreshold = 0.16;
  static const double _overlayThreshold = 0.18;

  /// Copy an asset file to the app's local directory so TFLite can read it.
  Future<File> _copyAssetToLocal(String assetPath, String filename) async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File('${dir.path}/$filename');
    if (!await file.exists()) {
      final data = await rootBundle.load(assetPath);
      await file.writeAsBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
    }
    return file;
  }

  /// Load model and labels from assets. Safe to call multiple times.
  Future<void> init() async {
    if (_ready) return;

    // Copy model from Flutter assets to local filesystem, then load
    final modelFile = await _copyAssetToLocal(
      'assets/model/crop_disease_model.tflite',
      'crop_disease_model.tflite',
    );
    _interpreter = Interpreter.fromFile(modelFile);

    final raw = await rootBundle.loadString('assets/model/label_map.txt');
    _labels = [];
    for (final line in raw.split('\n')) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) continue;
      // Format: "0:Apple___Apple_scab"
      final colonIndex = trimmed.indexOf(':');
      if (colonIndex != -1) {
        _labels.add(trimmed.substring(colonIndex + 1));
      } else {
        _labels.add(trimmed);
      }
    }

    _ready = true;
  }

  /// Run prediction on a local image file.
  /// Returns a result map matching the shape of the online API response.
  Future<Map<String, dynamic>> predict(File imageFile, String cropType) async {
    if (!_ready || _interpreter == null) {
      await init();
    }

    // Read and preprocess image
    final bytes = await imageFile.readAsBytes();
    final decoded = img.decodeImage(bytes);
    if (decoded == null) {
      throw Exception('Failed to decode image.');
    }

    final resized = img.copyResize(
      decoded,
      width: inputSize,
      height: inputSize,
    );

    // Build input tensor [1, 224, 224, 3] normalized to [0, 1]
    final input = List.generate(
      1,
      (_) => List.generate(
        inputSize,
        (y) => List.generate(inputSize, (x) {
          final pixel = resized.getPixel(x, y);
          return [pixel.r / 255.0, pixel.g / 255.0, pixel.b / 255.0];
        }),
      ),
    );

    // Allocate output
    final output = List.generate(1, (_) => List.filled(_labels.length, 0.0));

    _interpreter!.run(input, output);

    final predictions = output[0];

    // Top prediction
    int topIdx = 0;
    double topConf = predictions[0];
    for (int i = 1; i < predictions.length; i++) {
      if (predictions[i] > topConf) {
        topConf = predictions[i];
        topIdx = i;
      }
    }

    final diseaseId = topIdx < _labels.length ? _labels[topIdx] : 'Unknown';

    // Entropy
    double entropy = 0.0;
    for (final p in predictions) {
      final clipped = p.clamp(1e-10, 1.0);
      entropy -= clipped * log(clipped);
    }

    // Margin (top1 - top2)
    final sorted = List<double>.from(predictions)
      ..sort((a, b) => b.compareTo(a));
    final margin = sorted.length > 1 ? sorted[0] - sorted[1] : 1.0;

    // Uncertainty decision (mirrors backend)
    final lowConfidence = topConf < confidenceThreshold;
    final highEntropy = entropy > entropyThreshold;
    final lowMargin = margin < marginThreshold;
    final isUncertain = lowConfidence || highEntropy || lowMargin;

    final isHealthy = diseaseId.toLowerCase().contains('healthy');

    String diseaseName;
    if (isUncertain) {
      diseaseName = 'Unknown/Unclear';
    } else {
      diseaseName = _formatDiseaseName(diseaseId);
    }

    // Determine severity from confidence (simple heuristic)
    String severity;
    if (isHealthy || isUncertain) {
      severity = 'unknown';
    } else if (topConf > 0.90) {
      severity = 'high';
    } else if (topConf > 0.70) {
      severity = 'medium';
    } else {
      severity = 'low';
    }

    String localHeatmapPath = '';
    if (!isHealthy) {
      localHeatmapPath = await _generateHeatmap(decoded);
    }

    return {
      'disease_id': diseaseId,
      'disease_name': diseaseName,
      'confidence': topConf,
      'severity': severity,
      'is_healthy': isHealthy,
      'is_uncertain': isUncertain,
      'is_offline': true,
      'crop_type': cropType,
      'local_image_path': imageFile.path,
      'local_heatmap_path': localHeatmapPath,
      'image_url': '',
      'heatmap_url': '',
      'bounding_boxes': <dynamic>[],
      'secondary_diagnoses': <dynamic>[],
      'created_at': DateTime.now().toIso8601String(),
    };
  }

  Future<String> _generateHeatmap(img.Image source) async {
    final analysis = img.copyResize(
      source,
      width: _heatmapGridSize,
      height: _heatmapGridSize,
    );

    const totalPixels = _heatmapGridSize * _heatmapGridSize;
    final leafMask = List<double>.filled(totalPixels, 0.0);
    final greenness = List<double>.filled(totalPixels, 0.0);
    final brightness = List<double>.filled(totalPixels, 0.0);
    final baseScores = List<double>.filled(totalPixels, 0.0);

    for (int y = 0; y < _heatmapGridSize; y++) {
      for (int x = 0; x < _heatmapGridSize; x++) {
        final p = analysis.getPixel(x, y);
        final idx = y * _heatmapGridSize + x;

        final rf = p.r / 255.0;
        final gf = p.g / 255.0;
        final bf = p.b / 255.0;
        final maxChannel = max(rf, max(gf, bf));
        final minChannel = min(rf, min(gf, bf));
        final saturation = maxChannel <= 1e-6
            ? 0.0
            : (maxChannel - minChannel) / maxChannel;
        final value = maxChannel;

        final greenAdvantage = gf - max(rf, bf);
        final yellowCue =
            max(0.0, min(rf, gf) - bf) *
            (1.0 - (gf - rf).abs()).clamp(0.0, 1.0);
        final brownCue =
            max(0.0, rf - gf * 0.7) * max(0.0, gf - bf * 0.6) * 1.4;
        final darkCue = (1.0 - value) * saturation;

        final leafLikelihood =
            (saturation * 0.85) +
            (max(0.0, gf - bf) * 0.75) +
            (max(0.0, rf - bf) * 0.25) +
            (max(0.0, greenAdvantage) * 0.9);

        final isLeafPixel = leafLikelihood > _leafMaskThreshold;
        leafMask[idx] = isLeafPixel ? 1.0 : 0.0;
        greenness[idx] = greenAdvantage;
        brightness[idx] = value;
        baseScores[idx] = isLeafPixel
            ? max(0.0, -greenAdvantage) * 0.65 +
                  yellowCue * 0.9 +
                  brownCue +
                  darkCue * 0.35
            : 0.0;
      }
    }

    final smoothedLeafMask = _blurGrid(leafMask, radius: 4);
    final localGreenness = _blurGrid(greenness, radius: 5);
    final localBrightness = _blurGrid(brightness, radius: 5);

    final scores = List<double>.filled(totalPixels, 0.0);
    for (int i = 0; i < totalPixels; i++) {
      if (smoothedLeafMask[i] < 0.18) {
        continue;
      }

      final contrastCue = max(0.0, localGreenness[i] - greenness[i]);
      final darkSpotCue = max(0.0, localBrightness[i] - brightness[i]);
      scores[i] =
          (baseScores[i] * 0.7 + contrastCue * 1.05 + darkSpotCue * 0.45) *
          smoothedLeafMask[i];
    }

    final smoothedScores = _blurGrid(scores, radius: 4);
    final normalizedScores = _normalizeHotspots(smoothedScores);

    final heatmap = img.Image.from(source);
    for (int y = 0; y < heatmap.height; y++) {
      final sy = ((y * _heatmapGridSize) / heatmap.height).floor().clamp(
        0,
        _heatmapGridSize - 1,
      );
      for (int x = 0; x < heatmap.width; x++) {
        final sx = ((x * _heatmapGridSize) / heatmap.width).floor().clamp(
          0,
          _heatmapGridSize - 1,
        );

        final idx = sy * _heatmapGridSize + sx;
        final score = normalizedScores[idx];
        final maskStrength = smoothedLeafMask[idx];
        if (maskStrength < 0.18 || score < _overlayThreshold) {
          continue;
        }

        final p = heatmap.getPixel(x, y);
        final overlay = _heatColor(score);
        final alpha =
            (pow(
                      ((score - _overlayThreshold) / (1 - _overlayThreshold))
                          .clamp(0.0, 1.0),
                      1.15,
                    ).toDouble() *
                    0.82 *
                    maskStrength)
                .clamp(0.0, 0.82);
        final nr = _blendChannel(p.r, overlay[0], alpha);
        final ng = _blendChannel(p.g, overlay[1], alpha);
        final nb = _blendChannel(p.b, overlay[2], alpha);
        heatmap.setPixelRgb(x, y, nr, ng, nb);
      }
    }

    final dir = await getTemporaryDirectory();
    final outFile = File(
      '${dir.path}/offline_heatmap_${DateTime.now().millisecondsSinceEpoch}.jpg',
    );
    await outFile.writeAsBytes(img.encodeJpg(heatmap, quality: 90));

    return outFile.path;
  }

  List<double> _blurGrid(List<double> values, {required int radius}) {
    final result = List<double>.filled(values.length, 0.0);
    const side = _heatmapGridSize;

    for (int y = 0; y < side; y++) {
      final startY = max(0, y - radius);
      final endY = min(side - 1, y + radius);
      for (int x = 0; x < side; x++) {
        final startX = max(0, x - radius);
        final endX = min(side - 1, x + radius);

        double total = 0.0;
        int count = 0;
        for (int ny = startY; ny <= endY; ny++) {
          for (int nx = startX; nx <= endX; nx++) {
            total += values[ny * side + nx];
            count++;
          }
        }
        result[y * side + x] = count == 0 ? 0.0 : total / count;
      }
    }

    return result;
  }

  List<double> _normalizeHotspots(List<double> values) {
    final active = values.where((value) => value > 0).toList()..sort();
    if (active.isEmpty) {
      return List<double>.filled(values.length, 0.0);
    }

    final lowerIndex = ((active.length - 1) * 0.60).floor();
    final upperIndex = ((active.length - 1) * 0.98).floor();
    final lower = active[lowerIndex];
    final upper = active[upperIndex] <= lower
        ? active.last
        : active[upperIndex];
    final scale = max(upper - lower, 1e-6);

    return values.map((value) {
      final normalized = ((value - lower) / scale).clamp(0.0, 1.0);
      return pow(normalized, 1.1).toDouble();
    }).toList();
  }

  int _blendChannel(num original, int overlay, double alpha) {
    return (original * (1.0 - alpha) + overlay * alpha).round().clamp(0, 255);
  }

  List<int> _heatColor(double score) {
    if (score < 0.33) {
      return _interpolateColor(
        const [0, 150, 255],
        const [50, 220, 180],
        score / 0.33,
      );
    }
    if (score < 0.66) {
      return _interpolateColor(
        const [50, 220, 180],
        const [255, 210, 0],
        (score - 0.33) / 0.33,
      );
    }
    return _interpolateColor(
      const [255, 210, 0],
      const [225, 20, 20],
      (score - 0.66) / 0.34,
    );
  }

  List<int> _interpolateColor(List<int> a, List<int> b, double t) {
    final clamped = t.clamp(0.0, 1.0);
    return [
      (a[0] + (b[0] - a[0]) * clamped).round(),
      (a[1] + (b[1] - a[1]) * clamped).round(),
      (a[2] + (b[2] - a[2]) * clamped).round(),
    ];
  }

  String _formatDiseaseName(String diseaseId) {
    // "Apple___Apple_scab" → "Apple Scab"
    final parts = diseaseId.split('___');
    final name = parts.length > 1 ? parts[1] : parts[0];
    return name
        .replaceAll('_', ' ')
        .split(' ')
        .where((w) => w.isNotEmpty)
        .map((w) => w[0].toUpperCase() + w.substring(1).toLowerCase())
        .join(' ');
  }
}
