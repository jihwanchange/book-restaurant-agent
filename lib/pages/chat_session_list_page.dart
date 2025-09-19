import 'package:flutter/material.dart';
import '../models/chat_session.dart';
import '../services/server_api.dart';
import '../services/server_config.dart';
import 'package:provider/provider.dart';

class ChatSessionListPage extends StatefulWidget {
  const ChatSessionListPage({super.key});

  @override
  State<ChatSessionListPage> createState() => _ChatSessionListPageState();
}

class _ChatSessionListPageState extends State<ChatSessionListPage> {
  List<ChatSession> sessions = [];

  Future<void> _createSession() async {
    final config = Provider.of<ServerConfig>(context, listen: false);
    final serverApi = ServerApi(config);
    String sessionId = '';
    try {
      sessionId = await serverApi.createSession();
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('세션 생성 실패: $e')));
      return;
    }
    final newSession = ChatSession(
      id: sessionId,
      title: '새로운 예약',
      createdAt: DateTime.now(),
    );
    setState(() {
      sessions.insert(0, newSession);
    });
    Future.microtask(
      () => Navigator.pushNamed(context, '/chat', arguments: newSession),
    );
  }

  void _deleteSession(String id) {
    setState(() {
      sessions.removeWhere((s) => s.id == id);
    });
  }

  void _openSession(ChatSession session) async {
    await Navigator.pushNamed(context, '/chat', arguments: session);
    setState(() {}); // 세션 제목 등 변경사항 반영
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('예약 대화 목록'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () async {
              final result = await Navigator.pushNamed(context, '/settings');
              // TODO: result로 서버 주소/포트 처리
            },
          ),
        ],
      ),
      body: ListView.builder(
        itemCount: sessions.length,
        itemBuilder: (context, index) {
          final session = sessions[index];
          return Dismissible(
            key: Key(session.id),
            direction: DismissDirection.endToStart,
            onDismissed: (_) => _deleteSession(session.id),
            background: Container(
              color: Colors.red,
              alignment: Alignment.centerRight,
              child: const Padding(
                padding: EdgeInsets.only(right: 16),
                child: Icon(Icons.delete, color: Colors.white),
              ),
            ),
            child: ListTile(
              title: Text(session.title),
              subtitle: Text(session.createdAt.toString()),
              onTap: () => _openSession(session),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createSession,
        child: const Icon(Icons.add),
      ),
    );
  }
}
