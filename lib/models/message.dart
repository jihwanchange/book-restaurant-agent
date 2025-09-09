class Message {
  final String sender;
  final String text;
  final DateTime timestamp;

  Message({required this.sender, required this.text, DateTime? timestamp})
    : timestamp = timestamp ?? DateTime.now();
}

class UserMessage extends Message {
  UserMessage(String text) : super(sender: 'user', text: text);
}

class ServerMessage extends Message {
  ServerMessage(String text) : super(sender: 'server', text: text);
}

class RestaurantOptionMessage extends Message {
  final String title;
  final String id;
  RestaurantOptionMessage({required this.title, required this.id})
    : super(sender: 'server', text: title);
}

class ReservationStateMessage extends Message {
  final String title;
  final String id;
  final String status;
  final String? datetime;
  final int? persons;
  ReservationStateMessage({
    required this.title,
    required this.id,
    required this.status,
    this.datetime,
    this.persons,
  }) : super(sender: 'server', text: title);
}
