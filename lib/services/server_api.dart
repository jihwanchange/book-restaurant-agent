import 'dart:convert';
import 'package:http/http.dart' as http;
import 'server_config.dart';

class ServerApi {
  final ServerConfig config;
  ServerApi(this.config);

  Future<String> createSession() async {
    final url = Uri.parse('${config.baseUrl}/session');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['session_id'] ?? '';
    } else {
      throw Exception('세션 생성 오류: ${response.statusCode}');
    }
  }

  Future<String> greetings(String sessionId) async {
    final url = Uri.parse('${config.baseUrl}/greetings');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'session_id': sessionId}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['text'] ?? '';
    } else {
      throw Exception('서버 오류: ${response.statusCode}');
    }
  }

  Future<String> sendMessage(String sessionId, String message) async {
    final url = Uri.parse('${config.baseUrl}/chat');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'session_id': sessionId, 'text': message}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['text'] ?? '';
    } else {
      throw Exception('서버 오류: ${response.statusCode}');
    }
  }
}
