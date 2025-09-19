import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/server_config.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _portController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Provider에서 값 불러오기
    // context.read는 initState에서 사용 불가, didChangeDependencies에서 사용
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final config = Provider.of<ServerConfig>(context);
    _addressController.text = config.address;
    _portController.text = config.port.toString();
  }

  void _saveSettings() {
    final config = Provider.of<ServerConfig>(context, listen: false);
    config.update(
      address: _addressController.text,
      port: int.tryParse(_portController.text) ?? 5000,
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _addressController,
              decoration: const InputDecoration(labelText: '서버 주소'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _portController,
              decoration: const InputDecoration(labelText: '포트 번호'),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 32),
            ElevatedButton(onPressed: _saveSettings, child: const Text('저장')),
          ],
        ),
      ),
    );
  }
}
