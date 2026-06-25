import 'package:geolocator/geolocator.dart';

class LocationData {
  final double latitude;
  final double longitude;

  const LocationData({required this.latitude, required this.longitude});
}

class LocationService {
  const LocationService();

  Future<LocationData> getCurrentLocation() async {
    // Ensure service + permissions before fetching GPS.
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Location services are disabled.');
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.denied) {
      throw Exception('Location permissions are denied.');
    }

    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permissions are permanently denied.');
    }

    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
      timeLimit: const Duration(seconds: 10),
    );

    return LocationData(
      latitude: position.latitude,
      longitude: position.longitude,
    );
  }
}
