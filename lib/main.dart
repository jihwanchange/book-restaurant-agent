import 'package:flutter/material.dart';
import 'pages/chat_session_list_page.dart';
import 'pages/chat_page.dart';
import 'pages/settings_page.dart';
import 'package:provider/provider.dart';
import 'services/server_config.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<ServerConfig>(
      create: (_) => ServerConfig(),
      child: MaterialApp(
        title: 'LLM Chatbot',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
          useMaterial3: true,
        ),
        initialRoute: '/',
        routes: {
          '/': (context) => const ChatSessionListPage(),
          '/chat': (context) => const ChatPage(),
          '/settings': (context) => const SettingsPage(),
        },
      ),
    );
  }
}
