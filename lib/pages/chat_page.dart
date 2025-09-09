import 'package:flutter/material.dart';
import '../models/chat_session.dart';
import '../models/message.dart';
import '../services/server_api.dart';
import '../services/server_config.dart';
import 'package:provider/provider.dart';
import 'dart:convert';

class ChatPage extends StatefulWidget {
  const ChatPage({Key? key}) : super(key: key);

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  late ChatSession session;
  late List<Message> messages;
  final TextEditingController _controller = TextEditingController();
  late ServerApi serverApi;
  final ScrollController _scrollController = ScrollController();

  // 예약 정보 상태 변수
  String? selectedRestaurantTitle;
  String? selectedRestaurantId;
  String? reservationDatetime;
  int? reservationPersons;
  String? reservationStatus;

  // 예약 정보 편집용 컨트롤러
  final TextEditingController _datetimeController = TextEditingController();
  int? _personsEdit;

  Color _getReservationCardColor(String? status) {
    switch (status) {
      case '확정':
        return Colors.green;
      case '전송':
        return Colors.orange;
      case '취소':
        return Colors.red;
      default:
        return Colors.yellow;
    }
  }

  /// 서버 응답 문자열을 Message 리스트로 파싱
  List<Message> _parseServerReply(String reply) {
    List<Message> serverMessages = [];
    try {
      final decoded = reply.trim();
      if (decoded.startsWith('[') && decoded.endsWith(']')) {
        final List<dynamic> list = List<dynamic>.from(jsonDecode(decoded));
        for (var item in list) {
          if (item is Map<String, dynamic> && item['type'] != null) {
            switch (item['type']) {
              case 'Restaurant Option':
                serverMessages.add(
                  RestaurantOptionMessage(
                    title: item['title'] ?? '',
                    id: item['id'] ?? '',
                  ),
                );
                break;
              case 'Reservation State':
                serverMessages.add(
                  ReservationStateMessage(
                    title: item['restaurant_title'] ?? item['title'] ?? '',
                    id: item['restaurant_id'] ?? item['id'] ?? '',
                    status: item['status'] ?? '',
                    datetime: item['datetime'] ?? '',
                    persons: item['persons'] ?? null,
                  ),
                );
                break;
              default:
                serverMessages.add(
                  ServerMessage(item['text']?.toString() ?? item.toString()),
                );
            }
          } else if (item is Map && item['text'] != null) {
            serverMessages.add(ServerMessage(item['text'].toString()));
          }
          // else는 무시 (문자열로 출력하지 않음)
        }
      } else if (decoded.startsWith('{') && decoded.endsWith('}')) {
        final Map<String, dynamic> obj = Map<String, dynamic>.from(
          jsonDecode(decoded),
        );
        if (obj['type'] == 'Restaurant Option') {
          serverMessages.add(
            RestaurantOptionMessage(
              title: obj['title'] ?? '',
              id: obj['id'] ?? '',
            ),
          );
        } else if (obj['type'] == 'Reservation State') {
          serverMessages.add(
            ReservationStateMessage(
              title: obj['restaurant_title'] ?? obj['title'] ?? '',
              id: obj['restaurant_id'] ?? obj['id'] ?? '',
              status: obj['status'] ?? '',
              datetime: obj['datetime'] ?? '',
              persons: obj['persons'] ?? null,
            ),
          );
        } else {
          serverMessages.add(ServerMessage(obj['text']?.toString() ?? decoded));
        }
      } else {
        serverMessages.add(ServerMessage(reply));
      }
    } catch (_) {
      serverMessages.add(ServerMessage(reply));
    }
    return serverMessages;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    session = ModalRoute.of(context)!.settings.arguments as ChatSession;
    messages = session.messages;
    final config = Provider.of<ServerConfig>(context);
    serverApi = ServerApi(config);
    // greetings 메시지 요청: 저장된 메시지가 없을 때만 요청
    if (messages.isEmpty) {
      Future.microtask(() async {
        try {
          final greet = await serverApi.greetings(session.id);
          final serverMessages = _parseServerReply(greet);
          setState(() {
            messages.addAll(serverMessages);
            _updateReservationInfo();
            // 세션 제목 업데이트: ReservationStateMessage가 있으면 변경
            final hasReservationMsg = serverMessages.any(
              (m) => m is ReservationStateMessage,
            );
            if (hasReservationMsg) {
              final lastReservationMsg =
                  serverMessages.lastWhere((m) => m is ReservationStateMessage)
                      as ReservationStateMessage;
              String title = lastReservationMsg.title;
              String status = lastReservationMsg.status;
              String? dt = lastReservationMsg.datetime;
              String formattedDt = '';
              if (dt != null && dt.isNotEmpty) {
                try {
                  final date = DateTime.parse(dt);
                  final hour = date.hour;
                  final minute = date.minute;
                  final ampm = hour < 12 ? '오전' : '오후';
                  final hour12 = hour % 12 == 0 ? 12 : hour % 12;
                  formattedDt =
                      '${date.year}년 ${date.month}월 ${date.day}일 $ampm $hour12시';
                  if (minute > 0) formattedDt += ' ${minute}분';
                } catch (_) {
                  formattedDt = '';
                }
              }
              session.title =
                  title +
                  (formattedDt.isNotEmpty ? ' - $formattedDt' : '') +
                  (status.isNotEmpty ? '($status)' : '');
            }
          });
          _scrollToBottom();
        } catch (e) {
          setState(() {
            messages.add(ServerMessage('서버 인사말 오류: $e'));
          });
          _scrollToBottom();
        }
      });
    }
  }

  void _updateReservationInfo() {
    bool foundReservation = false;
    for (final msg in messages.reversed) {
      if (msg is ReservationStateMessage) {
        reservationDatetime = msg.datetime;
        reservationPersons = msg.persons;
        reservationStatus = msg.status;
        selectedRestaurantTitle = msg.title;
        selectedRestaurantId = msg.id;
        foundReservation = true;
        break;
      }
    }
    if (!foundReservation) {
      selectedRestaurantTitle = null;
      selectedRestaurantId = null;
      reservationDatetime = null;
      reservationPersons = null;
      reservationStatus = null;
    }
  }

  void _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    setState(() {
      messages.add(UserMessage(text));
    });
    _scrollToBottom();
    _controller.clear();
    try {
      final reply = await serverApi.sendMessage(session.id, text);
      final serverMessages = _parseServerReply(reply);
      setState(() {
        messages.addAll(serverMessages);
        _updateReservationInfo();
        // 세션 제목 업데이트: ReservationStateMessage가 있으면 변경
        final hasReservationMsg = serverMessages.any(
          (m) => m is ReservationStateMessage,
        );
        if (hasReservationMsg) {
          final lastReservationMsg =
              serverMessages.lastWhere((m) => m is ReservationStateMessage)
                  as ReservationStateMessage;
          String title = lastReservationMsg.title;
          String status = lastReservationMsg.status;
          String? dt = lastReservationMsg.datetime;
          String formattedDt = '';
          if (dt != null && dt.isNotEmpty) {
            try {
              final date = DateTime.parse(dt);
              final hour = date.hour;
              final minute = date.minute;
              final ampm = hour < 12 ? '오전' : '오후';
              final hour12 = hour % 12 == 0 ? 12 : hour % 12;
              formattedDt =
                  '${date.year}년 ${date.month}월 ${date.day}일 $ampm $hour12시';
              if (minute > 0) formattedDt += ' ${minute}분';
            } catch (_) {
              formattedDt = '';
            }
          }
          session.title =
              title +
              (formattedDt.isNotEmpty ? ' - $formattedDt' : '') +
              (status.isNotEmpty ? '($status)' : '');
        }
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        messages.add(ServerMessage('서버 오류: $e'));
      });
      _scrollToBottom();
    }
  }

  // UserMessage를 바로 서버로 전송하는 함수
  void _sendMessageDirect(String text) async {
    if (text.isEmpty) return;
    setState(() {
      messages.add(UserMessage(text));
    });
    _scrollToBottom();
    try {
      final reply = await serverApi.sendMessage(session.id, text);
      final serverMessages = _parseServerReply(reply);
      setState(() {
        messages.addAll(serverMessages);
        _updateReservationInfo();
        // 세션 제목 업데이트: ReservationStateMessage가 있으면 변경
        final hasReservationMsg = serverMessages.any(
          (m) => m is ReservationStateMessage,
        );
        if (hasReservationMsg) {
          final lastReservationMsg =
              serverMessages.lastWhere((m) => m is ReservationStateMessage)
                  as ReservationStateMessage;
          String title = lastReservationMsg.title;
          String status = lastReservationMsg.status;
          String? dt = lastReservationMsg.datetime;
          String formattedDt = '';
          if (dt != null && dt.isNotEmpty) {
            try {
              final date = DateTime.parse(dt);
              final hour = date.hour;
              final minute = date.minute;
              final ampm = hour < 12 ? '오전' : '오후';
              final hour12 = hour % 12 == 0 ? 12 : hour % 12;
              formattedDt =
                  '${date.year}년 ${date.month}월 ${date.day}일 $ampm $hour12시';
              if (minute > 0) formattedDt += ' ${minute}분';
            } catch (_) {
              formattedDt = '';
            }
          }
          session.title =
              title +
              (formattedDt.isNotEmpty ? ' - $formattedDt' : '') +
              (status.isNotEmpty ? '($status)' : '');
        }
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        messages.add(ServerMessage('서버 오류: $e'));
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    _updateReservationInfo();
    if (reservationDatetime != null)
      _datetimeController.text = reservationDatetime!;
    if (reservationPersons != null) _personsEdit = reservationPersons;
    return Scaffold(
      appBar: AppBar(title: Text(session.title)),
      body: Column(
        children: [
          // 예약 정보 카드: 레스토랑이 선택된 경우 항상 표시
          if (selectedRestaurantTitle != null)
            Card(
              color: _getReservationCardColor(reservationStatus),
              margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '예약 레스토랑: $selectedRestaurantTitle',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Row(
                      children: [
                        const Text('예약 일시:', style: TextStyle(fontSize: 16)),
                        const SizedBox(width: 8),
                        SizedBox(
                          width: 200,
                          child: TextField(
                            controller: _datetimeController,
                            decoration: const InputDecoration(
                              hintText: 'YYYY-MM-DD HH:mm',
                            ),
                            onSubmitted: (value) {
                              if (value.isNotEmpty &&
                                  value != reservationDatetime) {
                                setState(() {
                                  reservationDatetime = value;
                                });
                                final msg =
                                    '${selectedRestaurantTitle} 예약 일시를 $value로 변경해 주세요';
                                _sendMessageDirect(msg);
                              }
                            },
                          ),
                        ),
                        // datetime이 없으면 아무것도 표시하지 않음
                        if (reservationDatetime == null ||
                            reservationDatetime == '')
                          const SizedBox.shrink(),
                        const SizedBox(width: 16),
                        const Text('인원수:', style: TextStyle(fontSize: 16)),
                        const SizedBox(width: 8),
                        DropdownButton<int>(
                          value: _personsEdit,
                          items: List.generate(10, (i) => i + 1)
                              .map(
                                (v) => DropdownMenuItem(
                                  value: v,
                                  child: Text('$v'),
                                ),
                              )
                              .toList(),
                          onChanged: (value) {
                            if (value != null && value != reservationPersons) {
                              setState(() {
                                reservationPersons = value;
                                _personsEdit = value;
                              });
                              final msg =
                                  '${selectedRestaurantTitle} 예약 인원을 $value명으로 변경해 주세요';
                              _sendMessageDirect(msg);
                            }
                          },
                        ),
                        // persons가 없으면 아무것도 표시하지 않음
                        if (reservationPersons == null) const SizedBox.shrink(),
                        const SizedBox(width: 16),
                        Text(
                          '상태: ${reservationStatus ?? '생성'}',
                          style: const TextStyle(fontSize: 16),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                final isUser = msg.sender == 'user';
                Widget messageWidget;
                if (msg is RestaurantOptionMessage) {
                  messageWidget = Card(
                    color: Colors.orange[50],
                    margin: const EdgeInsets.symmetric(
                      vertical: 4,
                      horizontal: 8,
                    ),
                    child: ListTile(
                      leading: Icon(Icons.restaurant, color: Colors.orange),
                      title: Text(
                        msg.title,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text('ID: ${msg.id}'),
                      trailing: ElevatedButton(
                        child: const Text('선택'),
                        onPressed: () {
                          final requestText = '${msg.title}으로 예약해 주세요';
                          _controller.text = requestText;
                          _sendMessage();
                        },
                      ),
                    ),
                  );
                } else if (msg is ReservationStateMessage) {
                  // 항상 카드 표시, 값이 없으면 빈 문자열
                  messageWidget = Card(
                    color: Colors.green[50],
                    margin: const EdgeInsets.symmetric(
                      vertical: 4,
                      horizontal: 8,
                    ),
                    child: ListTile(
                      leading: Icon(Icons.event, color: Colors.green),
                      title: Text(
                        '${msg.title} 예약',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      subtitle: Text(
                        '상태: ${msg.status}\n일시: ${msg.datetime ?? ''}\n인원: ${msg.persons?.toString() ?? ''}',
                      ),
                    ),
                  );
                } else {
                  messageWidget = Row(
                    mainAxisAlignment: isUser
                        ? MainAxisAlignment.end
                        : MainAxisAlignment.start,
                    children: [
                      if (!isUser)
                        Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: CircleAvatar(
                            child: Icon(Icons.smart_toy, color: Colors.white),
                            backgroundColor: Colors.blue,
                          ),
                        ),
                      Flexible(
                        child: Container(
                          margin: const EdgeInsets.symmetric(
                            vertical: 4,
                            horizontal: 8,
                          ),
                          padding: const EdgeInsets.symmetric(
                            vertical: 8,
                            horizontal: 12,
                          ),
                          decoration: BoxDecoration(
                            color: isUser
                                ? Colors.green[100]
                                : Colors.grey[200],
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Column(
                            crossAxisAlignment: isUser
                                ? CrossAxisAlignment.end
                                : CrossAxisAlignment.start,
                            children: [
                              Text(
                                msg.text,
                                style: const TextStyle(fontSize: 16),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${msg.timestamp.hour}:${msg.timestamp.minute.toString().padLeft(2, '0')}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      if (isUser)
                        Padding(
                          padding: const EdgeInsets.only(left: 8.0),
                          child: CircleAvatar(
                            child: Icon(Icons.person, color: Colors.white),
                            backgroundColor: Colors.green,
                          ),
                        ),
                    ],
                  );
                }
                return messageWidget;
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(hintText: '메시지 입력'),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
