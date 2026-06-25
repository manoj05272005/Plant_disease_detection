import 'dart:io';
import 'dart:typed_data';

import 'package:image/image.dart' as img;

class BlurDetector {
  const BlurDetector();

  Future<bool> isBlurry(File imageFile, {double threshold = 200.0}) async {
    final bytes = await imageFile.readAsBytes();
    return isBlurryBytes(bytes, threshold: threshold);
  }

  bool isBlurryBytes(Uint8List bytes, {double threshold = 200.0}) {
    // Variance of Laplacian; lower variance implies blur.
    final image = img.decodeImage(bytes);
    if (image == null) {
      throw Exception('Unable to decode image.');
    }

    final resized = _prepareImage(image);
    final width = resized.width;
    final height = resized.height;

    double sum = 0;
    double sumSq = 0;
    int count = 0;

    for (var y = 1; y < height - 1; y++) {
      for (var x = 1; x < width - 1; x++) {
        final center = _luma(resized.getPixel(x, y));
        final up = _luma(resized.getPixel(x, y - 1));
        final down = _luma(resized.getPixel(x, y + 1));
        final left = _luma(resized.getPixel(x - 1, y));
        final right = _luma(resized.getPixel(x + 1, y));

        final laplacian = -4 * center + up + down + left + right;
        sum += laplacian;
        sumSq += laplacian * laplacian;
        count++;
      }
    }

    if (count == 0) {
      return false;
    }

    final mean = sum / count;
    final variance = (sumSq / count) - (mean * mean);

    return variance < threshold;
  }

  img.Image _prepareImage(img.Image image) {
    final targetWidth = 256;
    final resized = image.width > targetWidth
        ? img.copyResize(image, width: targetWidth)
        : image;
    return img.grayscale(resized);
  }

  double _luma(img.Pixel pixel) {
    return (0.299 * pixel.r) + (0.587 * pixel.g) + (0.114 * pixel.b);
  }
}
