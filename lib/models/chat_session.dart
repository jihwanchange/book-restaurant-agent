import 'message.dart';

class ChatSession {
  final String id;
  String title;
  final DateTime createdAt;
  final List<Message> messages;

  ChatSession({
    required this.id,
    required this.title,
    required this.createdAt,
    List<Message>? messages,
  }) : messages = messages ?? [];
}
