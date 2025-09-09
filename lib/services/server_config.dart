import 'package:flutter/foundation.dart';

class ServerConfig extends ChangeNotifier {
  String address;
  int port;

  ServerConfig({this.address = '127.0.0.1', this.port = 5000});

  String get baseUrl => 'http://$address:$port';

  void update({String? address, int? port}) {
    if (address != null) this.address = address;
    if (port != null) this.port = port;
    notifyListeners();
  }
}
