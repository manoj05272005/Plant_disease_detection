import 'dart:io';
import 'dart:typed_data';

import 'package:image/image.dart' as img;

class ImageCompressionService {
  const ImageCompressionService();

  Future<File> compressFile(
    File imageFile, {
    int quality = 80,
    int? maxWidth,
    int? maxHeight,
    String? outputPath,
  }) async {
    final bytes = await imageFile.readAsBytes();
    final compressedBytes = compressBytes(
      bytes,
      quality: quality,
      maxWidth: maxWidth,
      maxHeight: maxHeight,
    );

    final targetPath = outputPath ?? _buildOutputPath(imageFile.path);
    final outputFile = File(targetPath);
    await outputFile.writeAsBytes(compressedBytes, flush: true);
    return outputFile;
  }

  Uint8List compressBytes(
    Uint8List bytes, {
    int quality = 80,
    int? maxWidth,
    int? maxHeight,
  }) {
    final image = img.decodeImage(bytes);
    if (image == null) {
      throw Exception('Unable to decode image for compression.');
    }

    final safeQuality = quality.clamp(1, 100);
    final resized = _resizeIfNeeded(
      image,
      maxWidth: maxWidth,
      maxHeight: maxHeight,
    );

    final encoded = img.encodeJpg(resized, quality: safeQuality);
    return Uint8List.fromList(encoded);
  }

  img.Image _resizeIfNeeded(img.Image image, {int? maxWidth, int? maxHeight}) {
    final hasWidthLimit = maxWidth != null && maxWidth > 0;
    final hasHeightLimit = maxHeight != null && maxHeight > 0;
    if (!hasWidthLimit && !hasHeightLimit) {
      return image;
    }

    final widthLimit = hasWidthLimit ? maxWidth : image.width;
    final heightLimit = hasHeightLimit ? maxHeight : image.height;

    final widthScale = widthLimit / image.width;
    final heightScale = heightLimit / image.height;
    final scale = widthScale < heightScale ? widthScale : heightScale;

    if (scale >= 1) {
      return image;
    }

    final targetWidth = (image.width * scale).round().clamp(1, image.width);
    final targetHeight = (image.height * scale).round().clamp(1, image.height);

    return img.copyResize(
      image,
      width: targetWidth,
      height: targetHeight,
      interpolation: img.Interpolation.linear,
    );
  }

  String _buildOutputPath(String inputPath) {
    final lastSlashIndex = inputPath.lastIndexOf('/');
    if (lastSlashIndex == -1) {
      return '${inputPath}_compressed.jpg';
    }

    final directory = inputPath.substring(0, lastSlashIndex);
    final fileName = inputPath.substring(lastSlashIndex + 1);
    final dotIndex = fileName.lastIndexOf('.');
    final baseName = dotIndex > 0 ? fileName.substring(0, dotIndex) : fileName;

    return '$directory/${baseName}_compressed.jpg';
  }
}
